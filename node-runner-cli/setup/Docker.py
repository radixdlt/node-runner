import getpass
import os

import yaml

from env_vars import DOCKER_COMPOSE_FOLDER_PREFIX, COMPOSE_HTTP_TIMEOUT
from setup.Base import Base
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
    def run_docker_compose_up(keystore_password, composefile, trustednode):
        docker_compose_binary = os.getenv("DOCKER_COMPOSE_LOCATION", 'docker-compose')
        run_shell_command([docker_compose_binary, '-f', composefile, 'up', '-d'],
                          env={
                              "RADIXDLT_NETWORK_NODE": trustednode,
                              "RADIXDLT_NODE_KEY_PASSWORD": keystore_password,
                              COMPOSE_HTTP_TIMEOUT: os.getenv(COMPOSE_HTTP_TIMEOUT, 200)
                          })

    @staticmethod
    def save_compose_file(existing_docker_compose, composefile_yaml):
        with open(existing_docker_compose, 'w') as f:
            yaml.dump(composefile_yaml, f, default_flow_style=False, explicit_start=True, allow_unicode=True)

    @staticmethod
    def run_docker_compose_down(composefile, removevolumes=False):
        Helpers.docker_compose_down(composefile, removevolumes)
