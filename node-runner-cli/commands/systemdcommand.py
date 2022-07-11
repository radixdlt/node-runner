import os
import sys
from argparse import ArgumentParser

from commands.subcommand import get_decorator, argument
from env_vars import NODE_BINARY_OVERIDE, NGINX_BINARY_OVERIDE
from github.github import latest_release
from setup import SystemD, Base
from utils.utils import Helpers

systemdcli = ArgumentParser(
    description='Subcommand to help setup CORE using systemD service',
    usage="radixnode systemd ")
systemd_parser = systemdcli.add_subparsers(dest="systemdcommand")


def systemdcommand(systemdcommand_args=[], parent=systemd_parser):
    return get_decorator(systemdcommand_args, parent)

@systemdcommand([
    argument("-r", "--release",
             help="Version of node software to install",
             action="store"),
    argument("-x", "--nginxrelease", help="Version of radixdlt nginx release ", action="store"),
    argument("-t", "--trustednode", required=True, help="Trusted node on radix network", action="store"),
    argument("-n", "--nodetype", required=True, default="fullnode", help="Type of node fullnode or archivenode",
             action="store", choices=["fullnode", "archivenode"]),
    argument("-i", "--hostip", required=True, help="Static Public IP of the node", action="store"),
    argument("-ts", "--enabletransactions", help="Enable transaction stream api", action="store_true"),
    argument("-u", "--update", help="Update the node to new version of node", action="store_false"),

])
def install(args):
    """This sets up the systemd service for the core node."""

    if not args.release:
        release = latest_release()
    else:
        release = args.release

    if not args.nginxrelease:
        nginx_release = latest_release("radixdlt/radixdlt-nginx")
    else:
        nginx_release = args.nginxrelease

    if args.nodetype == "archivenode":
        Helpers.archivenode_deprecate_message()
    node_type_name = 'fullnode'
    node_dir = '/etc/radixdlt/node'
    nginx_dir = '/etc/nginx'
    nginx_secrets_dir = f"{nginx_dir}/secrets"
    node_secrets_dir = f"{node_dir}/secrets"
    node_binary_url = os.getenv(NODE_BINARY_OVERIDE,
                                f"https://github.com/radixdlt/radixdlt/releases/download/{release}/radixdlt-dist-{release}.zip")

    # TODO add method to fetch latest nginx release
    nginx_config_url = os.getenv(NGINX_BINARY_OVERIDE,
                                 f"https://github.com/radixdlt/radixdlt-nginx/releases/download/{nginx_release}/radixdlt-nginx-{node_type_name}-conf.zip")
    # TODO AutoApprove
    continue_setup = input(
        f"Going to setup node type {args.nodetype} for version {release} from location {node_binary_url} and {nginx_config_url}. \n Do you want to continue Y/n:")

    if not Helpers.check_Yes(continue_setup):
        print(" Quitting ....")
        sys.exit()

    backup_time = Helpers.get_current_date_time()
    SystemD.checkUser()
    keystore_password, keyfile_location = SystemD.generatekey(node_secrets_dir, keygen_tag=release)

    SystemD.backup_file(node_secrets_dir, "environment", backup_time)
    SystemD.set_environment_variables(keystore_password, node_secrets_dir)

    SystemD.backup_file(node_dir, f"default.config", backup_time)

    SystemD.setup_default_config(trustednode=args.trustednode, hostip=args.hostip, node_dir=node_dir,
                                 node_type=args.nodetype, transactions_enable=args.enabletransactions)

    node_version = node_binary_url.rsplit('/', 2)[-2]
    SystemD.backup_file("/etc/systemd/system", "radixdlt-node.service", backup_time)
    SystemD.setup_service_file(node_version, node_dir=node_dir, node_secrets_path=node_secrets_dir)

    SystemD.download_binaries(node_binary_url, node_dir=node_dir, node_version=node_version)

    SystemD.backup_file("/lib/systemd/system", "nginx.service", backup_time)

    nginx_configured = SystemD.setup_nginx_config(nginx_config_location_Url=nginx_config_url,
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
    """This stops the CORE node systemd service."""
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
    """This restarts the CORE node systemd service."""
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


@systemdcommand([])
def dependencies(args):
    """
    This commands installs all necessary software on the Virtual Machine(VM).
    Run this command on fresh VM or on a existing VM  as the command is tested to be idempotent
    """
    Base.dependencies()
    SystemD.install_java()
    SystemD.setup_user()
    SystemD.make_etc_directory()
    SystemD.make_data_directory()
    SystemD.create_service_user_password()
    SystemD.create_initial_service_file()
    SystemD.sudoers_instructions()
