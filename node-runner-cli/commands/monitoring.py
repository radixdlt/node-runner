from pathlib import Path

import sys
from argparse import ArgumentParser

import yaml

from commands.subcommand import get_decorator, argument
from config.BaseConfig import SetupMode
from config.MonitoringConfig import MonitoringSettings
from monitoring import Monitoring
from utils.Prompts import Prompts
from utils.utils import Helpers, bcolors

monitoringcli = ArgumentParser(
    description='API command')
monitoring_parser = monitoringcli.add_subparsers(dest="monitoringcommand")


def monitoringcommand(args=[], parent=monitoring_parser):
    return get_decorator(args, parent)


def read_monitoring_config(args):
    yaml.add_representer(type(None), Helpers.represent_none)
    with open(args.monitoringconfigfile, 'r') as file:
        all_config = yaml.safe_load(file)
    return all_config


@monitoringcommand([
    argument("-s", "--setupmode", nargs="+",
             help="""Quick setup with assumed defaults. It supports three quick setup mode and a detailed setup mode.
              \n\nMONITOR_CORE: Use this value to monitor Core using defaults which assume core is run on same machine
               as monitoring.
              \n\nMONITOR_GATEWAY: Use this value to monitor GATEWAY using defaults which assume network gateway is run on same machine.
              \n\nDETAILED: Default value if not provided. This mode takes your through series of questions.
              """,
             choices=["MONITOR_CORE", "MONITOR_GATEWAY", "DETAILED"], default="DETAILED", action="store"),
    argument("-cm", "--coremetricspassword",
             help="Password for core metrics basic auth user",
             action="store",
             default=""),
    argument("-gm", "--gatewayapimetricspassword",
             help="Password for gateway api metrics basic auth user",
             action="store",
             default=""),
    argument("-am", "--aggregatormetricspassword",
             help="Password for aggregator metrics basic auth user",
             action="store",
             default=""),
    argument("-d", "--monitoringconfigdir",
             help="Path to monitoring directory where config file will stored",
             action="store",
             default=f"{Helpers.get_default_monitoring_config_dir()}")
])
def config(args):
    setupmode = SetupMode.instance()
    setupmode.mode = args.setupmode
    coremetricspassword = args.coremetricspassword if args.coremetricspassword != "" else None
    gatewayapimetricspassword = args.gatewayapimetricspassword if args.gatewayapimetricspassword != "" else None
    aggregatormetricspassword = args.aggregatormetricspassword if args.aggregatormetricspassword != "" else None

    if "DETAILED" in setupmode.mode and len(setupmode.mode) > 1:
        print(f"{bcolors.FAIL}You cannot have DETAILED option with other options together."
              f"\nDETAILED option goes through asking each and every question that to customize setup. "
              f"Hence cannot be clubbed together with options"
              f"{bcolors.ENDC}")
        sys.exit()

    config_file = f"{args.monitoringconfigdir}/monitoring_config.yaml"
    Path(args.monitoringconfigdir).mkdir(parents=True, exist_ok=True)
    Helpers.section_headline("MONITORING CONFIG FILE")
    print(
        "\nCreating config file using the answers from the questions that would be asked in next steps."
        f"\nLocation of the config file: {bcolors.OKBLUE}{config_file}{bcolors.ENDC}")
    monitoring_config: MonitoringSettings = MonitoringSettings({})

    config_to_dump = {"common_config": dict(monitoring_config.common_settings)}

    if "MONITOR_CORE" in setupmode.mode:
        monitoring_config.configure_core_target(coremetricspassword)
        config_to_dump["monitor_core"] = dict(monitoring_config.core_prometheus_settings)
    if "MONITOR_GATEWAY" in setupmode.mode:
        monitoring_config.configure_aggregator_target(aggregatormetricspassword)
        monitoring_config.configure_gateway_api_target(gatewayapimetricspassword)

        config_to_dump["monitor_aggregator"] = dict(monitoring_config.aggregator_prometheus_settings)
        config_to_dump["monitor_gateway_api"] = dict(monitoring_config.gateway_api_prometheus_settings)
    if "DETAILED" in setupmode.mode:
        if Prompts.check_for_monitoring_core():
            monitoring_config.configure_core_target(coremetricspassword)
            config_to_dump["monitor_core"] = dict(monitoring_config.core_prometheus_settings)
        if Prompts.check_for_monitoring_gateway():
            monitoring_config.configure_aggregator_target(aggregatormetricspassword)
            monitoring_config.configure_gateway_api_target(gatewayapimetricspassword)
            config_to_dump["monitor_aggregator"] = dict(monitoring_config.aggregator_prometheus_settings)
            config_to_dump["monitor_gateway_api"] = dict(monitoring_config.gateway_api_prometheus_settings)

    yaml.add_representer(type(None), Helpers.represent_none)
    Helpers.section_headline("CONFIG is Generated as below")
    print(f"\n{yaml.dump(config_to_dump)}"
          f"\n\n Saving to file {config_file} ")

    with open(config_file, 'w') as f:
        yaml.dump(config_to_dump, f, default_flow_style=False, explicit_start=True, allow_unicode=True)


