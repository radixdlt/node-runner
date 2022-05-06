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


def print_cli_version():
    print(f"Cli - Version : {Helpers.cli_version()}")


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
