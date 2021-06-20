#!/usr/bin/env python
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
from env_vars import COMPOSE_FILE_OVERIDE, NODE_BINARY_OVERIDE, NGINX_BINARY_OVERIDE, NODE_END_POINT, \
    DISABLE_VERSION_CHECK
from setup import Base, Docker, SystemD

urllib3.disable_warnings()

cli = ArgumentParser()
cli.add_argument('subcommand', help='Subcommand to run',
                 choices=["docker", "systemd", "api", "monitoring", "version", "optimise-node", "auth"])
dockercli = ArgumentParser(
    description='Docker commands')
docker_parser = dockercli.add_subparsers(dest="dockercommand")
systemdcli = ArgumentParser(
    description='Systemd commands')
systemd_parser = systemdcli.add_subparsers(dest="systemdcommand")
apicli = ArgumentParser(
    description='API commands')
api_parser = apicli.add_subparsers(dest="apicommand")

cwd = os.getcwd()


def argument(*name_or_flags, **kwargs):
    return list(name_or_flags), kwargs


def subcommand(args=[], parent=docker_parser):
    def decorator(func):
        parser = parent.add_parser(func.__name__.replace("_", "-"), description=func.__doc__)
        for arg in args:
            parser.add_argument(*arg[0], **arg[1])
        parser.set_defaults(func=func)

    return decorator


def dockercommand(args=[], parent=docker_parser):
    def decorator(func):
        parser = parent.add_parser(func.__name__.replace("_", "-"), description=func.__doc__)
        for arg in args:
            parser.add_argument(*arg[0], **arg[1])
        parser.set_defaults(func=func)

    return decorator


def systemdcommand(args=[], parent=systemd_parser):
    def decorator(func):
        parser = parent.add_parser(func.__name__.replace("_", "-"), description=func.__doc__)
        for arg in args:
            parser.add_argument(*arg[0], **arg[1])
        parser.set_defaults(func=func)

    return decorator


def systemdcommand(args=[], parent=systemd_parser):
    def decorator(func):
        parser = parent.add_parser(func.__name__.replace("_", "-"), description=func.__doc__)
        for arg in args:
            parser.add_argument(*arg[0], **arg[1])
        parser.set_defaults(func=func)

    return decorator


def apicommand(args=[], parent=api_parser):
    def decorator(func):
        parser = parent.add_parser(func.__name__.replace("_", "-"), description=func.__doc__)
        for arg in args:
            parser.add_argument(*arg[0], **arg[1])
        parser.set_defaults(func=func)

    return decorator


monitoringcli = ArgumentParser(
    description='API command')
monitoring_parser = monitoringcli.add_subparsers(dest="monitoringcommand")


def monitoringcommand(args=[], parent=monitoring_parser):
    def decorator(func):
        parser = parent.add_parser(func.__name__.replace("_", "-"), description=func.__doc__)
        for arg in args:
            parser.add_argument(*arg[0], **arg[1])
        parser.set_defaults(func=func)

    return decorator


authcli = ArgumentParser(
    description='API command')
auth_parser = authcli.add_subparsers(dest="authcommand")


def authcommand(args=[], parent=auth_parser):
    def decorator(func):
        parser = parent.add_parser(func.__name__.replace("_", "-"), description=func.__doc__)
        for arg in args:
            parser.add_argument(*arg[0], **arg[1])
        parser.set_defaults(func=func)

    return decorator


def cli_version():
    return __version__


def version():
    print(f"Cli - Version : {cli_version()}")


