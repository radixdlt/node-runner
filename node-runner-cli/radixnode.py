import getpass
import os
import os.path
import sys
from argparse import ArgumentParser
from pathlib import Path

import requests
import urllib3
from github.github import latest_release
from requests.auth import HTTPBasicAuth
from utils.utils import run_shell_command
from utils.utils import Helpers
from version import __version__
from setup import Base, Docker, SystemD

urllib3.disable_warnings()

cli = ArgumentParser()
subparsers = cli.add_subparsers(dest="subcommand")
cwd = os.getcwd()


def argument(*name_or_flags, **kwargs):
    return list(name_or_flags), kwargs


def subcommand(args=[], parent=subparsers):
    def decorator(func):
        parser = parent.add_parser(func.__name__.replace("_", "-"), description=func.__doc__)
        for arg in args:
            parser.add_argument(*arg[0], **arg[1])
        parser.set_defaults(func=func)

    return decorator


def cli_version():
    return __version__


@subcommand([])
def version(args):
    print(f"Cli - Version : {cli_version()}")


@subcommand([

    argument("-r", "--release",
             help="Version of node software to install such as 1.0-beta.34",
             action="store"),
    argument("-n", "--nodetype", required=True, default="fullnode", help="Type of node fullnode or archivenode",
             action="store"),
    argument("-t", "--trustednode", required=True, help="Trusted node on radix network", action="store"),
    argument("-u", "--update", help="Update the node to new version of composefile", action="store_false"),
])
def setup_docker(args):
    if not args.release:
        release = latest_release()
    else:
        release = args.release
    composefileurl = f"https://github.com/radixdlt/radixdlt/releases/download/{release}/radix-{args.nodetype}-compose.yml"
    continue_setup = input(
        f"Going to setup node type {args.nodetype} for version {release} from location {composefileurl}.\n Do you want to continue Y/n:")

    if continue_setup != "Y":
        print(" Quitting ....")
        sys.exit()

    Docker.fetchComposeFile(composefileurl)
    keystore_password = Base.generatekey(keyfile_path=os.getcwd())
    Base.fetch_universe_json(args.trustednode)

    compose_file_name = composefileurl.rsplit('/', 1)[-1]
    action = "update" if args.update else "start"
    print(f"About to {action} the node using docker-compose file {compose_file_name}, which is as below")
    run_shell_command(f"cat {compose_file_name}", shell=True)
    should_start = input(f"\nOkay to start the node Y/n:")
    if should_start == "Y":
        if action == "update":
            print(f"For update, bringing down the node using compose file {compose_file_name}")
            Docker.run_docker_compose_down(compose_file_name)
        Docker.run_docker_compose_up(keystore_password, compose_file_name, args.trustednode)
    else:
        print(f"""
            ---------------------------------------------------------------
            Bring up node by updating the file {compose_file_name}
            You can do it through cli using below command
                ./radixnode stop-docker  -f {compose_file_name}
                ./radixnode start-docker -f {compose_file_name} -t {args.trustednode}
            ----------------------------------------------------------------
            """)


