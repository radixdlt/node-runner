import getpass
import os
import sys
from pathlib import Path

import requests

from setup.AnsibleRunner import AnsibleRunner
from utils.PromptFeeder import QuestionKeys
from utils.Prompts import Prompts
from utils.utils import run_shell_command, Helpers, bcolors


class Base:
    @staticmethod
    def dependencies():
        run_shell_command('sudo apt update', shell=True)
        run_shell_command('sudo apt install -y  docker.io wget unzip docker-compose rng-tools', shell=True)
        run_shell_command('sudo rngd -r /dev/random', shell=True)

    @staticmethod
    def add_user_docker_group():

        run_shell_command('sudo groupadd docker', shell=True, fail_on_error=False)
        is_in_docker_group = run_shell_command('groups | grep docker', shell=True, fail_on_error=False)
        if is_in_docker_group.returncode != 0:
            run_shell_command(f"sudo usermod -aG docker  {os.environ.get('USER')}", shell=True)
            print('Exit ssh login and relogin back for user addition to group "docker" to take effect')

    @staticmethod
    def fetch_universe_json(trustenode, extraction_path="."):
        run_shell_command(
            f'sudo wget --no-check-certificate -O {extraction_path}/universe.json https://{trustenode}/universe.json',
            shell=True)

    @staticmethod
    def generatekey(keyfile_path, keyfile_name, keygen_tag, ks_password=None, new=False):
        if os.path.isfile(f'{keyfile_path}/{keyfile_name}'):
            print(f"Node Keystore file already exist at location {keyfile_path}")
            keystore_password = ks_password if ks_password else getpass.getpass(
                f"Enter the password of the existing keystore file '{keyfile_name}':")
        else:
            if not new:
                ask_keystore_exists = input \
                    (f"Do you have keystore file named '{keyfile_name}' already from previous node Y/n?:")
                if Helpers.check_Yes(ask_keystore_exists):
                    print(
                        f"\nCopy the keystore file '{keyfile_name}' to the location {keyfile_path} and then rerun the command")
                    sys.exit()

            print(f"""
            \nGenerating new keystore file. Don't forget to backup the key from location {keyfile_path}/{keyfile_name}
            """)
            keystore_password = ks_password if ks_password else getpass.getpass(
                f"Enter the password of the new file '{keyfile_name}':")
            run_shell_command(['docker', 'run', '--rm', '-v', keyfile_path + ':/keygen/key',
                               f'radixdlt/keygen:{keygen_tag}',
                               f'--keystore=/keygen/key/{keyfile_name}',
                               '--password=' + keystore_password], quite=True
                              )
            run_shell_command(['sudo', 'chmod', '644', f'{keyfile_path}/{keyfile_name}'])

        return keystore_password, f'{keyfile_path}/{keyfile_name}'

    @staticmethod
    def setup_node_optimisation_config(version):
        ansibleRunner = AnsibleRunner(
            f'https://raw.githubusercontent.com/radixdlt/node-runner/{version}/node-runner-cli')
        file = 'ansible/project/provision.yml'
        ansibleRunner.check_install_ansible()
        ansibleRunner.download_ansible_file(file)
        setup_limits = Prompts.ask_ansible_setup_limits()
        if setup_limits:
            ansibleRunner.run_setup_limits(setup_limits)

        setup_swap, ask_swap_size = Prompts.ask_ansible_swap_setup()
        if setup_swap:
            ansibleRunner.run_swap_size(setup_swap, ask_swap_size)

    @staticmethod
    def get_data_dir(create_dir=True):
        Helpers.section_headline("LEDGER LOCATION")
        data_dir_path = Helpers.input_guestion(
            f"\nRadix node stores all the ledger data on a folder. "
            f"Mounting this location as a docker volume, "
            f"will allow to restart the node without a need to download ledger"
            f"\n{bcolors.WARNING}Press Enter to store ledger on \"{Helpers.get_home_dir()}/data\" directory OR "
            f"Type the absolute path of existing ledger data folder:{bcolors.ENDC}", QuestionKeys.input_ledger_path)
        if data_dir_path == "":
            data_dir_path = f"{Helpers.get_home_dir()}/data"
        if create_dir:
            run_shell_command(f'sudo mkdir -p {data_dir_path}', shell=True)
        return data_dir_path

    @staticmethod
    def get_network_id():
        # Network id
        network_prompt = Helpers.input_guestion(
            "Select the network you want to connect [S]Stokenet or [M]Mainnet or network_id:",
            QuestionKeys.select_network)
        if network_prompt.lower() in ["s", "stokenet"]:
            network_id = 2
        elif network_prompt.lower() in ["m", "mainnet"]:
            network_id = 1
        elif network_prompt in ["1", "2", "3", "4", "5", "6", "7", "8"]:
            network_id = network_prompt
        else:
            print("Input for network id is wrong. Exiting command")
            sys.exit()
        return network_id

    @staticmethod
    def path_to_genesis_json(network_id):
        if network_id not in [1, 2]:
            genesis_json_location = input("Enter absolute path to genesis json:")
        else:
            genesis_json_location = None

        return genesis_json_location
