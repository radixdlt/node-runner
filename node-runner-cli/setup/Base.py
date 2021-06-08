import getpass
import os
import sys
from pathlib import Path

import requests

from utils.utils import run_shell_command, Helpers


class Base:
    @staticmethod
    def install_dependecies():
        run_shell_command(['sudo', 'apt', 'update'])
        run_shell_command(['sudo', 'apt', 'install', 'docker.io'])
        run_shell_command(['sudo', 'apt', 'install', 'wget', 'unzip'])
        run_shell_command(['sudo', 'apt', 'install', 'docker-compose'])
        run_shell_command(['sudo', 'apt', 'install', 'rng-tools'])
        run_shell_command(['sudo', 'rngd', '-r', '/dev/random'])
        run_shell_command('sudo apt install python3-pip', shell=True)
        run_shell_command('pip install ansible==2.10.0', shell=True)

    @staticmethod
    def add_user_docker_group():

        run_shell_command(['sudo', 'groupadd', 'docker'], fail_on_error=False)
        is_in_docker_group = run_shell_command('groups | grep docker', shell=True, fail_on_error=False)
        if is_in_docker_group.returncode != 0:
            run_shell_command(['sudo', 'usermod', '-aG', 'docker', os.environ.get('USER')])
            print('Exit ssh login and relogin back for user addition to group "docker" to take effect')

    @staticmethod
    def fetch_universe_json(trustenode, extraction_path="."):
        run_shell_command(
            ['sudo', 'wget', '--no-check-certificate', '-O', f'{extraction_path}/universe.json',
             'https://' + trustenode + '/universe.json'])

    @staticmethod
    def generatekey(keyfile_path, keyfile_name="validator.ks"):
        print('-----------------------------')
        if os.path.isfile(f'{keyfile_path}/validator.ks'):
            print(f"Node key file already exist at location {keyfile_path}")
            keystore_password = getpass.getpass("Enter the password of the existing keystore file 'validator.ks':")
        else:
            ask_keystore_exists = input \
                ("Do you have keystore file named 'validator.ks' already from previous node Y/n?:")
            if ask_keystore_exists == "Y":
                print(
                    f"Copy the keystore file 'validator.ks' to the location {keyfile_path} and then rerun the command")
                sys.exit()
            else:
                print(f"""
                Generating new keystore file. Don't forget to backup the key from location {keyfile_path}/validator.ks
                """)
                keystore_password = getpass.getpass("Enter the password of the new file 'validator.ks':")
                # TODO keygen image needs to be updated
                run_shell_command(['docker', 'run', '--rm', '-v', keyfile_path + ':/keygen/key',
                                   'radixdlt/keygen:1.0-beta.31',
                                   '--keystore=/keygen/key/validator.ks',
                                   '--password=' + keystore_password], quite=True
                                  )
                run_shell_command(['sudo', 'chmod', '644', f'{keyfile_path}/validator.ks'])

        return keystore_password

    @staticmethod
    def download_ansible_file(ansible_dir,file):
        req = requests.Request('GET', f'{ansible_dir}/{file}')
        prepared = req.prepare()

        resp = Helpers.send_request(prepared, print_response=False)
        directory = file.rsplit('/', 1)[0]
        print(f'directory {directory}')
        Path(directory).mkdir(parents=True, exist_ok=True)
        with open(file, 'wb') as f:
            f.write(resp.content)

    @staticmethod
    def setup_node_optimisation_config(version,setup_swap,setup_limits):
        ansible_dir = f'https://raw.githubusercontent.com/radixdlt/node-runner/{version}/node-runner-cli'

        print(f"Downloading artifacts from {ansible_dir}\n")
        Base.download_ansible_file(ansible_dir, 'ansible/project/provision.yml')
        run_shell_command(f"ansible-playbook ansible/project/provision.yml -e setup_limits={setup_limits} -e setup_swap={setup_swap}", shell=True)