@subcommand([
    argument("-r", "--release",
             help="Version of node software to install",
             action="store"),
    argument("-t", "--trustednode", required=True, help="Trusted node on radix network", action="store"),
    argument("-n", "--nodetype", required=True, default="fullnode", help="Type of node fullnode or archivenode",
             action="store"),
    argument("-i", "--hostip", required=True, help="Static Public IP of the node", action="store"),
    argument("-u", "--update", help="Update the node to new version of node", action="store_false"),

])
def start_systemd(args):
    if not args.release:
        release = latest_release()
    else:
        release = args.release

    node_dir = '/etc/radixdlt/node'
    nginx_dir = '/etc/nginx'
    nginx_secrets_dir = f"{nginx_dir}/secrets"
    node_secrets_dir = f"{node_dir}/secrets"
    nodebinaryUrl = f"https://github.com/radixdlt/radixdlt/releases/download/{release}/radixdlt-dist-{release}.zip"

    # TODO add method to fetch latest nginx release
    nginxconfigUrl = f"https://github.com/radixdlt/radixdlt-nginx/releases/download/{release}/radixdlt-nginx-{args.nodetype}-conf.zip"

    continue_setup = input(
        f"Going to setup node type {args.nodetype} for version {release} from location {nodebinaryUrl} and {nginxconfigUrl}. \n Do you want to continue Y/n:")

    if continue_setup != "Y":
        print(" Quitting ....")
        sys.exit()

    backup_time = Helpers.get_current_date_time()
    SystemD.checkUser()
    keystore_password = SystemD.generatekey(node_secrets_dir)
    SystemD.fetch_universe_json(args.trustednode, node_dir)

    SystemD.backup_file(node_secrets_dir, f"environment", backup_time)
    SystemD.set_environment_variables(keystore_password, node_secrets_dir)

    SystemD.backup_file(node_dir, f"default.config", backup_time)
    SystemD.setup_default_config(trustednode=args.trustednode, hostip=args.hostip, node_dir=node_dir)

    node_version = nodebinaryUrl.rsplit('/', 2)[-2]
    SystemD.backup_file("/etc/systemd/system", "radixdlt-node.service", backup_time)
    SystemD.setup_service_file(node_version, node_dir=node_dir, node_secrets_path=node_secrets_dir)

    SystemD.download_binaries(nodebinaryUrl, node_dir=node_dir, node_version=node_version)

    SystemD.backup_file("/lib/systemd/system", f"nginx.service", backup_time)

    nginx_configured = SystemD.setup_nginx_config(nginx_config_location_Url=nginxconfigUrl,
                                                  node_type=args.nodetype,
                                                  nginx_etc_dir=nginx_dir, backup_time=backup_time)
    SystemD.create_ssl_certs(nginx_secrets_dir)
    if not args.update:
        SystemD.start_node_service()
    else:
        SystemD.restart_node_service()

    if nginx_configured and not args.update:
        SystemD.start_nginx_service()
    elif nginx_configured and args.update:
        SystemD.start_nginx_service()
    else:
        print("Nginx not configured or not updated")


@subcommand([
    argument("-s", "--services", default="all",
             help="Name of the service either to be stopped. Valid values nginx or radixdlt-node", action="store")
])
def stop_systemd(args):
    if args.services == "all":
        SystemD.stop_nginx_service()
        SystemD.stop_node_service()
    elif args.services == "nginx":
        SystemD.stop_nginx_service()
    elif args.services == "radixdlt-node":
        SystemD.stop_node_service()
    else:
        print(f"Invalid service name {args.services}")
        sys.exit()


@subcommand([
    argument("-f", "--composefile", required=True, help="The name of compose file ", action="store"),
    argument("-t", "--trustednode", required=True, help="Trusted node on radix network", action="store")
])
def start_docker(args):
    keystore_password = Base.generatekey(keyfile_path=os.getcwd())
    Docker.run_docker_compose_up(keystore_password, args.composefile, args.trustednode)


@subcommand([
    argument("-f", "--composefile", required=True, help="The name of compose file ", action="store"),
    argument("-v", "--removevolumes", help="Remove the volumes ", action="store_true"),
])
def stop_docker(args):
    if args.removevolumes:
        print(
            """ 
            Removing volumes including Nginx volume. Nginx password needs to be recreated again when you bring node up
            """)
    Docker.run_docker_compose_down(args.composefile, args.removevolumes)


@subcommand([])
def configure_docker(args):
    Base.install_dependecies()
    Base.add_user_docker_group()


@subcommand([])
def configure_systemd(args):
    Base.install_dependecies()
    SystemD.install_java()
    SystemD.setup_user()
    SystemD.make_etc_directory()
    SystemD.make_data_directory()
    SystemD.create_service_user_password()
    SystemD.create_initial_service_file()
    SystemD.sudoers_instructions()


