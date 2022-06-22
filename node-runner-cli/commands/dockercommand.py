import sys
from argparse import ArgumentParser
from argparse import RawTextHelpFormatter
from pathlib import Path

import yaml
from deepdiff import DeepDiff

from commands.subcommand import get_decorator, argument
from config.BaseConfig import SetupMode
from config.DockerConfig import DockerConfig, CoreDockerSettings
from config.GatewayDockerConfig import GatewayDockerSettings
from config.Renderer import Renderer
from github.github import latest_release
from setup import Docker, Base
from utils.Prompts import Prompts
from utils.utils import Helpers, run_shell_command, bcolors

dockercli = ArgumentParser(
    description='Docker commands', formatter_class=RawTextHelpFormatter)
docker_parser = dockercli.add_subparsers(dest="dockercommand")


def dockercommand(dockercommand_args=[], parent=docker_parser):
    return get_decorator(dockercommand_args, parent)


@dockercommand([
    argument("-t", "--trustednode",
             required=True,
             help="Trusted node on radix network. Example format: radix//brn1q0mgwag0g9f0sv9fz396mw9rgdall@10.1.2.3",
             action="store"),
    argument("-d", "--configdir",
             help="Path to node-config directory where config file will stored",
             action="store",
             default=f"{Helpers.get_default_node_config_dir()}"),
    argument("-n", "--networkid",
             help="Network id of network you want to connect.For stokenet it is 2 and for mainnet it is 1."
                  "If not provided you will be prompted to enter a value ",
             action="store",
             type=int,
             default=0),
    argument("-p", "--postgrespassword",
             help="Password for the postgres user. This is used for Gateway setup",
             action="store",
             default=""),
    argument("-k", "--keystorepassword",
             help="Password for the keystore file",
             action="store",
             default=""),
    argument("-nk", "--newkeystore", help="Set this to true to create a new store without any prompts using location"
                                          " defined in argument configdir", action="store_true"),
    argument("-xc", "--disablenginxforcore", help="Set this to disable to nginx for core",
             action="store", default="", choices=["true", "false"]),
    argument("-xg", "--disablenginxforgateway", help="Set this to disable to nginx for gateway",
             action="store", default="", choices=["true", "false"]),

    argument("-s", "--setupmode", nargs="+",
             help="""Quick config mode with assumed defaults. It supports two quick modes and a detailed config mode.
                  \n\nCORE: Use this value to setup CORE using defaults.
                  \n\nGATEWAY: Use this value to setup GATEWAY using defaults.
                  \n\nDETAILED: Default value if not provided. This mode takes your through series of questions.
                  """,
             choices=["CORE", "GATEWAY", "DETAILED"], default="DETAILED", action="store")
])
def config(args):
    setupmode = SetupMode.instance()
    setupmode.mode = args.setupmode
    keystore_password = args.keystorepassword if args.keystorepassword != "" else None
    postgrespassword = args.postgrespassword if args.postgrespassword != "" else None
    nginx_on_gateway = args.disablenginxforgateway if args.disablenginxforgateway != "" else None
    nginx_on_core = args.disablenginxforcore if args.disablenginxforcore != "" else None

    new_keystore = args.newkeystore

    if "DETAILED" in setupmode.mode and len(setupmode.mode) > 1:
        print(f"{bcolors.FAIL}You cannot have DETAILED option with other options together."
              f"\nDETAILED option goes through asking each and every question that to customize setup. "
              f"Hence cannot be clubbed together with options"
              f"{bcolors.ENDC}")
        sys.exit()
    release = latest_release()

    Path(f"{Helpers.get_default_node_config_dir()}").mkdir(parents=True, exist_ok=True)
    config_file = f"{args.configdir}/config.yaml"

    configuration = DockerConfig(release)
    Helpers.section_headline("CONFIG FILE")
    print(
        "\nCreating config file using the answers from the questions that would be asked in next steps."
        f"\nLocation of the config file: {bcolors.OKBLUE}{config_file}{bcolors.ENDC}")

    configuration.common_settings.ask_network_id(args.networkid)

    config_to_dump = {}

    if "CORE" in setupmode.mode:
        quick_node_settings: CoreDockerSettings = CoreDockerSettings({}).create_config(release, args.trustednode,
                                                                                       keystore_password, new_keystore)
        configuration.core_node_settings = quick_node_settings
        configuration.common_settings.ask_enable_nginx_for_core(nginx_on_core)
        config_to_dump["core_node"] = dict(configuration.core_node_settings)

    if "GATEWAY" in setupmode.mode:
        quick_gateway_settings: GatewayDockerSettings = GatewayDockerSettings({}).create_config(postgrespassword)

        configuration.gateway_settings = quick_gateway_settings
        configuration.common_settings.ask_enable_nginx_for_gateway(nginx_on_gateway)
        config_to_dump["gateway"] = dict(configuration.gateway_settings)

    if "DETAILED" in setupmode.mode:
        run_fullnode = Prompts.check_for_fullnode()
        if run_fullnode:
            detailed_node_settings = CoreDockerSettings({}).create_config(release, args.trustednode, keystore_password,
                                                                          new_keystore)
            configuration.core_node_settings = detailed_node_settings
            configuration.common_settings.ask_enable_nginx_for_core(nginx_on_core)
            config_to_dump["core_node"] = dict(configuration.core_node_settings)
        run_gateway = Prompts.check_for_gateway()
        if run_gateway:
            detailed_gateway_settings: GatewayDockerSettings = GatewayDockerSettings({}).create_config(
                postgrespassword)
            configuration.gateway_settings = detailed_gateway_settings
            configuration.common_settings.ask_enable_nginx_for_gateway(nginx_on_gateway)
            config_to_dump["gateway"] = dict(configuration.gateway_settings)
    if configuration.common_settings.check_nginx_required():
        configuration.common_settings.ask_nginx_release()
    else:
        configuration.common_settings.nginx_settings = None

    config_to_dump["common_config"] = dict(configuration.common_settings)

    yaml.add_representer(type(None), Helpers.represent_none)
    Helpers.section_headline("CONFIG is Generated as below")
    print(f"\n{yaml.dump(config_to_dump)}"
          f"\n\n Saving to file {config_file} ")

    with open(config_file, 'w') as f:
        yaml.dump(config_to_dump, f, default_flow_style=False, explicit_start=True, allow_unicode=True)


@dockercommand([
    argument("-f", "--configfile",
             help="Path to config file",
             default=f"{Helpers.get_default_node_config_dir()}/config.yaml",
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
    render_template = Renderer().load_file_based_template("radix-fullnode-compose.yml.j2").render(all_config).to_yaml()

    old_compose_file = Helpers.yaml_as_dict(f"{all_config['core_node']['existing_docker_compose']}")
    print(dict(DeepDiff(old_compose_file, render_template)))

    to_update = ""
    if autoapprove:
        print("In Auto mode - Updating file as suggested in above changes")
    else:
        to_update = input("\nOkay to update the file [Y/n]?:")
    if Helpers.check_Yes(to_update) or autoapprove:
        Docker.save_compose_file(docker_config.core_node_settings.existing_docker_compose, render_template)

    run_shell_command(f"cat {docker_config.core_node_settings.existing_docker_compose}", shell=True)
    should_start = ""
    if autoapprove:
        print("In Auto mode -  Updating the node as per above contents of docker file")
    else:
        should_start = input("\nOkay to start the containers [Y/n]?:")
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
