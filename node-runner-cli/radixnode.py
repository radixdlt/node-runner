#!/usr/bin/env python
import json
import os
import os.path
import sys
from argparse import ArgumentParser
from pathlib import Path

import requests
import urllib3

from api.Account import Account
from api.RestApi import RestApi
from api.System import System
from api.Validation import Validation
from github.github import latest_release
from monitoring import Monitoring
from utils.utils import run_shell_command
from utils.utils import Helpers
from utils.utils import bcolors

from version import __version__
from env_vars import COMPOSE_FILE_OVERIDE, NODE_BINARY_OVERIDE, NGINX_BINARY_OVERIDE, NODE_END_POINT, \
    DISABLE_VERSION_CHECK
from setup import Base, Docker, SystemD

urllib3.disable_warnings()

cli = ArgumentParser()
cli.add_argument('subcommand', help='Subcommand to run',
                 choices=["docker", "systemd", "api", "monitoring", "version", "optimise-node", "auth"])

apicli = ArgumentParser(
    description='API commands')
api_parser = apicli.add_argument(dest="apicommand",
                                 choices=["validation", "account", "health", "version", "universe", "metrics",
                                          "system"])

cwd = os.getcwd()


def get_decorator(args, parent):
    def decorator(func):
        parser = parent.add_parser(func.__name__.replace("_", "-"), description=func.__doc__)
        for arg in args:
            parser.add_argument(*arg[0], **arg[1])
        parser.set_defaults(func=func)

    return decorator


def argument(*name_or_flags, **kwargs):
    return list(name_or_flags), kwargs


dockercli = ArgumentParser(
    description='Docker commands')
docker_parser = dockercli.add_subparsers(dest="dockercommand")


def dockercommand(args=[], parent=docker_parser):
    return get_decorator(args, parent)


systemdcli = ArgumentParser(
    description='Systemd commands')
systemd_parser = systemdcli.add_subparsers(dest="systemdcommand")


def systemdcommand(args=[], parent=systemd_parser):
    return get_decorator(args, parent)


validationcli = ArgumentParser(
    description='validation commands')
validation_parser = validationcli.add_subparsers(dest="validationcommand")


def validationcommand(args=[], parent=validation_parser):
    return get_decorator(args, parent)


accountcli = ArgumentParser(
    description='account commands')
account_parser = accountcli.add_subparsers(dest="accountcommand")


def accountcommand(args=[], parent=account_parser):
    return get_decorator(args, parent)


systemapicli = ArgumentParser(
    description='systemapi commands')
systemapi_parser = systemapicli.add_subparsers(dest="systemapicommand")


def systemapicommand(args=[], parent=systemapi_parser):
    return get_decorator(args, parent)


monitoringcli = ArgumentParser(
    description='API command')
monitoring_parser = monitoringcli.add_subparsers(dest="monitoringcommand")


def monitoringcommand(args=[], parent=monitoring_parser):
    return get_decorator(args, parent)


authcli = ArgumentParser(
    description='API command')
auth_parser = authcli.add_subparsers(dest="authcommand")


def authcommand(args=[], parent=auth_parser):
    return get_decorator(args, parent)


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

    keystore_password, file_location = Base.generatekey(keyfile_path=Helpers.get_keyfile_path())
    Docker.setup_compose_file(composefileurl, file_location)

    trustednode_ip = Helpers.parse_trustednode(args.trustednode)

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
    keystore_password, keyfile_location = SystemD.generatekey(node_secrets_dir)
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


@systemdcommand([
    argument("-s", "--services", default="all",
             help="Name of the service either to be started. Valid values nginx or radixdlt-node",
             choices=["all", "nginx", "radixdlt-node"], action="store")
])
def restart(args):
    if args.services == "all":
        SystemD.restart_node_service()
        SystemD.restart_nginx_service()
    elif args.services == "nginx":
        SystemD.restart_nginx_service()
    elif args.services == "radixdlt-node":
        SystemD.restart_node_service()
    else:
        print(f"Invalid service name {args.services}")
        sys.exit()


@dockercommand([
    argument("-f", "--composefile", required=True, help="The name of compose file ", action="store"),
    argument("-t", "--trustednode", required=True, help="Trusted node on radix network", action="store")
])
def start(args):
    keystore_password = Base.generatekey(keyfile_path=Helpers.get_keyfile_path())
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


@validationcommand()
def get_validator_info(args):
    Validation.get_validator_info()


