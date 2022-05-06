#!/usr/bin/env python
import os
import os.path
import sys
from argparse import ArgumentParser

import urllib3

from api.DefaultApiHelper import DefaultApiHelper
from commands.authcommand import authcli
from commands.coreapi import handle_core
from commands.dockercommand import dockercli
from commands.key import keycli
from commands.monitoring import monitoringcli
from commands.systemapi import handle_systemapi
from commands.systemdcommand import systemdcli
from env_vars import DISABLE_VERSION_CHECK
from github.github import latest_release
from setup import Base
from utils.utils import Helpers, cli_version

urllib3.disable_warnings()

cli = ArgumentParser()
cli.add_argument('subcommand', help='Subcommand to run',
                 choices=["docker", "systemd", "api", "monitoring", "version", "optimise-node", "auth", "key"])

apicli = ArgumentParser(
    description='API commands')
api_parser = apicli.add_argument(dest="apicommand",
                                 choices=["system", "core"])

cwd = os.getcwd()


@corecommand()
def signal_candidate_fork_readiness(args):
    core_api_helper = CoreApiHelper(False)
    health = DefaultApiHelper(False).health()
    if health['fork_vote_status'] == 'VOTE_REQUIRED':
        candidate_fork_name = core_api_helper.engine_configuration()["forks"][-1]['name']
        print(
            f"{bcolors.WARNING}NOTICE: Because the validator is running software with a candidate fork ({candidate_fork_name}{bcolors.WARNING}), " +
            "by performing this action, the validator will signal the readiness to run this fork onto the ledger.\n" +
            f"If you later choose to downgrade the software to a version that no longer includes this fork configuration, you should manually retract your readiness signal by using the retract-candidate-fork-readiness-signal subcommand.{bcolors.ENDC}"
        )
        should_vote = input(f"Do you want to signal the readiness for {core_api_helper.engine_configuration().forks[-1]['name']} now? [Y/n]{bcolors.ENDC}")
        if Helpers.check_Yes(should_vote): core_api_helper.vote(print_response=True)
    else:
        print(f"{bcolors.WARNING}There's no need to signal the readiness for any candidate fork.{bcolors.ENDC}")


@corecommand()
def retract_candidate_fork_readiness_signal(args):
    core_api_helper = CoreApiHelper(False)
    should_vote = input(f"This action will retract your candidate fork readiness signal (if there was one), continue? [Y/n]{bcolors.ENDC}")
    if Helpers.check_Yes(should_vote): core_api_helper.withdraw_vote(print_response=True)


def print_cli_version():
    print(f"Cli - Version : {cli_version()}")


@dockercommand([

    argument("-n", "--nodetype", required=True, default="fullnode", help="Type of node fullnode or archivenode",
             action="store", choices=["fullnode", "archivenode"]),
    argument("-t", "--trustednode", required=True,
             help="Trusted node on radix network. Example format: radix//brn1q0mgwag0g9f0sv9fz396mw9rgdall@10.1.2.3",
             action="store"),
    argument("-u", "--update", help="Update the node to new version of composefile", action="store_false"),
    argument("-ts", "--enabletransactions", help="Enable transaction stream api", action="store_true"),
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
    Docker.setup_compose_file(composefileurl, file_location, args.enabletransactions)

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
    argument("-ts", "--enabletransactions", help="Enable transaction stream api", action="store_true"),
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
                                 node_type=args.nodetype, transactions_enable=args.enabletransactions)

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



@corecommand()
def update_validator_config(args):
    health = DefaultApiHelper(verify_ssl=False).check_health()
    core_api_helper = CoreApiHelper(verify_ssl=False)

    key_list_response: KeyListResponse = core_api_helper.key_list()

    validator_info: EntityResponse = core_api_helper.entity(
        key_list_response.public_keys[0].identifiers.validator_entity_identifier)

    actions = []
    actions = ValidatorConfig.registration(actions, validator_info, health)
    actions = ValidatorConfig.validator_metadata(actions, validator_info, health)
    actions = ValidatorConfig.add_validation_fee(actions, validator_info)
    actions = ValidatorConfig.setup_update_delegation(actions, validator_info)
    actions = ValidatorConfig.add_change_ownerid(actions, validator_info)
    build_response: ConstructionBuildResponse = core_api_helper.construction_build(actions, ask_user=True)
    if build_response:
        signed_transaction: KeySignResponse = core_api_helper.key_sign(build_response.unsigned_transaction)
        core_api_helper.construction_submit(signed_transaction.signed_transaction, print_response=True)

    if health['fork_vote_status'] == 'VOTE_REQUIRED':
        print("\n------Candidate fork detected------")
        engine_configuration = core_api_helper.engine_configuration()
        print_vote_and_fork_info(health, engine_configuration)
        should_vote = input(f"Do you want to signal the readiness for {core_api_helper.engine_configuration().forks[-1]['name']} now? [Y/n]{bcolors.ENDC}")
        if Helpers.check_Yes(should_vote): core_api_helper.vote(print_response=True)



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
    elif args.subcommand == "key":
        keycli_args = keycli.parse_args(sys.argv[2:])
        if keycli_args.keycommand is None:
            keycli.print_help()
        else:
            keycli_args.func(keycli_args)
    elif args.subcommand == "version":
        print_cli_version()
    elif args.subcommand == "optimise-node":
        optimise_node()
    else:
        print(f"Invalid subcommand {args.subcommand}")
