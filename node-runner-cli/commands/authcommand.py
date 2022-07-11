from argparse import ArgumentParser

from commands.subcommand import get_decorator, argument
from setup import Docker, SystemD

authcli = ArgumentParser(
    description='Subcommand to aid creation of nginx basic auth users',
    usage="radixnode auth "
)

auth_parser = authcli.add_subparsers(dest="authcommand")


def authcommand(args=[], parent=auth_parser):
    return get_decorator(args, parent)


@authcommand(
    [
        argument("-m", "--setupmode", required=True, help="Setup type whether it is DOCKER or SYSTEMD",
                 choices=["DOCKER", "SYSTEMD"], action="store"),
        argument("-u", "--username", default="admin", help="Name of admin user. Default value is `admin` ",
                 action="store"),
        argument("-p", "--password", default="", help="Password of admin user", action="store")

    ])
def set_admin_password(args):
    """
    This sets up admin password on nginx basic auth. Refer this link for all the paths.
    https://docs.radixdlt.com/main/node-and-gateway/port-reference.html#_endpoint_usage
    """
    password = args.password if args.password != "" else None

    set_auth(args, usertype="admin", password=password)


@authcommand(
    [
        argument("-m", "--setupmode", required=True, help="Setup type whether it is DOCKER or SYSTEMD",
                 choices=["DOCKER", "SYSTEMD"], action="store"),
        argument("-u", "--username", default="metrics", help="Name of metrics user. Default value is `metrics`",
                 action="store"),
        argument("-p", "--password", default="", help="Password of metrics user", action="store")
    ])
def set_metrics_password(args):
    """
    This sets up metrics password on nginx basic auth. Refer this link for all the paths.
    https://docs.radixdlt.com/main/node-and-gateway/port-reference.html#_endpoint_usage
    """
    password = args.password if args.password != "" else None
    set_auth(args, usertype="metrics", password=password)


@authcommand(
    [
        argument("-m", "--setupmode", required=True, help="Setup type whether it is DOCKER or SYSTEMD",
                 choices=["DOCKER", "SYSTEMD"], action="store"),
        argument("-u", "--username", default="superadmin",
                 help="Name of superadmin user. Default value is `superadmin` ", action="store"),
        argument("-p", "--password", default="", help="Password of superadmin user", action="store")
    ])
def set_superadmin_password(args):
    """
    This sets up superadmin password on nginx basic auth. Refer this link for all the paths.
    https://docs.radixdlt.com/main/node-and-gateway/port-reference.html#_endpoint_usage
    """
    password = args.password if args.password != "" else None
    set_auth(args, usertype="superadmin", password=password)


@authcommand(
    [
        argument("-m", "--setupmode", required=True, help="Setup type whether it is DOCKER or SYSTEMD",
                 choices=["DOCKER", "SYSTEMD"], action="store"),
        argument("-u", "--username", default="gateway",
                 help="Name of gateway user. Default value is `gateway` ", action="store"),
        argument("-p", "--password", default="", help="Password of gateway user", action="store")
    ])
def set_gateway_password(args):
    """
    This sets up gateway password on nginx basic auth. Refer this link for all the paths.
    https://docs.radixdlt.com/main/node-and-gateway/port-reference.html#_endpoint_usage
    """
    password = args.password if args.password != "" else None
    set_auth(args, usertype="gateway", password=password)


def set_auth(args, usertype, password=None):
    if args.setupmode == "DOCKER":
        Docker.setup_nginx_Password(usertype, args.username, password)
    elif args.setupmode == "SYSTEMD":
        SystemD.checkUser()
        SystemD.install_nginx()
        SystemD.setup_nginx_password("/etc/nginx/secrets", usertype, args.username)
    else:
        print("Invalid setupmode specified. It should be either DOCKER or SYSTEMD.")