@dockercommand([

    argument("-r", "--release",
             help="Version of node software to install such as 1.0-beta.34",
             action="store"),
    argument("-n", "--nodetype", required=True, default="fullnode", help="Type of node fullnode or archivenode",
             action="store", choices=["fullnode", "archivenode"]),
    argument("-t", "--trustednode", required=True,
             help="Trusted node on radix network. Example format: radix//brn1q0mgwag0g9f0sv9fz396mw9rgdall@10.1.2.3",
             action="store"),
    argument("-u", "--update", help="Update the node to new version of composefile", action="store_false"),
])
def setup(args):
    if not args.release:
        release = latest_release()
    else:
        release = args.release
    composefileurl = os.getenv(COMPOSE_FILE_OVERIDE,
                               f"https://github.com/radixdlt/radixdlt/releases/download/{release}/radix-{args.nodetype}-compose.yml")
    print(f"Going to setup node type {args.nodetype} for version {release} from location {composefileurl}.\n")
    # TODO autoapprove
    continue_setup = input(
        "Do you want to continue [Y/n]?:")

    if not Helpers.check_Yes(continue_setup):
        print(" Quitting ....")
        sys.exit()

    Docker.fetchComposeFile(composefileurl)
    keystore_password = Base.generatekey(keyfile_path=os.getcwd())

    trustednode_ip = Helpers.parse_trustednode(args.trustednode)
    Base.fetch_universe_json(trustednode_ip)

    compose_file_name = composefileurl.rsplit('/', 1)[-1]
    action = "update" if args.update else "start"
    print(f"About to {action} the node using docker-compose file {compose_file_name}, which is as below")
    run_shell_command(f"cat {compose_file_name}", shell=True)
    # TODO AutoApprove
    should_start = input(f"\nOkay to start the node [Y/n]?:")
    if Helpers.check_Yes(should_start):
        if action == "update":
            print(f"For update, bringing down the node using compose file {compose_file_name}")
            Docker.run_docker_compose_down(compose_file_name)
        Docker.run_docker_compose_up(keystore_password, compose_file_name, args.trustednode)
    else:
        print(f"""
            ---------------------------------------------------------------
            Bring up node by updating the file {compose_file_name}
            You can do it through cli using below command
                radixnode docker stop  -f {compose_file_name}
                radixnode docker start -f {compose_file_name} -t {args.trustednode}
            ----------------------------------------------------------------
            """)


@systemdcommand([
    argument("-r", "--release",
             help="Version of node software to install",
             action="store"),
    argument("-t", "--trustednode", required=True, help="Trusted node on radix network", action="store"),
    argument("-n", "--nodetype", required=True, default="fullnode", help="Type of node fullnode or archivenode",
             action="store", choices=["fullnode", "archivenode"]),
    argument("-i", "--hostip", required=True, help="Static Public IP of the node", action="store"),
    argument("-u", "--update", help="Update the node to new version of node", action="store_false"),

])
def setup(args):
    if not args.release:
        release = latest_release()
    else:
        release = args.release

    if args.nodetype == "archivenode":
        node_type_name = 'archive'
    elif args.nodetype == "fullnode":
        node_type_name = 'fullnode'
    else:
        print(f"Node type - {args.nodetype} specificed should be either archivenode or fullnode")
        sys.exit()

    node_dir = '/etc/radixdlt/node'
    nginx_dir = '/etc/nginx'
    nginx_secrets_dir = f"{nginx_dir}/secrets"
    node_secrets_dir = f"{node_dir}/secrets"
    nodebinaryUrl = os.getenv(NODE_BINARY_OVERIDE,
                              f"https://github.com/radixdlt/radixdlt/releases/download/{release}/radixdlt-dist-{release}.zip")

    # TODO add method to fetch latest nginx release
    nginxconfigUrl = os.getenv(NGINX_BINARY_OVERIDE,
                               f"https://github.com/radixdlt/radixdlt-nginx/releases/download/{release}/radixdlt-nginx-{node_type_name}-conf.zip")
    # TODO AutoApprove
    continue_setup = input(
        f"Going to setup node type {args.nodetype} for version {release} from location {nodebinaryUrl} and {nginxconfigUrl}. \n Do you want to continue Y/n:")

    if not Helpers.check_Yes(continue_setup):
        print(" Quitting ....")
        sys.exit()

    backup_time = Helpers.get_current_date_time()
    SystemD.checkUser()
    keystore_password = SystemD.generatekey(node_secrets_dir)
    trustednode_ip = Helpers.parse_trustednode(args.trustednode)
    SystemD.fetch_universe_json(trustednode_ip, node_dir)

    SystemD.backup_file(node_secrets_dir, f"environment", backup_time)
    SystemD.set_environment_variables(keystore_password, node_secrets_dir)

    SystemD.backup_file(node_dir, f"default.config", backup_time)
    SystemD.setup_default_config(trustednode=args.trustednode, hostip=args.hostip, node_dir=node_dir,
                                 node_type=args.nodetype)

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


