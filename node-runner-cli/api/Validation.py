import json
import os
import sys

import requests
from requests.auth import HTTPBasicAuth

from api.Api import API
from utils.utils import Helpers, bcolors


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
    def get_validator_info_json():
        resp = Validation.get_validator_info()
        if not resp.ok or  not Helpers.is_json(resp.content):
            Helpers.print_coloured_line("Failed retrieving information from get_node_info method",bcolors.FAIL)
            sys.exit()
        resp_content = json.loads(resp.content)
        if Helpers.is_json(resp.content) and "error" not in resp_content:

            def check_key(key):
                if key not in resp_content["result"]:
                    print(f"'{key}' not present in the json response of validator get_node_info")
                    sys.exit()

            def get_attribute(data, attribute, default_value):
                return data.get(attribute) or default_value

            check_key("registered")
            check_key("allowDelegation")
            check_key("validatorFee")
            check_key("owner")
            check_key("address")

            validator = {
                "name": get_attribute(resp_content["result"], "name", ""),
                "url": get_attribute(resp_content["result"], "url", ""),
                "registered": resp_content["result"]["registered"],
                "allowDelegation": resp_content["result"]["allowDelegation"],
                "validatorFee": resp_content["result"]["validatorFee"],
                "owner": resp_content["result"]["owner"],
                "address": resp_content["result"]["address"],
            }
            return validator
        else:
            print("Error occured fetching validator get_node_info")
            sys.exit()