@subcommand(
    [argument("-m", "--setupmode", required=True, help="Setup type whether it is DOCKER or SYSTEMD", action="store")])
def set_admin_password(args):
    if args.setupmode == "DOCKER":
        Docker.setup_nginx_Password()
    elif args.setupmode == "SYSTEMD":
        SystemD.checkUser()
        SystemD.install_nginx()
        SystemD.setup_nginx_password("/etc/nginx/secrets")
    else:
        print("Invalid setupmode specified. It should be either DOCKER or SYSTEMD.")


"""
  Below is the list of API commands 
"""


@subcommand()
def get_node_address(args):
    node_host = 'localhost'
    user = Helpers.get_nginx_user()
    req = requests.Request('GET',
                           f'https://{node_host}/node',
                           auth=HTTPBasicAuth(user["name"], user["password"]))
    prepared = req.prepare()
    Helpers.send_request(prepared)


@subcommand()
def get_peers(args):
    node_host = 'localhost'
    user = Helpers.get_nginx_user()
    req = requests.Request('GET',
                           f'https://{node_host}/system/peers',
                           auth=HTTPBasicAuth(user["name"], user["password"]))
    prepared = req.prepare()
    Helpers.send_request(prepared)


@subcommand()
def register_validator(args):
    node_host = 'localhost'
    user = Helpers.get_nginx_user()
    validator_name = input("Name of your validator:")
    validator_url = input("Info URL of your validator:")
    data = f"""
    {{"actions":
        [
        {{"action":"RegisterValidator",
        "params":{{
            "name": "{validator_name}",
            "url": "{validator_url}"
            }}
        }}
        ]
    }}
    """
    req = requests.Request('POST',
                           f'https://{node_host}/node/execute',
                           data=data,
                           auth=HTTPBasicAuth(user["name"], user["password"]))
    prepared = req.prepare()

    # prepared.body = json.dumps(u"""%s""" % data)
    prepared.headers['Content-Type'] = 'application/json'
    Helpers.send_request(prepared)


@subcommand()
def validator_info(args):
    node_host = 'localhost'
    user = Helpers.get_nginx_user()
    req = requests.Request('POST',
                           f'https://{node_host}/node/validator',
                           auth=HTTPBasicAuth(user["name"], user["password"]))
    prepared = req.prepare()

    prepared.headers['Content-Type'] = 'application/json'
    Helpers.send_request(prepared)


@subcommand()
def system_info(args):
    node_host = 'localhost'
    user = Helpers.get_nginx_user()
    req = requests.Request('GET',
                           f'https://{node_host}/system/info',
                           auth=HTTPBasicAuth(user["name"], user["password"]))
    prepared = req.prepare()

    prepared.headers['Content-Type'] = 'application/json'
    Helpers.send_request(prepared)


@subcommand(
    [argument("-m", "--setupmode", default="QUICK_SETUP_MODE",
              help="Setup type whether it is QUICK_SETUP_MODE or PRODUCTION_MODE",
              action="store")])
def setup_monitoring(args):
    if args.setupmode == "QUICK_SETUP_MODE":
        monitor_url_dir = f'https://raw.githubusercontent.com/radixdlt/node-runner/{cli_version()}/monitoring'
        print(f"Downloading artifacts from {monitor_url_dir}\n")
        Monitoring.setup_prometheus_yml(f"{monitor_url_dir}/prometheus/prometheus.yml")
        Monitoring.setup_datasource(f"{monitor_url_dir}/grafana/provisioning/datasources/datasource.yml")
        Monitoring.setup_dashboard(f"{monitor_url_dir}/grafana/provisioning/dashboards/",
                                   ["dashboard.yml", "sample-node-dashboard.json"])
        Monitoring.setup_monitoring_containers(f"{monitor_url_dir}/node-monitoring.yml")
        Monitoring.setup_external_volumes()
        Monitoring.start_monitoring(f"monitoring/node-monitoring.yml")
    elif args.setupmode == "PRODUCTION_MODE":
        print(" PRODUCTION_MODE not supported yet ")
        sys.exit()
    else:
        print("Invalid setup mode . It should be either QUICK_SETUP_MODE or PRODUCTION_MODE")


