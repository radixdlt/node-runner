from argparse import ArgumentParser

from commands.subcommand import get_decorator, argument
from setup import Docker, SystemD

authcli = ArgumentParser(
    description='API command')
auth_parser = authcli.add_subparsers(dest="authcommand")


def authcommand(args=[], parent=auth_parser):
    return get_decorator(args, parent)


@authcommand(
    [
        argument("-m", "--setupmode", required=True, help="Setup type whether it is DOCKER or SYSTEMD",
                 choices=["DOCKER", "SYSTEMD"], action="store"),
        argument("-u", "--username", default="admin", help="Name of admin user", action="store")
    ])
def set_admin_password(args):
    set_auth(args, usertype="admin")


@authcommand(
    [
        argument("-m", "--setupmode", required=True, help="Setup type whether it is DOCKER or SYSTEMD",
                 choices=["DOCKER", "SYSTEMD"], action="store"),
        argument("-u", "--username", default="metrics", help="Name of metrics user", action="store")
    ])
def set_metrics_password(args):
    set_auth(args, usertype="metrics")


@authcommand(
    [
        argument("-m", "--setupmode", required=True, help="Setup type whether it is DOCKER or SYSTEMD",
                 choices=["DOCKER", "SYSTEMD"], action="store"),
        argument("-u", "--username", default="superadmin", help="Name of metrics user", action="store")
    ])
def set_superadmin_password(args):
    set_auth(args, usertype="superadmin")


def set_auth(args, usertype):
    if args.setupmode == "DOCKER":
        Docker.setup_nginx_Password(usertype, args.username)
    elif args.setupmode == "SYSTEMD":
        SystemD.checkUser()
        SystemD.install_nginx()
        SystemD.setup_nginx_password("/etc/nginx/secrets", usertype, args.username)
    else:
        print("Invalid setupmode specified. It should be either DOCKER or SYSTEMD.")
