import json
import os
import sys

import requests
from requests.auth import HTTPBasicAuth

from api.Api import API
from utils.utils import Helpers, bcolors


class Validation(API):

    @staticmethod
    def get_node_info():
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
        headers = Helpers.get_basic_auth_header(user)

        req = requests.Request('POST',
                               f"{node_host}/validation",
                               data=data,
                               headers=headers)

        prepared = req.prepare()
        return Helpers.send_request(prepared)

    @staticmethod
    def get_validator_info_json():
        resp = Validation.get_node_info()
        if not resp.ok or not Helpers.is_json(resp.content):
            Helpers.print_coloured_line("Failed retrieving information from get_node_info method", bcolors.FAIL)
            sys.exit()
        resp_content = json.loads(resp.content)
        if Helpers.is_json(resp.content) and "error" not in resp_content:

            def check_key(key, dest):
                if key not in dest:
                    print(f"'{key}' not present in the json response of validator get_node_info")
                    sys.exit()

            def get_attribute(data, attribute, default_value):
                if attribute not in data:
                    return default_value
                return data.get(attribute)

            epochInfo = resp_content["result"]["epochInfo"]

            def check_updates_return(key):
                return epochInfo["updates"][key] if get_attribute(
                    epochInfo["updates"], key, None) is not None else \
                    epochInfo["current"][key]

            check_key("registered", epochInfo["current"])
            check_key("allowDelegation", resp_content["result"])
            check_key("validatorFee", epochInfo["current"])
            check_key("owner", epochInfo["current"])
            check_key("address", resp_content["result"])

            validator = {
                "name": get_attribute(resp_content["result"], "name", ""),
                "url": get_attribute(resp_content["result"], "url", ""),
                "registered": check_updates_return("registered"),
                "allowDelegation": resp_content["result"]["allowDelegation"],
                "validatorFee": check_updates_return("validatorFee"),
                "owner": check_updates_return("owner"),
                "address": resp_content["result"]["address"],
            }
            return validator
        else:
            print("Error occured fetching validator get_node_info")
            sys.exit()
