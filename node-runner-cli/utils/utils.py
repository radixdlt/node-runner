import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import requests
import yaml
from system_client import ApiException

from env_vars import PRINT_REQUEST
from version import __version__


def printCommand(cmd):
    print('-----------------------------')
    if type(cmd) is list:
        print('Running command :' + ' '.join(cmd))
        print('-----------------------------')
    else:
        print('Running command ' + cmd)
        print('-----------------------------')


def run_shell_command(cmd, env=None, shell=False, fail_on_error=True, quite=False):
    if not quite:
        printCommand(cmd)
    if env:
        result = subprocess.run(cmd, env=env, shell=shell)
    else:
        result = subprocess.run(cmd, shell=shell)
    if fail_on_error and result.returncode != 0:
        print("""
            Command failed. Exiting...
        """)
        sys.exit()
    return result


def print_vote_and_fork_info(health, engine_configuration):
    newest_fork = engine_configuration['forks'][-1]
    newest_fork_name = newest_fork['name']
    is_candidate = newest_fork['is_candidate']

    if health['current_fork_name'] == newest_fork_name:
        print(
            f"The node is currently running fork {Bcolors.BOLD}{health['current_fork_name']}{Bcolors.ENDC}, which is the newest fork in its configuration")
        print(f"{Bcolors.WARNING}No action is needed{Bcolors.ENDC}")
        return

    if not is_candidate:
        print(
            f"The node is currently running fork {Bcolors.BOLD}{health['current_fork_name']}{Bcolors.ENDC}. The node is aware of a newer fixed epoch fork ({newest_fork_name})")
        print(f"{Bcolors.WARNING}This newer fork is not a candidate fork, so no action is needed{Bcolors.ENDC}")
        return

    node_says_vote_required = health['fork_vote_status'] == 'VOTE_REQUIRED'
    if not node_says_vote_required:
        print(
            f"The node is currently running fork {Bcolors.BOLD}{health['current_fork_name']}{Bcolors.ENDC}. The node is aware of a newer candidate fork ({newest_fork_name})")
        print(
            f"{Bcolors.WARNING}The node has already signalled the readiness for this candidate fork, so no action is needed{Bcolors.ENDC}")
        return

    print(
        f"The node is currently running fork {Bcolors.BOLD}{health['current_fork_name']}{Bcolors.ENDC}. The node is aware of a newer candidate fork ({newest_fork_name})")
    print(f"{Bcolors.WARNING}The node has not yet signalled the readiness for this fork{Bcolors.ENDC}")