@systemdcommand([
    argument("-s", "--services", default="all",
             help="Name of the service either to be stopped. Valid values nginx or radixdlt-node",
             choices=["all", "nginx", "radixdlt-node"], action="store")
])
def stop(args):
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


@dockercommand([
    argument("-f", "--composefile", required=True, help="The name of compose file ", action="store"),
    argument("-t", "--trustednode", required=True, help="Trusted node on radix network", action="store")
])
def start(args):
    keystore_password = Base.generatekey(keyfile_path=os.getcwd())
    Docker.run_docker_compose_up(keystore_password, args.composefile, args.trustednode)


@dockercommand([
    argument("-f", "--composefile", required=True, help="The name of compose file ", action="store"),
    argument("-v", "--removevolumes", help="Remove the volumes ", action="store_true"),
])
def stop(args):
    if args.removevolumes:
        print(
            """ 
            Removing volumes including Nginx volume. Nginx password needs to be recreated again when you bring node up
            """)
    Docker.run_docker_compose_down(args.composefile, args.removevolumes)


@dockercommand([])
def configure(args):
    Base.install_dependecies()
    Base.add_user_docker_group()


@systemdcommand([])
def configure(args):
    Base.install_dependecies()
    SystemD.install_java()
    SystemD.setup_user()
    SystemD.make_etc_directory()
    SystemD.make_data_directory()
    SystemD.create_service_user_password()
    SystemD.create_initial_service_file()
    SystemD.sudoers_instructions()


@authcommand(
    [
        argument("-m", "--setupmode", required=True, help="Setup type whether it is DOCKER or SYSTEMD",
                 choices=["DOCKER", "SYSTEMD"], action="store"),
        argument("-u", "--username", default="admin", help="Name of admin user", action="store")
    ])
def set_admin_password(args):
    set_auth(args, usertype="admin")


@authcommand(
    [
        argument("-m", "--setupmode", required=True, help="Setup type whether it is DOCKER or SYSTEMD",
                 choices=["DOCKER", "SYSTEMD"], action="store"),
        argument("-u", "--username", default="metrics", help="Name of metrics user", action="store")
    ])
def set_metrics_password(args):
    set_auth(args, usertype="metrics")


@authcommand(
    [
        argument("-m", "--setupmode", required=True, help="Setup type whether it is DOCKER or SYSTEMD",
                 choices=["DOCKER", "SYSTEMD"], action="store"),
        argument("-u", "--username", default="superadmin", help="Name of metrics user", action="store")
    ])
def set_superadmin_password(args):
    set_auth(args, usertype="superadmin")


def set_auth(args, usertype):
    if args.setupmode == "DOCKER":
        Docker.setup_nginx_Password(usertype, args.username)
    elif args.setupmode == "SYSTEMD":
        SystemD.checkUser()
        SystemD.install_nginx()
        SystemD.setup_nginx_password("/etc/nginx/secrets", usertype, args.username)
    else:
        print("Invalid setupmode specified. It should be either DOCKER or SYSTEMD.")


"""
  Below is the list of API commands 
"""


@apicommand()
def get_node_address(args):
    node_host = 'localhost'
    user = Helpers.get_nginx_user(usertype="admin", default_username="admin")
    req = requests.Request('GET',
                           f'https://{node_host}/node',
                           auth=HTTPBasicAuth(user["name"], user["password"]))
    prepared = req.prepare()
    Helpers.send_request(prepared)