@subcommand([
    argument("-m", "--setupmode", default="QUICK_SETUP_MODE",
             help="Setup type whether it is QUICK_SETUP_MODE or PRODUCTION_MODE",
             action="store"),
    argument("-v", "--removevolumes", help="Remove the volumes ", action="store_true")])
def stop_monitoring(args):
    if args.setupmode == "QUICK_SETUP_MODE":
        Monitoring.stop_monitoring(f"monitoring/node-monitoring.yml", args.removevolumes)
    elif args.setupmode == "PRODUCTION_MODE":
        print(" PRODUCTION_MODE not supported yet ")
        sys.exit()
    else:
        print("Invalid setup mode . It should be either QUICK_SETUP_MODE or PRODUCTION_MODE")

@subcommand([])
def check_ansible(args):
    Base.setup_node_optimisation_config(cli_version())

class Monitoring():

    @staticmethod
    def setup_prometheus_yml(default_prometheus_yaml_url):
        req = requests.Request('GET', f'{default_prometheus_yaml_url}')
        prepared = req.prepare()

        resp = Helpers.send_request(prepared, print_response=False)
        Path("monitoring/prometheus").mkdir(parents=True, exist_ok=True)
        with open("monitoring/prometheus/prometheus.yml", 'wb') as f:
            f.write(resp.content)

    @staticmethod
    def setup_datasource(default_datasource_cfg_url):
        req = requests.Request('GET', f'{default_datasource_cfg_url}')
        prepared = req.prepare()
        resp = Helpers.send_request(prepared, print_response=False)
        Path("monitoring/grafana/provisioning/datasources").mkdir(parents=True, exist_ok=True)
        with open("monitoring/grafana/provisioning/datasources/datasource.yml", 'wb') as f:
            f.write(resp.content)

    @staticmethod
    def setup_dashboard(default_dashboard_cfg_url, files):
        for file in files:
            req = requests.Request('GET', f'{default_dashboard_cfg_url}/{file}')
            prepared = req.prepare()
            resp = Helpers.send_request(prepared, print_response=False)
            Path("monitoring/grafana/provisioning/dashboards").mkdir(parents=True, exist_ok=True)
            with open(f"monitoring/grafana/provisioning/dashboards/{file}", 'wb') as f:
                f.write(resp.content)

    @staticmethod
    def setup_external_volumes():
        run_shell_command(["docker", "volume", "create", "prometheus_tsdb"])
        run_shell_command(["docker", "volume", "create", "grafana-storage"])

    @staticmethod
    def setup_monitoring_containers(default_monitoring_cfg_url):
        req = requests.Request('GET', f'{default_monitoring_cfg_url}')
        prepared = req.prepare()
        resp = Helpers.send_request(prepared, print_response=False)
        Path("monitoring").mkdir(parents=True, exist_ok=True)
        with open("monitoring/node-monitoring.yml", 'wb') as f:
            f.write(resp.content)

    @staticmethod
    def start_monitoring(composefile):
        user = Helpers.get_nginx_user()
        node_endpoint_env = "NODE_END_POINT"
        if os.environ.get('%s' % node_endpoint_env) is None:
            ip = Helpers.get_public_ip()
            node_endpoint = f"https://{ip}"
        else:
            node_endpoint = os.environ.get(node_endpoint_env)
        run_shell_command(f'docker-compose -f {composefile} up -d',
                          env={
                              "BASIC_AUTH_USER_CREDENTIALS": f'{user["name"]}:{user["password"]}',
                              "NODE_END_POINT": node_endpoint
                          }, shell=True)

    @staticmethod
    def stop_monitoring(composefile, remove_volumes):
        Helpers.docker_compose_down(composefile, remove_volumes)


if __name__ == "__main__":
    args = cli.parse_args()
    if args.subcommand is None:
        cli.print_help()
    else:
        args.func(args)
