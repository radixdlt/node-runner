from pathlib import Path

import requests
import sys

from utils.utils import run_shell_command, Helpers, bcolors
import subprocess


class AnsibleRunner:

    def __init__(self, ansible_dir):
        self.ansible_dir = ansible_dir

    def download_ansible_file(self, file):
        print(f"Downloading artifacts from {self.ansible_dir}\n")
        req = requests.Request('GET', f'{self.ansible_dir}/{file}')
        prepared = req.prepare()

        resp = Helpers.send_request(prepared, print_response=False)
        if not resp.ok:
            print(f"{resp.status_code} error retrieving ansible playbook.. Existing the command...")
            sys.exit()

        directory = file.rsplit('/', 1)[0]
        Path(directory).mkdir(parents=True, exist_ok=True)
        with open(file, 'wb') as f:
            f.write(resp.content)

    def check_install_ansible(self, exit_cmd=False):
        check_ansible = run_shell_command(f"pip list | grep ansible", shell=True, fail_on_error=False)
        user = subprocess.check_output('whoami', shell=True).strip()
        if check_ansible.returncode != 0:
            print(f"Ansible not found for the user {user.decode('utf-8')}. Installing ansible now")
            check_pip = run_shell_command("pip -V ", shell=True, fail_on_error=False)
            if check_pip.returncode != 0:
                print(f"Pip is not installed. Installing pip now")
                run_shell_command('sudo apt install python3-pip -y', shell=True)
            run_shell_command(f"pip install --user ansible==2.10.0", shell=True)
            print("----------------------------------------------------------------------------------------\n"
                  f"{bcolors.WARNING}Ansible installed successfully. You need exit shell and login back{bcolors.ENDC}")
            if exit_cmd:
                sys.exit()
        return

    @classmethod
    def run_setup_limits(cls, setup_limits):
        run_shell_command(
            f"ansible-playbook ansible/project/provision.yml -e setup_limits={setup_limits}",
            shell=True)

    def run_swap_size(self, setup_swap, setup_swap_size):
        run_shell_command(
            f"ansible-playbook ansible/project/provision.yml -e setup_swap={setup_swap} -e swap_size={setup_swap_size}",
            shell=True)

    def run_setup_postgress(self, postgress_password, postgresql_user, postgresql_db_name, file):
        self.check_install_ansible()
        self.download_ansible_file(file)
        run_shell_command(f"ansible-galaxy collection install community.postgresql", shell=True)
        run_shell_command(
            f"ansible-playbook ansible/project/provision.yml -e postgres_local='true' "
            f"-e postgress_password={postgress_password} -e postgresql_user={postgresql_user} "
            f"-e postgresql_db_name={postgresql_db_name}",
            shell=True)
