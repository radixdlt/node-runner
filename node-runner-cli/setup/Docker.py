import getpass
import os
import sys

import requests
from setup.Base import Base
from utils.utils import run_shell_command, Helpers
import yaml


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
        return nginx_password

    @staticmethod
    def run_docker_compose_up(keystore_password, composefile, trustednode):
        run_shell_command(['docker-compose', '-f', composefile, 'up', '-d'],
                          env={
                              "RADIXDLT_NETWORK_NODE": trustednode,
                              "RADIXDLT_NODE_KEY_PASSWORD": keystore_password
                          })

    @staticmethod
    def fetchComposeFile(composefileurl):
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

        #TODO AutoApprove
        prompt_external_db = input("Do you want to configure data directory for the ledger [Y/n]?:")
        if Helpers.check_Yes(prompt_external_db):
            composefile_yaml = Docker.merge_external_db_config(composefile_yaml)

        def represent_none(self, _):
            return self.represent_scalar('tag:yaml.org,2002:null', '')

        yaml.add_representer(type(None), represent_none)

        with open(compose_file_name, 'w') as f:
            yaml.dump(composefile_yaml, f, default_flow_style=False, explicit_start=True, allow_unicode=True)

    @staticmethod
    def merge_external_db_config(composefile_yaml):
        data_dir_path = Base.get_data_dir()

        #TODO fix the issue where volumes array gets merged correctly
        external_data_yaml = yaml.safe_load(f"""
        services:
          core:
            volumes:
              - "core_ledger:/home/radixdlt/RADIXDB"
              - "./universe.json:/home/radixdlt/universe.json"
              - "./validator.ks:/home/radixdlt/validator.ks"
        volumes:
          core_ledger:
            driver: local
            driver_opts:
              o: bind
              type: none
              device: {data_dir_path}
        """)
        final_conf = Helpers.merge(external_data_yaml, composefile_yaml)
        return final_conf

    @staticmethod
    def run_docker_compose_down(composefile, removevolumes=False):
        Helpers.docker_compose_down(composefile, removevolumes)
