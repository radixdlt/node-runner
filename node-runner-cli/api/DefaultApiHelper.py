import json
import sys
import system_client as system_api
from system_client import ApiException, Configuration, ApiClient
from system_client.api import default_api

import requests
from requests.auth import HTTPBasicAuth

from api.Api import API
from utils.utils import Helpers, bcolors


def set_basic_auth(api_client: ApiClient, usertype: str, username: str):
    user = Helpers.get_nginx_user(usertype=usertype, default_username=username)
    headers = Helpers.get_basic_auth_header(user)
    api_client.set_default_header("Authorization", headers["Authorization"])
    return api_client


class DefaultApiHelper(API):
    system_config: Configuration = None

    def __init__(self, verify_ssl):
        node_host = API.get_host_info()
        self.system_config = system_api.Configuration(node_host, verify_ssl=verify_ssl)

    def health(self,print_response=False):
        with system_api.ApiClient(self.system_config) as api_client:
            api_client = set_basic_auth(api_client, "admin", "admin")
            try:
                api = default_api.DefaultApi(api_client)
                health_response = api.system_health_get()
                if print_response:
                    print(health_response)
                return health_response
            except ApiException as e:
                Helpers.handleApiException(e)

    @staticmethod
    def get_request(usertype, username, api_path):
        node_host = API.get_host_info()
        user = Helpers.get_nginx_user(usertype=usertype, default_username=username)
        headers = Helpers.get_basic_auth_header(user)
        req = requests.Request('GET',
                               f"{node_host}/{api_path}",
                               headers=headers)

        prepared = req.prepare()
        prepared.headers['Content-Type'] = 'application/json'
        return Helpers.send_request(prepared)

    def get_version(self):
        with system_api.ApiClient(self.system_config) as api_client:
            api_client = set_basic_auth(api_client, "admin", "admin")
            try:
                api = default_api.DefaultApi(api_client)
                print(api.system_version_get())
            except ApiException as e:
                Helpers.handleApiException(e)

    def metrics(self):
        with system_api.ApiClient(self.system_config) as api_client:
            api_client = set_basic_auth(api_client, "admin", "admin")
            try:
                api = default_api.DefaultApi(api_client)
                print(api.system_metrics_get())
            except ApiException as e:
                Helpers.handleApiException(e)

    def prometheus_metrics(self):
        with system_api.ApiClient(self.system_config) as api_client:
            api_client = set_basic_auth(api_client, "metrics", "metrics")
            try:
                api = default_api.DefaultApi(api_client)
                print(api.prometheus_metrics_get())
            except ApiException as e:
                Helpers.handleApiException(e)

    def check_health(self):
        Helpers.print_coloured_line("Checking status of the node\n", bcolors.BOLD)
        health = self.health()

        if health["status"] != "UP":
            Helpers.print_coloured_line(
                f"Node status is {health['status']} Rerun the command once node is completely synced",
                bcolors.WARNING)
            proceed = Helpers.print_coloured_line("Do you want to continue [Y/n]?")
            if not Helpers.check_Yes(proceed):
                sys.exit()
