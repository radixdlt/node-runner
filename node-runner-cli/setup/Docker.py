import getpass
import os
import sys

import yaml

from config.BaseConfig import SetupMode
from config.GatewayDockerConfig import PostGresSettings
from env_vars import DOCKER_COMPOSE_FOLDER_PREFIX, COMPOSE_HTTP_TIMEOUT, RADIXDLT_NODE_KEY_PASSWORD, POSTGRES_PASSWORD
from github import github
from setup.AnsibleRunner import AnsibleRunner
from setup.Base import Base
from utils.Prompts import Prompts
from utils.utils import run_shell_command, Helpers


class Docker(Base):

    @staticmethod
    def setup_nginx_Password(usertype, username, password=None):
        print('-----------------------------')
        print(f'Setting up nginx user of type {usertype} with username {username}')
        if not password:
            nginx_password = getpass.getpass(f"Enter your nginx the password: ")
        else:
            nginx_password = password
        docker_compose_folder_prefix = os.getenv(DOCKER_COMPOSE_FOLDER_PREFIX, os.getcwd().rsplit('/', 1)[-1])
        run_shell_command(['docker', 'run', '--rm', '-v',
                           docker_compose_folder_prefix + '_nginx_secrets:/secrets',
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
    def run_docker_compose_up(composefile):
        docker_compose_binary = os.getenv("DOCKER_COMPOSE_LOCATION", 'docker-compose')
        result = run_shell_command([docker_compose_binary, '-f', composefile, 'up', '-d'],
                                   env={
                                       COMPOSE_HTTP_TIMEOUT: os.getenv(COMPOSE_HTTP_TIMEOUT, "200")
                                   }, fail_on_error=False)
        if result.returncode != 0:
            run_shell_command([docker_compose_binary, '-f', composefile, 'up', '-d'],
                              env={
                                  COMPOSE_HTTP_TIMEOUT: os.getenv(COMPOSE_HTTP_TIMEOUT, "200")
                              }, fail_on_error=True)

    @staticmethod
    def save_compose_file(existing_docker_compose: str, composefile_yaml: dict):
        with open(existing_docker_compose, 'w') as f:
            yaml.dump(composefile_yaml, f, default_flow_style=False, explicit_start=True, allow_unicode=True)

    @staticmethod
    def run_docker_compose_down(composefile, removevolumes=False):
        Helpers.docker_compose_down(composefile, removevolumes)

    @staticmethod
    def check_set_passwords(all_config):
        keystore_password = all_config.get('core_node', {}).get('keydetails', {}).get("keystore_password")
        if all_config.get('core_node') and not keystore_password:
            keystore_password_from_env = os.getenv(RADIXDLT_NODE_KEY_PASSWORD, None)
            if not keystore_password_from_env:
                print(
                    "Cannot find Keystore password either in config "
                    "or as environment variable RADIXDLT_NODE_KEY_PASSWORD")
                sys.exit(1)
            else:
                all_config['core_node']["keydetails"]["keystore_password"] = keystore_password_from_env

        postgres_password = all_config.get('gateway', {}).get('postgres_db', {}).get("password")
        if all_config.get('gateway') and not postgres_password:
            postgres_password_from_env = os.getenv(POSTGRES_PASSWORD, None)

            if not postgres_password_from_env:
                print(
                    "Cannot find POSTGRES_PASSWORD either in config"
                    "or as environment variable POSTGRES_PASSWORD")
                sys.exit(1)
            else:
                all_config['gateway']["postgres_db"]["password"] = postgres_password_from_env
        return all_config

    @staticmethod
    def check_run_local_postgreSQL(all_config):
        postgres_db = all_config.get('gateway', {}).get('postgres_db')
        if Docker.check_post_db_local(all_config):
            ansible_dir = f'https://raw.githubusercontent.com/radixdlt/node-runner/{Helpers.cli_version()}/node-runner-cli'
            AnsibleRunner(ansible_dir).run_setup_postgress(
                postgres_db.get("password"),
                postgres_db.get("user"),
                postgres_db.get("dbname"),
                'ansible/project/provision.yml')

    @staticmethod
    def check_post_db_local(all_config):
        postgres_db = all_config.get('gateway', {}).get('postgres_db')
        if postgres_db and postgres_db.get("setup", None) == "local":
            return True
        return False

    @staticmethod
    def load_all_config(configfile):
        yaml.add_representer(type(None), Helpers.represent_none)

        if os.path.exists(configfile):
            with open(configfile, 'r') as file:
                all_config = yaml.safe_load(file)
                return all_config
        else:
            print(f"Config file '{configfile}' doesn't exist");
            return {}

    @staticmethod
    def get_existing_compose_file(all_config):
        compose_file = all_config['common_config']['docker_compose']
        if os.path.exists(compose_file):
            return compose_file, Helpers.yaml_as_dict(compose_file)
        else:
            return compose_file, {}

    @staticmethod
    def exit_on_missing_trustednode():
        print("-t or --trustednode parameter is mandatory")
        sys.exit(1)

    @staticmethod
    def update_versions(all_config, autoapprove):
        updated_config = dict(all_config)

        if all_config.get('core_node'):
            current_core_release = all_config['core_node']["core_release"]
            latest_core_release = github.latest_release("radixdlt/radixdlt")
            updated_config['core_node']["core_release"] = Prompts.confirm_version_updates(current_core_release,
                                                                                          latest_core_release, 'CORE',
                                                                                          autoapprove)
        if all_config.get("gateway"):
            latest_gateway_release = github.latest_release("radixdlt/radixdlt-network-gateway")
            current_gateway_release = all_config['gateway']["data_aggregator"]["release"]

            if all_config.get('gateway', {}).get('data_aggregator'):
                updated_config['gateway']["data_aggregator"]["release"] = Prompts.confirm_version_updates(
                    current_gateway_release,
                    latest_gateway_release, 'AGGREGATOR', autoapprove)

            if all_config.get('gateway', {}).get('gateway_api'):
                updated_config['gateway']["gateway_api"]["release"] = Prompts.confirm_version_updates(
                    current_gateway_release,
                    latest_gateway_release, 'GATEWAY', autoapprove)

        if all_config.get("common_config").get("nginx_settings"):
            latest_nginx_release = github.latest_release("radixdlt/radixdlt-nginx")
            current_nginx_release = all_config['common_config']["nginx_settings"]["release"]
            updated_config['common_config']["nginx_settings"]["release"] = Prompts.confirm_version_updates(
                current_nginx_release, latest_nginx_release, "RADIXDLT NGINX", autoapprove
            )

        return updated_config

    @staticmethod
    def backup_save_config(config_file, new_config, autoapprove, backup_time):
        to_update = ""
        if autoapprove:
            print("In Auto mode - Updating the file as suggested in above changes")
        else:
            to_update = input("\nOkay to update the config file [Y/n]?:")
        if Helpers.check_Yes(to_update) or autoapprove:
            if os.path.exists(config_file):
                Helpers.backup_file(config_file, f"{config_file}_{backup_time}")
            print(f"\n\n Saving to file {config_file} ")
            with open(config_file, 'w') as f:
                yaml.dump(new_config, f, default_flow_style=False, explicit_start=True, allow_unicode=True)
