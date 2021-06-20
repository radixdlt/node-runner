import os
import requests
from requests.auth import HTTPBasicAuth

from api.Api import API
from api.Validation import Validation
from utils.utils import Helpers


class Account(API):

    @staticmethod
    def register_validator(name, url):
        validator_id = Validation.get_validator_id()
        data = f"""
        {{
            "jsonrpc": "2.0",
            "method": "account.submit_transaction_single_step",
            "params": {{
                "actions": [
                    {{
                        "type": "RegisterValidator",
                        "validator": "{validator_id}",
                        "name": "{name}",
                        "url": "{url}"
                    }}
                ]
            }},
            "id": 1
        }}
                
        """
        Account.post_on_account(data)

    @staticmethod
    def un_register_validator():
        validator_id = Validation.get_validator_id()
        data = f"""
         {{
            "jsonrpc": "2.0",
            "method": "account.submit_transaction_single_step",
            "params": {{
                "actions": [
                    {{
                        "type": "UnregisterValidator",
                        "validator": "{validator_id}"
                    }}
                ]
            }},
            "id": 1
        }}
        """
        Account.post_on_account(data)

    @staticmethod
    def post_on_account(data):
        node_host = Account.get_host_info()
        user = Helpers.get_nginx_user(usertype="superadmin", default_username="superadmin")

        req = requests.Request('POST',
                               f"{node_host}/account",
                               data=data,
                               auth=HTTPBasicAuth(user["name"], user["password"]))

        prepared = req.prepare()
        prepared.headers['Content-Type'] = 'application/json'
        Helpers.send_request(prepared)

    @staticmethod
    def get_info():

        data = f"""
            {{
                "jsonrpc": "2.0",
                "method": "account.get_info",
                "params": [],
                "id": 1
            }}
        """
        Account.post_on_account(data)
