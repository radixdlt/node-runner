import sys
from argparse import ArgumentParser

from api.DefaultApiHelper import DefaultApiHelper
from commands.subcommand import get_decorator

systemapicli = ArgumentParser(
    description='Subcommand to aid interaction with system api of core node',
    usage="radixnode api system ")
systemapi_parser = systemapicli.add_subparsers(dest="systemapicommand")


def handle_systemapi():
    systemcli_args = systemapicli.parse_args(sys.argv[3:])
    if systemcli_args.systemapicommand is None:
        systemapicli.print_help()
    else:
        systemcli_args.func(systemcli_args)


def systemapicommand(args=[], parent=systemapi_parser):
    return get_decorator(args, parent)


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
