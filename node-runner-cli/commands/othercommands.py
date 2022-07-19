from argparse import ArgumentParser

from commands.subcommand import get_decorator
from setup import Base
from utils.utils import Helpers

other_command_cli = ArgumentParser(
    description='Other CLI commands')
other_command_parser = other_command_cli.add_subparsers(dest="othercommands")


def othercommands(args=[], parent=other_command_parser):
    return get_decorator(args, parent)


@othercommands()
def version(args):
    """
    Run this command td display the version of CLI been used.
    """
    print(f"Cli - Version : {Helpers.cli_version()}")


@othercommands()
def optimise_node(args):
    """
    Run this command to setup ulimits and swap size on the fresh ubuntu machine

    . Prompts asking to setup limits
    . Prompts asking to setup swap and size of swap in GB
    """
    Base.setup_node_optimisation_config(Helpers.cli_version())