@apicommand()
def get_peers(args):
    node_host = 'localhost'
    user = Helpers.get_nginx_user(usertype="admin", default_username="admin")
    req = requests.Request('GET',
                           f'https://{node_host}/system/peers',
                           auth=HTTPBasicAuth(user["name"], user["password"]))
    prepared = req.prepare()
    Helpers.send_request(prepared)


@apicommand()
def register_validator(args):
    node_host = 'localhost'
    user = Helpers.get_nginx_user(usertype="admin", default_username="admin")
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


@apicommand()
def validator_info(args):
    node_host = 'localhost'
    user = Helpers.get_nginx_user(usertype="admin", default_username="admin")
    req = requests.Request('POST',
                           f'https://{node_host}/node/validator',
                           auth=HTTPBasicAuth(user["name"], user["password"]))
    prepared = req.prepare()

    prepared.headers['Content-Type'] = 'application/json'
    Helpers.send_request(prepared)


@apicommand()
def system_info(args):
    node_host = 'localhost'
    user = Helpers.get_nginx_user(usertype="admin", default_username="admin")
    req = requests.Request('GET',
                           f'https://{node_host}/system/info',
                           auth=HTTPBasicAuth(user["name"], user["password"]))
    prepared = req.prepare()

    prepared.headers['Content-Type'] = 'application/json'
    Helpers.send_request(prepared)


@monitoringcommand(
    [argument("-m", "--setupmode", default="QUICK_SETUP_MODE",
              help="Setup type whether it is QUICK_SETUP_MODE or PRODUCTION_MODE",
              action="store")])
def setup(args):
    if args.setupmode == "QUICK_SETUP_MODE":
        monitor_url_dir = f'https://raw.githubusercontent.com/radixdlt/node-runner/{cli_version()}/monitoring'
        print(f"Downloading artifacts from {monitor_url_dir}\n")
        Monitoring.setup_prometheus_yml(f"{monitor_url_dir}/prometheus/prometheus.yml")
        Monitoring.setup_datasource(f"{monitor_url_dir}/grafana/provisioning/datasources/datasource.yml")
        Monitoring.setup_dashboard(f"{monitor_url_dir}/grafana/provisioning/dashboards/",
                                   ["dashboard.yml", "sample-node-dashboard.json"])
        Monitoring.setup_monitoring_containers(f"{monitor_url_dir}/node-monitoring.yml")
        Monitoring.setup_external_volumes()

        monitoring_file_location = "monitoring/node-monitoring.yml"
        start_monitoring_answer = input(
            f"Do you want to start monitoring using file as {monitoring_file_location} [Y/n]?")
        if Helpers.check_Yes(start_monitoring_answer):
            Monitoring.start_monitoring(f"{monitoring_file_location}")

    elif args.setupmode == "PRODUCTION_MODE":
        print(" PRODUCTION_MODE not supported yet ")
        sys.exit()
    else:
        print("Invalid setup mode . It should be either QUICK_SETUP_MODE or PRODUCTION_MODE")


@monitoringcommand(
    [
        argument("-f", "--composefile", default="monitoring/node-monitoring.yml", action="store"),
        argument("-m", "--setupmode", default="QUICK_SETUP_MODE",
                 help="Setup type whether it is QUICK_SETUP_MODE or PRODUCTION_MODE",
                 action="store")
    ]
)
def start(args):
    if args.setupmode == "QUICK_SETUP_MODE":
        Monitoring.start_monitoring(f"monitoring/node-monitoring.yml")
    elif args.setupmode == "PRODUCTION_MODE":
        print(" PRODUCTION_MODE not supported yet ")
        sys.exit()
    else:
        print("Invalid setup mode . It should be either QUICK_SETUP_MODE or PRODUCTION_MODE")