@validationcommand()
def get_next_epoch_data(args):
    Validation.get_next_epoch_data()


@validationcommand()
def get_current_epoch_data(args):
    Validation.get_current_epoch_data()


@accountcommand()
def register_validator(args):
    request_data = {
        "jsonrpc": "2.0",
        "method": "account.submit_transaction_single_step",
        "params": {
            "actions": []
        },
        "id": 1
    }
    RestApi.check_health()

    validator_info = Validation.get_validator_info_json()

    user = Helpers.get_nginx_user(usertype="superadmin", default_username="superadmin")
    request_data = Account.register_or_update_steps(request_data, validator_info)
    request_data = Account.add_update_rake(request_data, validator_info)
    request_data = Account.setup_update_delegation(request_data, validator_info)
    request_data = Account.add_change_ownerid(request_data, validator_info)

    print(f"{bcolors.WARNING}\nAbout to update node account with following{bcolors.ENDC}")
    print(f"")
    print(f"{bcolors.BOLD}{json.dumps(request_data, indent=4, sort_keys=True)}{bcolors.ENDC}")
    submit_changes = input(f"{bcolors.BOLD}\nDo you want to continue [Y/n]{bcolors.ENDC}")
    if Helpers.check_Yes(submit_changes) and len(request_data["params"]["actions"]) != 0:
        Account.post_on_account(json.dumps(request_data))
    else:
        print(f"{bcolors.WARNING} Changes were not submitted.{bcolors.ENDC} or there are no actions to submit")


@accountcommand()
def unregister_validator(args):
    RestApi.check_health()
    Account.un_register_validator()


@accountcommand()
def get_info(args):
    Account.get_info()


@systemapicommand()
def api_get_configuration(args):
    System.api_get_configuration()


@systemapicommand()
def api_get_data(args):
    System.api_get_data()


@systemapicommand()
def bft_get_configuration(args):
    System.bft_get_configuration()


@systemapicommand()
def bft_get_data(args):
    System.bft_get_data()


@systemapicommand()
def mempool_get_configuration(args):
    System.mempool_get_configuration()


@systemapicommand()
def mempool_get_data(args):
    System.mempool_get_data()


@systemapicommand()
def ledger_get_latest_proof(args):
    System.ledger_get_latest_proof()


@systemapicommand()
def ledger_get_latest_epoch_proof(args):
    System.ledger_get_latest_epoch_proof()


@systemapicommand()
def radix_engine_get_configuration(args):
    System.radix_engine_get_configuration()


@systemapicommand()
def radix_engine_get_data(args):
    System.radix_engine_get_data()


@systemapicommand()
def sync_get_configuration(args):
    System.sync_get_configuration()


@systemapicommand()
def sync_get_data(args):
    System.sync_get_data()


@systemapicommand()
def networking_get_configuration(args):
    System.networking_get_configuration()


@systemapicommand()
def networking_get_peers(args):
    System.networking_get_peers()


@systemapicommand()
def networking_get_data(args):
    System.networking_get_data()


@systemapicommand()
def checkpoints_get_checkpoints(args):
    System.checkpoints_get_checkpoints()


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


def handle_validation():
    args = validationcli.parse_args(sys.argv[3:])
    if args.validationcommand is None:
        validationcli.print_help()
    else:
        args.func(args)


def handle_account():
    args = accountcli.parse_args(sys.argv[3:])
    if args.accountcommand is None:
        accountcli.print_help()
    else:
        args.func(args)


def handle_systemapi():
    args = systemapicli.parse_args(sys.argv[3:])
    if args.systemapicommand is None:
        systemapicli.print_help()
    else:
        args.func(args)


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
        apicli_args = apicli.parse_args(sys.argv[2:3])
        if apicli_args.apicommand is None:
            apicli.print_help()
        else:
            if apicli_args.apicommand == "validation":
                handle_validation()
            elif apicli_args.apicommand == "account":
                handle_account()
            elif apicli_args.apicommand == "health":
                RestApi.get_health()
            elif apicli_args.apicommand == "version":
                RestApi.get_version()
            elif apicli_args.apicommand == "universe":
                RestApi.get_universe()
            elif apicli_args.apicommand == "metrics":
                RestApi.get_metrics()
            elif apicli_args.apicommand == "system":
                handle_systemapi()
            else:
                print(f"Invalid api command {apicli_args.apicommand}")

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
