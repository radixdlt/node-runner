import sys

import requests
from requests.auth import HTTPBasicAuth

from api.Api import API
from utils.utils import Helpers, bcolors


class RestApi(API):
    @staticmethod
    def get_health():
        return RestApi.get_request("admin", "admin", "health")

    @staticmethod
    def get_request(usertype, username, api_path):
        node_host = API.get_host_info()
        user = Helpers.get_nginx_user(usertype=usertype, default_username=username)

        req = requests.Request('GET',
                               f"{node_host}/{api_path}",
                               auth=HTTPBasicAuth(user["name"], user["password"]))

        prepared = req.prepare()
        prepared.headers['Content-Type'] = 'application/json'
        return Helpers.send_request(prepared)

    @staticmethod
    def get_version():
        RestApi.get_request("admin", "admin", "version")

    @staticmethod
    def get_universe():
        RestApi.get_request("admin", "admin", "universe.json")

    @staticmethod
    def get_metrics():
        RestApi.get_request("metrics", "metrics", "metrics")

    @staticmethod
    def check_health():
        error = False
        Helpers.print_coloured_line("Checking status of the node\n", bcolors.BOLD)
        health = RestApi.get_health()

        if not health.ok:
            Helpers.print_coloured_line("Error retrieving health\n", bcolors.FAIL)
            sys.exit()

        if Helpers.is_json(health.content) and health.content.status != "UP":
            Helpers.print_coloured_line(
                "Node is not in sync. Rerun the command once node is completely synced",
                bcolors.WARNING)
            proceed = Helpers.print_coloured_line("Do you want to continue [Y/n]?")
            if not Helpers.check_Yes(proceed):
                sys.exit()
