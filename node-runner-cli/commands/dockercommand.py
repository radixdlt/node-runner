from argparse import ArgumentParser

import yaml
from commands.subcommand import get_decorator, argument
from config.DockerConfig import DockerConfig
from github.github import latest_release
from setup import Docker, Base
from utils.utils import Helpers, run_shell_command
from deepdiff import DeepDiff
from pathlib import Path
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
def config(args):
    release = latest_release()

    if args.nodetype == "archivenode":
        Helpers.archivenode_deprecate_message()

    config = DockerConfig(release)
    config.set_node_type(args.nodetype)
    config.set_composefile_url()
    config.set_keydetails()
    config.set_core_release(release)
    config.set_data_directory()
    config.set_network_id()
    config.set_enable_transaction(args.enabletransactions)
    config.set_trusted_node(args.trustednode)
    config.set_existing_docker_compose_file()
    config_to_dump = {"core-node": dict(config.core_node_settings)}
    print(f"Yaml of config \n{yaml.dump(config_to_dump)}")
    config_file = f"{Path.home()}/config.yaml"

    def represent_none(self, _):
        return self.represent_scalar('tag:yaml.org,2002:null', '')

    yaml.add_representer(type(None), represent_none)

    with open(config_file, 'w') as f:
        yaml.dump(config_to_dump, f, default_flow_style=False, explicit_start=True, allow_unicode=True)


@dockercommand([
    argument("-f", "--configfile", required=True,
             help="Path to config file",
             action="store")
])
def setup(args):
    release = latest_release()
    docker_config = DockerConfig(release)
    docker_config.loadConfig(args.configfile)

    composefile_yaml = Docker.setup_compose_file(docker_config)

    existing_yaml = Helpers.yaml_as_dict(f"{docker_config.core_node_settings.existing_docker_compose}")
    print(dict(DeepDiff(existing_yaml, composefile_yaml,
                        ignore_order=True))
          )
    update_compose_file = input("\nOkay to update the file [Y/n]?:")
    if Helpers.check_Yes(update_compose_file):
        Docker.save_compose_file(docker_config, composefile_yaml)
    compose_file_name = docker_config.core_node_settings.existing_docker_compose.rsplit('/', 1)[-1]

    run_shell_command(f"cat {docker_config.core_node_settings.existing_docker_compose}", shell=True)
    should_start = input("\nOkay to start the node [Y/n]?:")
    if Helpers.check_Yes(should_start):
        Docker.run_docker_compose_up(docker_config.core_node_settings.keydetails.keystore_password, compose_file_name,
                                     docker_config.core_node_settings.trusted_node)
        # print(f"""
        #     ---------------------------------------------------------------
        #     Bring up node by updating the file {compose_file_name}
        #     You can do it through cli using below command
        #         radixnode docker stop  -f {compose_file_name}
        #         radixnode docker start -f {compose_file_name} -t {args.trustednode}
        #     ----------------------------------------------------------------
        #     """)


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
