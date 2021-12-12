import json
import sys
import system_client as system_api
from system_client import ApiException, Configuration, ApiClient
from system_client.api import default_api

import requests
from requests.auth import HTTPBasicAuth

from api.Api import API
from utils.utils import Helpers, bcolors


class RestApi(API):
    @staticmethod
    def health(api_client: ApiClient):
        try:
            api = default_api.DefaultApi(api_client)
            return api.system_health_get()
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

    @staticmethod
    def get_version():
        RestApi.get_request("admin", "admin", "version")

    @staticmethod
    def metrics(apl_Client: ApiClient):
        try:
            api = default_api.DefaultApi(apl_Client)
            print(api.system_metrics_get())
        except ApiException as e:
            Helpers.handleApiException(e)

    @staticmethod
    def prometheus_metrics():
        node_host = API.get_host_info()
        system_config = system_api.Configuration(node_host, verify_ssl=False)
        with system_api.ApiClient(system_config) as api_client:
            user = Helpers.get_nginx_user(usertype="metrics", default_username="metrics")
            headers = Helpers.get_basic_auth_header(user)
            api_client.set_default_header("Authorization", headers["Authorization"])
            try:
                api = default_api.DefaultApi(api_client)
                print(api.prometheus_metrics_get())
            except ApiException as e:
                Helpers.handleApiException(e)

    @staticmethod
    def check_health(api_client: ApiClient):
        Helpers.print_coloured_line("Checking status of the node\n", bcolors.BOLD)
        health = RestApi.health(api_client)

        if health["status"] != "UP":
            Helpers.print_coloured_line(
                f"Node status is {health['status']} Rerun the command once node is completely synced",
                bcolors.WARNING)
            proceed = Helpers.print_coloured_line("Do you want to continue [Y/n]?")
            if not Helpers.check_Yes(proceed):
                sys.exit()