@monitoringcommand([
    argument("-m", "--setupmode", default="QUICK_SETUP_MODE",
             help="Setup type whether it is QUICK_SETUP_MODE or PRODUCTION_MODE",
             action="store"),
    argument("-v", "--removevolumes", help="Remove the volumes ", action="store_true")])
def stop(args):
    if args.setupmode == "QUICK_SETUP_MODE":
        Monitoring.stop_monitoring(f"monitoring/node-monitoring.yml", args.removevolumes)
    elif args.setupmode == "PRODUCTION_MODE":
        print(" PRODUCTION_MODE not supported yet ")
        sys.exit()
    else:
        print("Invalid setup mode . It should be either QUICK_SETUP_MODE or PRODUCTION_MODE")


def optimise_node():
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
        user = Helpers.get_nginx_user(usertype="metrics", default_username="metrics")
        if os.environ.get('%s' % NODE_END_POINT) is None:
            print(
                f"{NODE_END_POINT} environment not setup. Fetching the IP of node assuming the monitoring is run on the same machine machine as "
                "the node.")
            ip = Helpers.get_public_ip()
            node_endpoint = f"https://{ip}"
        else:
            node_endpoint = os.environ.get(NODE_END_POINT)
        run_shell_command(f'docker-compose -f {composefile} up -d',
                          env={
                              "BASIC_AUTH_USER_CREDENTIALS": f'{user["name"]}:{user["password"]}',
                              f"{NODE_END_POINT}": node_endpoint
                          }, shell=True)

    @staticmethod
    def stop_monitoring(composefile, remove_volumes):
        Helpers.docker_compose_down(composefile, remove_volumes)


def check_latest_cli():
    cli_latest_version = latest_release("radixdlt/node-runner")

    if os.getenv(DISABLE_VERSION_CHECK, "False").lower() not in ("true", "yes"):
        if cli_version() != cli_latest_version:
            os_name = "ubuntu-20.04"
            print(
                f"Radixnode CLI latest version is {cli_latest_version} and current version of the binary is {cli_version()}.\n.")
            print(f"""
                ---------------------------------------------------------------
                Update the CLI by running these commands
                    wget -O radixnode https://github.com/radixdlt/node-runner/releases/download/{cli_latest_version}/radixnode-{os_name}
                    chmod +x radixnode
                    sudo mv radixnode /usr/local/bin
                """)
            abort = input("Do you want to ABORT the command now to update the cli Y/n?:")
            if Helpers.check_Yes(abort):
                sys.exit()


if __name__ == "__main__":

    args = cli.parse_args(sys.argv[1:2])

    if args.subcommand is None:
        cli.print_help()
    else:
        if args.subcommand != "version":
            check_latest_cli()

    if args.subcommand == "docker":
        dockercli_args = dockercli.parse_args(sys.argv[2:])
        if dockercli_args.dockercommand is None:
            dockercli.print_help()
        else:
            dockercli_args.func(dockercli_args)

    elif args.subcommand == "systemd":
        systemdcli_args = systemdcli.parse_args(sys.argv[2:])
        if systemdcli_args.systemdcommand is None:
            systemdcli.print_help()
        else:
            systemdcli_args.func(systemdcli_args)

    elif args.subcommand == "api":
        apicli_args = apicli.parse_args(sys.argv[2:])
        if apicli_args.apicommand is None:
            apicli.print_help()
        else:
            apicli_args.func(apicli_args)
    elif args.subcommand == "monitoring":
        monitoringcli_args = monitoringcli.parse_args(sys.argv[2:])
        if monitoringcli_args.monitoringcommand is None:
            monitoringcli.print_help()
        else:
            monitoringcli_args.func(monitoringcli_args)
    elif args.subcommand == "auth":
        authcli_args = authcli.parse_args(sys.argv[2:])
        if authcli_args.authcommand is None:
            authcli.print_help()
        else:
            authcli_args.func(authcli_args)
    elif args.subcommand == "version":
        version()
    elif args.subcommand == "optimise-node":
        optimise_node()
    else:
        print(f"Invalid subcommand {args.subcommand}")
