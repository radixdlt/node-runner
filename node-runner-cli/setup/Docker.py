import getpass
import os
import sys

import requests

from env_vars import IMAGE_OVERRIDE
from setup.Base import Base
from utils.utils import run_shell_command, Helpers
import yaml
from deepmerge import always_merger


class Docker(Base):

    @staticmethod
    def setup_nginx_Password(usertype, username):
        print('-----------------------------')
        print(f'Setting up nginx user of type {usertype} with username {username}')
        nginx_password = getpass.getpass(f"Enter your nginx the password: ")
        run_shell_command(['docker', 'run', '--rm', '-v',
                           os.getcwd().rsplit('/', 1)[-1] + '_nginx_secrets:/secrets',
                           'radixdlt/htpasswd:v1.0.0',
                           'htpasswd', '-bc', f'/secrets/htpasswd.{usertype}', username, nginx_password])

        print(
            f"""
            Setup NGINX_{usertype.upper()}_PASSWORD environment variable using below command . Replace the string 'nginx_password_of_your_choice' with your password

            echo 'export NGINX_{usertype.upper()}_PASSWORD="nginx_password_of_your_choice"' >> ~/.bashrc
            """)
        if username not in ["admin", "metrics", "superadmin"]:
            print(
                f"""
            echo 'export NGINX_{usertype.upper()}_USERNAME="{username}"' >> ~/.bashrc
            """
            )
        return nginx_password

    @staticmethod
    def run_docker_compose_up(keystore_password, composefile, trustednode):
        run_shell_command(['docker-compose', '-f', composefile, 'up', '-d'],
                          env={
                              "RADIXDLT_NETWORK_NODE": trustednode,
                              "RADIXDLT_NODE_KEY_PASSWORD": keystore_password
                          })

    @staticmethod
    def setup_compose_file(composefileurl, file_location):
        compose_file_name = composefileurl.rsplit('/', 1)[-1]
        if os.path.isfile(compose_file_name):
            backup_file_name = f"{Helpers.get_current_date_time()}_{compose_file_name}"
            print(f"Docker compose file {compose_file_name} exists. Backing it up as {backup_file_name}")
            run_shell_command(f"cp {compose_file_name} {backup_file_name}", shell=True)
        print(f"Downloading new compose file from {composefileurl}")

        req = requests.Request('GET', f'{composefileurl}')
        prepared = req.prepare()
        resp = Helpers.send_request(prepared, print_response=False)

        if not resp.ok:
            print(f" Errored downloading file {composefileurl}. Exitting ... ")
            sys.exit()

        composefile_yaml = yaml.safe_load(resp.content)

        # TODO AutoApprove
        prompt_external_db = input("Do you want to configure data directory for the ledger [Y/n]?:")
        if Helpers.check_Yes(prompt_external_db):
            composefile_yaml = Docker.merge_external_db_config(composefile_yaml)
        prompt_enable_transactions = input(
            " Transactions API that can be used stream transactions can be created and exposed by changing api.transactions.enable settings"
            "Do you want to enable it [true/false]?:")
        if Helpers.check_Yes(prompt_enable_transactions):
            composefile_yaml = Docker.merge_transactions_env_var(composefile_yaml, "true")

        def represent_none(self, _):
            return self.represent_scalar('tag:yaml.org,2002:null', '')

        yaml.add_representer(type(None), represent_none)

        network_id = Base.get_network_id()
        genesis_json_location = Base.path_to_genesis_json(network_id)

        composefile_yaml = Docker.merge_network_info(composefile_yaml, network_id, genesis_json_location)
        composefile_yaml = Docker.merge_keyfile_path(composefile_yaml, file_location)
        composefile_yaml = Docker.merge_transactions_env_var(composefile_yaml, prompt_enable_transactions)

        if os.getenv(IMAGE_OVERRIDE, "False") in ("true", "yes"):
            composefile_yaml = Docker.merge_image_overrides(composefile_yaml)

        with open(compose_file_name, 'w') as f:
            yaml.dump(composefile_yaml, f, default_flow_style=False, explicit_start=True, allow_unicode=True)

    @staticmethod
    def merge_external_db_config(composefile_yaml, keyfile_name="node-keystore.ks"):
        data_dir_path = Base.get_data_dir()

        # TODO fix the issue where volumes array gets merged correctly
        external_data_yaml = yaml.safe_load(f"""
        services:
          core:
            volumes:
              - "core_ledger:/home/radixdlt/RADIXDB"
        volumes:
          core_ledger:
            driver: local
            driver_opts:
              o: bind
              type: none
              device: {data_dir_path}
        """)
        final_conf = always_merger.merge(composefile_yaml, external_data_yaml)
        return final_conf

    @staticmethod
    def run_docker_compose_down(composefile, removevolumes=False):
        Helpers.docker_compose_down(composefile, removevolumes)

    @staticmethod
    def merge_keyfile_path(composefile_yaml, keyfile_location):
        key_yaml = yaml.safe_load(f"""
        services:
          core:
            volumes:
             - "{keyfile_location}:/home/radixdlt/node-keystore.ks"
        """)
        final_conf = always_merger.merge(composefile_yaml, key_yaml)
        return final_conf

    @staticmethod
    def merge_transactions_env_var(composefile_yaml, transactions_enable="false"):
        transactions_enable_yml = yaml.safe_load(f"""
                services:
                  core:
                    environment:
                      RADIXDLT_TRANSACTIONS_API_ENABLE: {transactions_enable}
                """)
        return always_merger.merge(transactions_enable_yml, composefile_yaml)

    @staticmethod
    def merge_network_info(composefile_yaml, network_id, genesis_json=None):

        network_info_yml = yaml.safe_load(f"""
        services:
          core:
            environment:
              RADIXDLT_NETWORK_ID: {network_id}
        """)
        if genesis_json:
            genesis_info_yml = yaml.safe_load(f"""
            services:
              core:
                environment:
                  RADIXDLT_GENESIS_FILE: "/home/radixdlt/genesis.json"
                volumes:
                - "{genesis_json}:/home/radixdlt/genesis.json"
            """)
            # network_info_yml = Helpers.merge(genesis_info_yml, network_info_yml)
            network_info_yml = always_merger.merge(network_info_yml, genesis_info_yml)
        volumes = composefile_yaml["services"]["core"]["volumes"]
        harcoded_key_volume = "./node-keystore.ks:/home/radixdlt/node-keystore.ks"
        if "./node-keystore.ks:/home/radixdlt/node-keystore.ks" in volumes: volumes.remove(harcoded_key_volume)

        composefile_yaml["services"]["core"]["environment"].pop("RADIXDLT_NETWORK_ID")
        yml_to_return = always_merger.merge(network_info_yml, composefile_yaml)
        return yml_to_return

    @staticmethod
    def merge_image_overrides(composefile_yaml):
        prompt_core_image = input("Enter the core image along with repo:")
        prompt_nginx_image = input("Enter the nginx image along with repo:")
        images_yml = yaml.safe_load(f"""
                    services:
                      core:
                       image: {prompt_core_image}
                      nginx:
                       image: {prompt_nginx_image}
                    """)

        final_conf = always_merger.merge(composefile_yaml, images_yml)
        return final_conf