@monitoringcommand(
    [
        argument("-f", "--monitoringconfigfile", required=True,
                 help=f"Path to config file. Default is '{Helpers.get_default_monitoring_config_dir()}/monitoring_config.yaml'",
                 action="store", default=f"{Helpers.get_default_monitoring_config_dir()}/monitoring_config.yaml"),
    ])
def setup(args):
    monitor_url_dir = f'https://raw.githubusercontent.com/radixdlt/node-runner/{Helpers.cli_version()}/monitoring'
    print(f"Downloading artifacts from {monitor_url_dir}\n==")

    all_config = read_monitoring_config(args)

    monitoring_config_dir = all_config["common_config"]["config_dir"]
    Monitoring.template_prometheus_yml(all_config)
    Monitoring.template_datasource(monitoring_config_dir)
    Monitoring.template_dashboards(["dashboard.yml", "sample-node-dashboard.json", "network-gateway-dashboard.json"],monitoring_config_dir)

    Monitoring.template_monitoring_containers(monitoring_config_dir)
    Monitoring.setup_external_volumes()
    monitoring_file_location = f"{monitoring_config_dir}/node-monitoring.yml"
    Monitoring.stop_monitoring(monitoring_file_location, remove_volumes=False)
    Monitoring.start_monitoring(monitoring_file_location)


@monitoringcommand(
    [
        argument("-f", "--monitoringconfigfile", required=True,
                 help=f"Path to config file. Default is '{Helpers.get_default_monitoring_config_dir()}/monitoring_config.yaml'",
                 action="store", default=f"{Helpers.get_default_monitoring_config_dir()}/monitoring_config.yaml"),
    ]
)
def start(args):
    all_config = read_monitoring_config(args)
    monitoring_config_dir = all_config["common_config"]["config_dir"]

    monitoring_file_location = f"{monitoring_config_dir}/node-monitoring.yml"
    Monitoring.stop_monitoring(monitoring_file_location, remove_volumes=False)
    Monitoring.start_monitoring(monitoring_file_location)


@monitoringcommand([
    argument("-f", "--monitoringconfigfile", required=True,
             help=f"Path to config file. Default is '{Helpers.get_default_monitoring_config_dir()}/monitoring_config.yaml'",
             action="store", default=f"{Helpers.get_default_monitoring_config_dir()}/monitoring_config.yaml"),
    argument("-v", "--removevolumes", help="Remove the volumes ", action="store_true")])
def stop(args):
    all_config = read_monitoring_config(args)
    monitoring_config_dir = all_config["common_config"]["config_dir"]
    monitoring_file_location = f"{monitoring_config_dir}/node-monitoring.yml"
    Monitoring.stop_monitoring(monitoring_file_location, args.removevolumes)
