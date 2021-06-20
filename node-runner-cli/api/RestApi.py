import requests
from requests.auth import HTTPBasicAuth

from api.Api import API
from utils.utils import Helpers


class RestApi(API):
    @staticmethod
    def get_health():
        RestApi.get_request("admin", "admin", "health")

    @staticmethod
    def get_request(usertype, username, api_path):
        node_host = API.get_host_info()
        user = Helpers.get_nginx_user(usertype=usertype, default_username=username)

        req = requests.Request('GET',
                               f"{node_host}/{api_path}",
                               auth=HTTPBasicAuth(user["name"], user["password"]))

        prepared = req.prepare()
        prepared.headers['Content-Type'] = 'application/json'
        Helpers.send_request(prepared)

    @staticmethod
    def get_version():
        RestApi.get_request("admin", "admin", "version")

    @staticmethod
    def get_universe():
        RestApi.get_request("admin", "admin", "universe.json")

    @staticmethod
    def get_metrics():
        RestApi.get_request("metrics", "metrics", "metrics")
