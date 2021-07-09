import json
import subprocess
from datetime import datetime
import requests
import sys, os
from pathlib import Path

from env_vars import PRINT_REQUEST


def printCommand(cmd):
    print('-----------------------------')
    if type(cmd) is list:
        print('Running command :' + ' '.join(cmd))
        print('-----------------------------')
    else:
        print('Running command ' + cmd)
        print('-----------------------------')


def run_shell_command(cmd, env=None, shell=False, fail_on_error=True, quite=False):
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
                    f"{bcolors.FAIL}\n Failed to submit changes Check the response for the error details{bcolors.ENDC}")
        elif not resp.ok:
            print(f"{bcolors.FAIL}\n Failed to submit changes")

    @staticmethod
    def check_validatorFee_input():
        while True:
            try:
                str_validatorFee = input(
                    f'{bcolors.BOLD}Enter the validatorFee value between 0.00 to 100.00 as the validator fees:{bcolors.ENDC}')
                validatorFee = float(str_validatorFee)
                integral, fractional = str_validatorFee.split('.')
                if len(fractional) <= 2 and len(integral) <= 2:
                    break
            except ValueError:
                pass
            print(
                f"{bcolors.FAIL}The validatorFee value should between 0.00 to 100.00 as the validator fees!{bcolors.ENDC}")
        return int(validatorFee)

    @staticmethod
    def print_coloured_line(text, color="\033[0m", return_string=False):
        if not return_string:
            print(f"{color}{text}{bcolors.ENDC}")
        else:
            return f"{color}{text}{bcolors.ENDC}"

    @staticmethod
    def get_keyfile_path():
        radixnode_dir = f"{Path.home()}/node-config"
        print(f"Path to keyfile is {radixnode_dir}")
        run_shell_command(f'mkdir -p {radixnode_dir}', shell=True)
        return str(radixnode_dir)


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
