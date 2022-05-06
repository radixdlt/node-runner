from argparse import ArgumentParser

import yaml

from commands.subcommand import get_decorator, argument
from config.DockerConfig import DockerConfig
from github.github import latest_release
from setup import Docker, Base
from utils.utils import Helpers, run_shell_command
from deepdiff import DeepDiff

dockercli = ArgumentParser(
    description='Docker commands')
docker_parser = dockercli.add_subparsers(dest="dockercommand")


def dockercommand(dockercommand_args=[], parent=docker_parser):
    return get_decorator(dockercommand_args, parent)


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

    config = DockerConfig()
    config.set_node_type(args.nodetype)
    config.set_composefile_url()
    config.set_keydetails()
    config.set_core_release(release)
    config.set_data_directory()
    config.set_network_id()
    config.set_enable_transaction(args.enabletransactions)

    print(f"Yaml of config {yaml.dump(config.core_node_settings)}")

    composefile_yaml = Docker.setup_compose_file(config)

    print(DeepDiff(composefile_yaml, Helpers.yaml_as_dict(config.core_node_settings.existing_docker_compose),
                   ignore_order=True))
    update_compose_file = input("\nOkay to update the file [Y/n]?:")
    if Helpers.check_Yes(update_compose_file):
        Docker.save_compose_file(config, composefile_yaml)
    compose_file_name = config.core_node_settings.composefileurl.rsplit('/', 1)[-1]

    action = "update" if args.update else "start"
    print(f"About to {action} the node using docker-compose file {compose_file_name}, which is as below")
    run_shell_command(f"cat {compose_file_name}", shell=True)
    should_start = input("\nOkay to start the node [Y/n]?:")
    if Helpers.check_Yes(should_start):
        if action == "update":
            print(f"For update, bringing down the node using compose file {compose_file_name}")
            Docker.run_docker_compose_down(compose_file_name)
        Docker.run_docker_compose_up(config.core_node_settings.keydetails.keystore_password, compose_file_name,
                                     args.trustednode)
    else:
        print(f"""
            ---------------------------------------------------------------
            Bring up node by updating the file {compose_file_name}
            You can do it through cli using below command
                radixnode docker stop  -f {compose_file_name}
                radixnode docker start -f {compose_file_name} -t {args.trustednode}
            ----------------------------------------------------------------
            """)


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
