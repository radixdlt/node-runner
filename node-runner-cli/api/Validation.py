import json
import os
import requests
from requests.auth import HTTPBasicAuth

from api.Api import API
from utils.utils import Helpers


class Validation(API):

    @staticmethod
    def get_validator_info():
        data = f"""
            {{
                "jsonrpc": "2.0",
                "method": "validation.get_node_info",
                "params": [],
                "id": 1
            }}
        """
        return Validation.post_on_validation(data)

    @staticmethod
    def get_next_epoch_data():
        data = f"""
            {{
                "jsonrpc": "2.0",
                "method": "validation.get_next_epoch_data",
                "params": [],
                "id": 1
            }}
        """
        return Validation.post_on_validation(data)

    @staticmethod
    def get_current_epoch_data():
        data = f"""
            {{
                "jsonrpc": "2.0",
                "method": "validation.get_current_epoch_data",
                "params": [],
                "id": 1
            }}
        """
        return Validation.post_on_validation(data)

    @staticmethod
    def post_on_validation(data):
        node_host = Validation.get_host_info()
        user = Helpers.get_nginx_user(usertype="admin", default_username="admin")

        req = requests.Request('POST',
                               f"{node_host}/validation",
                               data=data,
                               auth=HTTPBasicAuth(user["name"], user["password"]))

        prepared = req.prepare()
        return Helpers.send_request(prepared)

    @staticmethod
    def get_validator_id():
        resp = Validation.get_validator_info()
        if Helpers.is_json(resp.content):
            return json.loads(resp.content)["result"]["address"]
        else:
            print("Error occured fetching validator address")