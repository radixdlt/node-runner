from argparse import ArgumentParser

import yaml
from deepdiff import DeepDiff

from commands.subcommand import get_decorator, argument
from config.DockerConfig import DockerConfig
from config.Renderer import Renderer
from github.github import latest_release
from setup import Docker, Base
from utils.Prompts import Prompts
from utils.utils import Helpers, run_shell_command

dockercli = ArgumentParser(
    description='Docker commands')
docker_parser = dockercli.add_subparsers(dest="dockercommand")


def dockercommand(dockercommand_args=[], parent=docker_parser):
    return get_decorator(dockercommand_args, parent)


@dockercommand([
    argument("-t", "--trustednode",
             required=True,
             help="Trusted node on radix network. Example format: radix//brn1q0mgwag0g9f0sv9fz396mw9rgdall@10.1.2.3",
             action="store"),
    argument("-f", "--configfile",
             help="Path to config file",
             action="store",
             default=f"{Helpers.get_home_dir()}/config.yaml"),
])
def config(args):
    release = latest_release()
    configuration = DockerConfig(release)
    configuration.common_settings.ask_network_id()

    if Prompts.check_for_fullnode():
        configuration.core_node_settings.set_node_type()
        configuration.core_node_settings.set_composefile_url()
        configuration.core_node_settings.set_core_release(release)
        configuration.core_node_settings.set_trusted_node(args.trustednode)
        configuration.core_node_settings.ask_keydetails()
        configuration.core_node_settings.ask_data_directory()
        configuration.core_node_settings.ask_enable_transaction()
        configuration.core_node_settings.ask_existing_docker_compose_file()

    if Prompts.check_for_gateway():
        configuration.gateway_settings.data_aggregator.ask_core_api_node_settings()
        configuration.gateway_settings.data_aggregator.ask_postgress_settings()
        configuration.gateway_settings.data_aggregator.ask_gateway_release()
        configuration.gateway_settings.data_aggregator.ask_core_api_node_settings()
        configuration.gateway_settings.gateway_api.set_core_api_node_setings(
            configuration.gateway_settings.data_aggregator.coreApiNode)
        configuration.gateway_settings.gateway_api.set_postgress_settings(
            configuration.gateway_settings.data_aggregator.postgresSettings)

    config_to_dump = {
        "common_config": dict(configuration.common_settings),
        "core_node": dict(configuration.core_node_settings),
        "data_aggregator": dict(configuration.gateway_settings.data_aggregator),
        "gateway_api": dict(configuration.gateway_settings.gateway_api)
    }

    # TODO make this as optional parameter
    config_file = f"{Helpers.get_home_dir()}/config.yaml"

    def represent_none(self, _):
        return self.represent_scalar('tag:yaml.org,2002:null', '')

    yaml.add_representer(type(None), represent_none)
    print(f"Yaml of config \n{yaml.dump(config_to_dump)}")

    with open(config_file, 'w') as f:
        yaml.dump(config_to_dump, f, default_flow_style=False, explicit_start=True, allow_unicode=True)


@dockercommand([
    argument("-f", "--configfile", required=True,
             help="Path to config file",
             action="store"),
    argument("-a", "--autoapprove", help="Set this to true to run without any prompts", action="store_true"),
])
def setup(args):
    release = latest_release()
    autoapprove = args.autoapprove

    docker_config = DockerConfig(release)
    docker_config.loadConfig(args.configfile)

    def represent_none(self, _):
        return self.represent_scalar('tag:yaml.org,2002:null', '')

    yaml.add_representer(type(None), represent_none)

    with open(args.configfile, 'r') as file:
        all_config = yaml.safe_load(file)
    render_template = Renderer().load_file_based_template("radix-fullnode-compose.j2").render(all_config).to_yaml()

    old_compose_file = Helpers.yaml_as_dict(f"{all_config['core_node']['existing_docker_compose']}")
    print(dict(DeepDiff(old_compose_file, render_template)))

    to_update = ""
    if autoapprove:
        print("In Auto mode - Updating file as suggested in above changes")
    else:
        to_update = input("\nOkay to update the file [Y/n]?:")
    if Helpers.check_Yes(to_update) or autoapprove:
        Docker.save_compose_file(docker_config, render_template)

    run_shell_command(f"cat {docker_config.core_node_settings.existing_docker_compose}", shell=True)
    should_start = ""
    if autoapprove:
        print("In Auto mode -  Updating the node as per above contents of docker file")
    else:
        should_start = input("\nOkay to start the node [Y/n]?:")
    if Helpers.check_Yes(should_start) or autoapprove:
        Docker.run_docker_compose_up(docker_config.core_node_settings.keydetails.keystore_password,
                                     docker_config.core_node_settings.existing_docker_compose,
                                     docker_config.core_node_settings.trusted_node)


@dockercommand([
    argument("-f", "--configfile", required=True,
             help="Path to config file",
             action="store"),
])
def start(args):
    release = latest_release()
    docker_config = DockerConfig(release)
    docker_config.loadConfig(args.configfile)
    core_node_settings = docker_config.core_node_settings
    Docker.run_docker_compose_up(core_node_settings.keydetails.keystore_password,
                                 core_node_settings.existing_docker_compose,
                                 core_node_settings.trusted_node)


@dockercommand([
    argument("-f", "--configfile", required=True,
             help="Path to config file",
             action="store"),
    argument("-v", "--removevolumes", help="Remove the volumes ", action="store_true"),
])
def stop(args):
    if args.removevolumes:
        print(
            """ 
            Removing volumes including Nginx volume. Nginx password needs to be recreated again when you bring node up
            """)
    release = latest_release()
    docker_config = DockerConfig(release)
    docker_config.loadConfig(args.configfile)
    core_node_settings = docker_config.core_node_settings
    Docker.run_docker_compose_down(core_node_settings.existing_docker_compose, args.removevolumes)


@dockercommand([])
def configure(args):
    Base.install_dependecies()
    Base.add_user_docker_group()
