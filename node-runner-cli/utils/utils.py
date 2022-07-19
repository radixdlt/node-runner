import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import requests
import yaml
from system_client import ApiException

from env_vars import PRINT_REQUEST, NODE_HOST_IP_OR_NAME, COMPOSE_HTTP_TIMEOUT
from utils.PromptFeeder import PromptFeeder
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
    if result.returncode != 0:
        print(result)
    if fail_on_error and result.returncode != 0:
        print("""
            Command failed. Exiting...
        """)
        sys.exit(1)
    return result


def print_vote_and_fork_info(health, engine_configuration):
    newest_fork = engine_configuration['forks'][-1]
    newest_fork_name = newest_fork['name']
    is_candidate = newest_fork['is_candidate']

    if health['current_fork_name'] == newest_fork_name:
        print(
            f"The node is currently running fork {bcolors.BOLD}{health['current_fork_name']}{bcolors.ENDC}, which is the newest fork in its configuration")
        print(f"{bcolors.WARNING}No action is needed{bcolors.ENDC}")
        return

    if not is_candidate:
        print(
            f"The node is currently running fork {bcolors.BOLD}{health['current_fork_name']}{bcolors.ENDC}. The node is aware of a newer fixed epoch fork ({newest_fork_name})")
        print(f"{bcolors.WARNING}This newer fork is not a candidate fork, so no action is needed{bcolors.ENDC}")
        return

    node_says_vote_required = health['fork_vote_status'] == 'VOTE_REQUIRED'
    if not node_says_vote_required:
        print(
            f"The node is currently running fork {bcolors.BOLD}{health['current_fork_name']}{bcolors.ENDC}. The node is aware of a newer candidate fork ({newest_fork_name})")
        print(
            f"{bcolors.WARNING}The node has already signalled the readiness for this candidate fork, so no action is needed{bcolors.ENDC}")
        return

    print(
        f"The node is currently running fork {bcolors.BOLD}{health['current_fork_name']}{bcolors.ENDC}. The node is aware of a newer candidate fork ({newest_fork_name})")
    print(f"{bcolors.WARNING}The node has not yet signalled the readiness for this fork{bcolors.ENDC}")


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
            If you not running nginx, then export below environment variable
                export NGINX=false
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
        result = run_shell_command(command, env={
            COMPOSE_HTTP_TIMEOUT: os.getenv(COMPOSE_HTTP_TIMEOUT, "200")
        }, fail_on_error=False)
        if result.returncode != 0:
            run_shell_command(command, env={
                COMPOSE_HTTP_TIMEOUT: os.getenv(COMPOSE_HTTP_TIMEOUT, "200")
            })

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
                if 0 <= validatorFee <= 100:
                    break
            except ValueError:
                pass
            print(
                f"{bcolors.FAIL}The validatorFee value should between 0.00 to 100.00 as the validator fees!{bcolors.ENDC}")
        return round(validatorFee, 2)

    @staticmethod
    def print_coloured_line(text, color="\033[0m", return_string=False):
        if not return_string:
            print(f"{color}{text}{bcolors.ENDC}")
        else:
            return f"{color}{text}{bcolors.ENDC}"

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
        sys.exit(1)

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

    @staticmethod
    def get_default_node_config_dir():
        return f"{Path.home()}/node-config"

    @staticmethod
    def get_default_monitoring_config_dir():
        return f"{Path.home()}/monitoring"

    @staticmethod
    def section_headline(title):
        print(f"{bcolors.BOLD}--------------{title}----------------------{bcolors.ENDC}")

    @staticmethod
    def input_guestion(question, question_key=None):
        prompt_feed = None
        if question_key:
            prompt_feed = PromptFeeder.instance().get_answer(question_key)
        if not prompt_feed:
            return input(f"\n{bcolors.WARNING}{question}{bcolors.ENDC}")
        else:
            print("Got from promptfeeder")
            print(f"Question is {question}")
            print(f"Answer is {prompt_feed}")
            return prompt_feed

    @staticmethod
    def print_info(info):
        print(f"{bcolors.OKBLUE}{info}{bcolors.ENDC}")

    @staticmethod
    def represent_none(self, _):
        return self.represent_scalar('tag:yaml.org,2002:null', '')

    @staticmethod
    def get_node_host_ip():
        if os.environ.get('%s' % NODE_HOST_IP_OR_NAME) is None:
            print(
                f"{NODE_HOST_IP_OR_NAME} environment variable not setup. Fetching the IP of node assuming the monitoring is run on the same machine machine as "
                "the node.")
            ip = Helpers.get_public_ip()
            node_endpoint = f"{ip}"
        else:
            node_endpoint = os.environ.get(NODE_HOST_IP_OR_NAME)
        return node_endpoint

    @staticmethod
    def dump_rendered_template(render_template, file_location, quiet=False):
        yaml.add_representer(type(None), Helpers.represent_none)
        if not quiet:
            print(f"\n{yaml.dump(render_template)}")
        print(f"\n\n Saving to file {file_location} ")
        with open(file_location, 'w') as f:
            yaml.dump(render_template, f, default_flow_style=False, explicit_start=True, allow_unicode=True)

    @staticmethod
    def backup_file(source: str, dest: str):
        import shutil
        shutil.copy2(source, dest)


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
