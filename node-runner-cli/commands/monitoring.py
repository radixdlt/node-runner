import sys
from argparse import ArgumentParser

from commands.subcommand import get_decorator, argument
from monitoring import Monitoring
from utils.utils import Helpers

monitoringcli = ArgumentParser(
    description='API command')
monitoring_parser = monitoringcli.add_subparsers(dest="monitoringcommand")


def monitoringcommand(args=[], parent=monitoring_parser):
    return get_decorator(args, parent)


@monitoringcommand(
    [argument("-m", "--setupmode", default="QUICK_SETUP_MODE",
              help="Setup type whether it is QUICK_SETUP_MODE or PRODUCTION_MODE",
              action="store")])
def setup(args):
    if args.setupmode == "QUICK_SETUP_MODE":
        monitor_url_dir = f'https://raw.githubusercontent.com/radixdlt/node-runner/{Helpers.cli_version()}/monitoring'
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