class Helpers:
    @staticmethod
    def is_json(myjson):
        try:
            json_object = json.loads(myjson)
        except ValueError as e:
            return False
        return True

    @staticmethod
    def pretty_print_request(req):
        print('{}\n{}\r\n{}\r\n\r\n{}\n{}'.format(
            '-----------Request-----------',
            req.method + ' ' + req.url,
            '\r\n'.join('{}: {}'.format(k, v) for k, v in req.headers.items()),
            req.body,
            '-------------------------------'
        ))

    @staticmethod
    def send_request(prepared, print_request=False, print_response=True):
        if print_request or os.getenv(PRINT_REQUEST) is not None:
            Helpers.pretty_print_request(prepared)
        s = requests.Session()
        resp = s.send(prepared, verify=False)
        if Helpers.is_json(resp.content):
            response_content = json.dumps(resp.json())
        else:
            response_content = resp.content

        if print_response:
            print(response_content)
        return resp

    @staticmethod
    def get_nginx_user(usertype, default_username):
        nginx_password = f'NGINX_{usertype.upper()}_PASSWORD'
        nginx_username = f'NGINX_{default_username.upper()}_USERNAME'
        if os.environ.get('%s' % nginx_password) is None:
            print(f"""
            ------
            NGINX_{usertype.upper()}_PASSWORD is missing !
            Setup NGINX_{usertype.upper()}_PASSWORD environment variable using below command . Replace the string 'nginx_password_of_your_choice' with your password

            echo 'export NGINX_{usertype.upper()}_PASSWORD="nginx_password_of_your_choice"' >> ~/.bashrc
            """)
            sys.exit()
        else:
            # if os.getenv(nginx_username) is None:
            #     print (f"Using default name of usertype {usertype} as {default_username}")
            return dict({
                "name": os.getenv(nginx_username, default_username),
                "password": os.environ.get("%s" % nginx_password)
            })

    @staticmethod
    def docker_compose_down(composefile, remove_volumes):
        command = ['docker-compose', '-f', composefile, 'down']
        if remove_volumes:
            command.append('-v')
        run_shell_command(command)

    @staticmethod
    def get_public_ip():
        return requests.get('https://api.ipify.org').text

    @staticmethod
    def get_current_date_time():
        now = datetime.now()
        return now.strftime("%Y_%m_%d_%H_%M")

    @staticmethod
    def get_application_path():
        if getattr(sys, 'frozen', False):
            # If the application is run as a bundle, the PyInstaller bootloader
            # extends the sys module by a flag frozen=True and sets the app
            # path into variable _MEIPASS'.
            print(f"Getting application for executable {sys._MEIPASS}")
            application_path = sys._MEIPASS
        else:
            print("Getting application for file")
            application_path = os.path.dirname(os.path.abspath(__file__))

        return application_path

    @staticmethod
    def check_Yes(answer):
        if answer.lower() == "y":
            return True
        else:
            return False

    @staticmethod
    def merge(source, destination):
        for key, value in source.items():
            if isinstance(value, dict):
                # get node or create one
                node = destination.setdefault(key, {})
                Helpers.merge(value, node)
            else:
                destination[key] = value

        return destination

    @staticmethod
    def parse_trustednode(trustednode):
        import re
        if not bool(re.match(r"radix://(.*)@\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", trustednode)):
            print(f"Trusted node {trustednode} does match pattern radix://public_key@ip. Please enter right value")
            sys.exit()
        return trustednode.rsplit('@', 1)[-1]

    @staticmethod
    def json_response_check(resp):
        if Helpers.is_json(resp.content):
            json_response = json.loads(resp.content)
            if "error" in json_response:
                print(
                    f"{Bcolors.FAIL}\n Failed to submit changes Check the response for the error details{Bcolors.ENDC}")
        elif not resp.ok:
            print(f"{Bcolors.FAIL}\n Failed to submit changes")

    @staticmethod
    def check_validatorFee_input():
        while True:
            try:
                str_validatorFee = input(
                    f'{Bcolors.BOLD}Enter the validatorFee value between 0.00 to 100.00 as the validator fees:{Bcolors.ENDC}')
                validatorFee = float(str_validatorFee)
                if 0 <= validatorFee <= 100:
                    break
            except ValueError:
                pass
            print(
                f"{Bcolors.FAIL}The validatorFee value should between 0.00 to 100.00 as the validator fees!{Bcolors.ENDC}")
        return round(validatorFee, 2)

    @staticmethod
    def print_coloured_line(text, color="\033[0m", return_string=False):
        if not return_string:
            print(f"{color}{text}{Bcolors.ENDC}")
        else:
            return f"{color}{text}{Bcolors.ENDC}"

    @staticmethod
    def get_keyfile_path():
        radixnode_dir = f"{Helpers.get_home_dir()}/node-config"
        print(f"------ KEYSTORE FILE ----\n"
              f"\nThis keystore file is very important and it is the identity of the node."
              f"\nIf you are planning to run a validator, make sure you backup this keystore file"
              f"\nFolder Location for Keystore file will be: {radixnode_dir}")
        # TODO this needs to moved out of init
        run_shell_command(f'mkdir -p {radixnode_dir}', shell=True, quite=True)
        return str(radixnode_dir)

    @staticmethod
    def get_keyfile_name():
        default_keyfile_name = "node-keystore.ks"
        value = input(
            f"\nType in name of keystore file. Otherwise press 'Enter' to use default value '{default_keyfile_name}':").strip()
        if value != "":
            keyfile_name = value
        else:
            keyfile_name = default_keyfile_name

        return keyfile_name

    @staticmethod
    def get_basic_auth_header(user):
        import base64
        data = f"{user['name']}:{user['password']}"
        encodedBytes = base64.b64encode(data.encode("utf-8"))
        encodedStr = str(encodedBytes, "utf-8")
        headers = {
            'Authorization': f'Basic {encodedStr}'}
        return headers

    @staticmethod
    def handleApiException(e: ApiException):
        print(f"Exception-reason:{e.reason},status:{e.status}.body:{e.body}")
        sys.exit()

    @staticmethod
    def archivenode_deprecate_message():
        print(
            "Archive node is no more supported for core releases from 1.1.0 onwards. Use cli versions older than 1.0.11 to run or maintain archive nodes")
        sys.exit()

    @staticmethod
    def print_request_body(item, name):
        if os.getenv(PRINT_REQUEST):
            print(f"----Body for {name}---")
            print(item)

    @staticmethod
    def cli_version():
        return __version__

    @staticmethod
    def yaml_as_dict(my_file):
        my_dict = {}
        with open(my_file, 'r') as fp:
            docs = yaml.safe_load_all(fp)
            for doc in docs:
                for key, value in doc.items():
                    my_dict[key] = value
        return my_dict

    @staticmethod
    def get_home_dir():
        return Path.home()


class Bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
