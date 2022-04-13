#!/usr/bin/env python
import os
import os.path
import sys
from argparse import ArgumentParser

import system_client as system_api
import urllib3
from core_client.model.construction_build_response import ConstructionBuildResponse
from core_client.model.construction_submit_response import ConstructionSubmitResponse
from core_client.model.entity_identifier import EntityIdentifier
from core_client.model.entity_response import EntityResponse
from core_client.model.key_list_response import KeyListResponse
from core_client.model.key_sign_response import KeySignResponse
from core_client.model.sub_entity import SubEntity
from core_client.model.sub_entity_metadata import SubEntityMetadata
from api.Api import API
from api.CoreApiHelper import CoreApiHelper
from api.DefaultApiHelper import DefaultApiHelper
from api.ValidatorConfig import ValidatorConfig
from env_vars import COMPOSE_FILE_OVERIDE, NODE_BINARY_OVERIDE, NGINX_BINARY_OVERIDE, DISABLE_VERSION_CHECK
from github.github import latest_release
from monitoring import Monitoring
from setup import Base, Docker, SystemD
from utils.utils import Helpers
from utils.utils import run_shell_command
from version import __version__

urllib3.disable_warnings()

cli = ArgumentParser()
cli.add_argument('subcommand', help='Subcommand to run',
                 choices=["docker", "systemd", "api", "monitoring", "version", "optimise-node", "auth"])

apicli = ArgumentParser(
    description='API commands')
api_parser = apicli.add_argument(dest="apicommand",
                                 choices=["system", "core"])

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


# Setup core parser
corecli = ArgumentParser(
    description='Core Api comands')
core_parser = corecli.add_subparsers(dest="corecommand")


def corecommand(args=[], parent=core_parser):
    return get_decorator(args, parent)


def handle_core():
    args = corecli.parse_args(sys.argv[3:])
    if args.corecommand is None:
        corecli.print_help()
    else:
        args.func(args)


@corecommand()
def network_configuration(args):
    core_api_helper = CoreApiHelper(False)
    core_api_helper.network_configuration(True)


@corecommand()
def network_status(args):
    core_api_helper = CoreApiHelper(False)
    core_api_helper.network_status(True)


@corecommand([
    argument("-v", "--validator",
             help="Display entity details of validator address",
             action="store_true"),
    argument("-a", "--address",
             help="Display entity details of validator account address",
             action="store_true"),
    argument("-p", "--p2p",
             help="Display entity details of validator peer to peer address",
             action="store_true"),
    argument("-sy", "--subEntitySystem",
             help="Display entity details of validator address along with sub entity system",
             action="store_true"),
    argument("-ss", "--subPreparedStake",
             help="Display entity details of validator account address along with sub entity  prepared_stake",
             action="store_true"),
    argument("-su", "--subPreparedUnStake",
             help="Display entity details of validator account address along with sub entity  prepared_unstake",
             action="store_true"),
    argument("-se", "--subExitingStake",
             help="Display entity details of validator account address along with sub entity exiting_stake",
             action="store_true")
])
def entity(args):
    core_api_helper = CoreApiHelper(False)
    key_list_response: KeyListResponse = core_api_helper.key_list(False)
    validator_address = key_list_response.public_keys[0].identifiers.validator_entity_identifier.address
    account_address = key_list_response.public_keys[0].identifiers.account_entity_identifier.address
    if args.validator:
        if args.subEntitySystem:
            subEntity = SubEntity(address=str("system"))
            entityIdentifier = EntityIdentifier(
                address=validator_address,
                sub_entity=subEntity
            )
        else:
            entityIdentifier = EntityIdentifier(
                address=validator_address,
            )

        core_api_helper.entity(entityIdentifier, True)
        sys.exit()
    if args.address:
        if args.subPreparedStake:
            metadata = SubEntityMetadata(validator=validator_address)
            subEntity = SubEntity(address=str("prepared_stake"), metadata=metadata)
            entityIdentifier = EntityIdentifier(
                address=account_address,
                sub_entity=subEntity
            )
        if args.subPreparedUnStake:
            metadata = SubEntityMetadata(validator=validator_address)
            subEntity = SubEntity(address=str("prepared_unstake"), metadata=metadata)
            entityIdentifier = EntityIdentifier(
                address=account_address,
                sub_entity=subEntity
            )
        if args.subExitingStake:
            metadata = SubEntityMetadata(validator=validator_address)
            subEntity = SubEntity(address=str("exiting_stake"), metadata=metadata)
            entityIdentifier = EntityIdentifier(
                address=account_address,
                sub_entity=subEntity
            )
        else:
            entityIdentifier = EntityIdentifier(
                address=account_address,
            )
        core_api_helper.entity(entityIdentifier, True)
        sys.exit()
    if args.p2p:
        core_api_helper.entity(key_list_response.public_keys[0].identifiers.p2p_node, True)
        sys.exit()


@corecommand()
def key_list(args):
    core_api_helper = CoreApiHelper(False)
    core_api_helper.key_list(True)


@corecommand()
def mempool(args):
    core_api_helper = CoreApiHelper(False)
    core_api_helper.mempool(True)


@corecommand([
    argument("-t", "--transactionId", required=True,
             help="transaction Id to be searched on mempool",
             action="store")
])
def mempool_transaction(args):
    core_api_helper = CoreApiHelper(False)
    core_api_helper.mempool_transaction(args.transactionId, True)


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


def print_cli_version():
    print(f"Cli - Version : {cli_version()}")


@dockercommand([

    argument("-n", "--nodetype", required=True, default="fullnode", help="Type of node fullnode or archivenode",
             action="store", choices=["fullnode", "archivenode"]),
    argument("-t", "--trustednode", required=True,
             help="Trusted node on radix network. Example format: radix//brn1q0mgwag0g9f0sv9fz396mw9rgdall@10.1.2.3",
             action="store"),
    argument("-u", "--update", help="Update the node to new version of composefile", action="store_false"),
])
def setup(args):
    release = latest_release()

    if args.nodetype == "archivenode":
        Helpers.archivenode_deprecate_message()

    composefileurl = os.getenv(COMPOSE_FILE_OVERIDE,
                               f"https://raw.githubusercontent.com/radixdlt/node-runner/{cli_version()}/node-runner-cli/release_ymls/radix-{args.nodetype}-compose.yml")
    print(f"Going to setup node type {args.nodetype} from location {composefileurl}.\n")
    # TODO autoapprove
    continue_setup = input(
        "Do you want to continue [Y/n]?:")

    if not Helpers.check_Yes(continue_setup):
        print(" Quitting ....")
        sys.exit()

    keystore_password, file_location = Base.generatekey(keyfile_path=Helpers.get_keyfile_path(), keygen_tag=release)
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
    argument("-x", "--nginxrelease", help="Version of radixdlt nginx release ", action="store"),
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
    nodebinaryUrl = os.getenv(NODE_BINARY_OVERIDE,
                              f"https://github.com/radixdlt/radixdlt/releases/download/{release}/radixdlt-dist-{release}.zip")

    # TODO add method to fetch latest nginx release
    nginxconfigUrl = os.getenv(NGINX_BINARY_OVERIDE,
                               f"https://github.com/radixdlt/radixdlt-nginx/releases/download/{nginx_release}/radixdlt-nginx-{node_type_name}-conf.zip")
    # TODO AutoApprove
    continue_setup = input(
        f"Going to setup node type {args.nodetype} for version {release} from location {nodebinaryUrl} and {nginxconfigUrl}. \n Do you want to continue Y/n:")

    if not Helpers.check_Yes(continue_setup):
        print(" Quitting ....")
        sys.exit()

    backup_time = Helpers.get_current_date_time()
    SystemD.checkUser()
    keystore_password, keyfile_location = SystemD.generatekey(node_secrets_dir, keygen_tag=release)
    trustednode_ip = Helpers.parse_trustednode(args.trustednode)

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
    release = latest_release()
    keystore_password, keyfile_location = Base.generatekey(keyfile_path=Helpers.get_keyfile_path(), keygen_tag=release)
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


@corecommand()
def update_validator_config(args):
    node_host = API.get_host_info()

    defaultApiHelper = DefaultApiHelper(verify_ssl=False)
    health = defaultApiHelper.check_health()

    core_api_helper = CoreApiHelper(verify_ssl=False)
    engine_configuration = core_api_helper.engine_configuration()
    key_list_response: KeyListResponse = core_api_helper.key_list()
    
    validator_info: EntityResponse = core_api_helper.entity(
        key_list_response.public_keys[0].identifiers.validator_entity_identifier)

    actions = []
    actions = ValidatorConfig.registration(actions, validator_info, health, engine_configuration)
    actions = ValidatorConfig.validator_metadata(actions, validator_info, health, engine_configuration)
    actions = ValidatorConfig.add_validation_fee(actions, validator_info)
    actions = ValidatorConfig.setup_update_delegation(actions, validator_info)
    actions = ValidatorConfig.add_change_ownerid(actions, validator_info)
    actions = ValidatorConfig.vote(actions, health, engine_configuration)
    actions = ValidatorConfig.withdraw_vote(actions)
    build_response: ConstructionBuildResponse = core_api_helper.construction_build(actions, ask_user=True)
    signed_transaction: KeySignResponse = core_api_helper.key_sign(build_response.unsigned_transaction)
    submitted_transaction: ConstructionSubmitResponse = core_api_helper.construction_submit(
        signed_transaction.signed_transaction, print_response=True)


@systemapicommand()
def metrics(args):
    defaultApiHelper = DefaultApiHelper(verify_ssl=False)
    defaultApiHelper.metrics()


@systemapicommand()
def version(args):
    defaultApiHelper = DefaultApiHelper(verify_ssl=False)
    defaultApiHelper.version()


@systemapicommand()
def health(args):
    defaultApiHelper = DefaultApiHelper(verify_ssl=False)
    defaultApiHelper.health(print_response=True)


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
            if apicli_args.apicommand == "metrics":
                defaultApi = DefaultApiHelper(verify_ssl=False)
                defaultApi.prometheus_metrics()
            elif apicli_args.apicommand == "system":
                handle_systemapi()
            elif apicli_args.apicommand == "core":
                handle_core()
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
        print_cli_version()
    elif args.subcommand == "optimise-node":
        optimise_node()
    else:
        print(f"Invalid subcommand {args.subcommand}")
