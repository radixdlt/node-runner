import json
import os
import sys

import requests
from requests.auth import HTTPBasicAuth

from api.Api import API
from api.Validation import Validation
from utils.utils import Helpers
from utils.utils import bcolors


class Account(API):

    @staticmethod
    def get_register_validator_action(name, url, register_or_update, validator_id):

        data = {
            "type": register_or_update,
            "validator": validator_id,
            "name": name,
            "url": url
        }
        return data

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
        resp = Helpers.send_request(prepared)
        Helpers.json_response_check(resp)

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

    @staticmethod
    def get_update_rake_action(percentage, validator_id):
        # TODO is this percentage by number or decimal?
        data = {
            "type": "UpdateRake",
            "validator": validator_id,
            "percentage": percentage
        }
        return data

    @staticmethod
    def get_update_allow_delegation_flag_action(allowDelegation, validator_id):
        data = {
            "type": "UpdateAllowDelegationFlag",
            "validator": validator_id,
            "allowDelegation": allowDelegation
        }
        return data

    @staticmethod
    def get_update_validator_owner_address_action(owner_id, validator_id):
        data = {
            "type": "UpdateValidatorOwnerAddress",
            "validator": validator_id,
            "owner": owner_id
        }
        return data

    @staticmethod
    def register_or_update_steps(request_data, validator_id):
        ask_add_or_change_info = input("\nDo you want add or change the validator name and info url [Y/n]?")
        if Helpers.check_Yes(ask_add_or_change_info):
            print("--------Registration-----\n")
            ask_registration_or_update = input(
                f"{bcolors.BOLD}\nIs this first time you registering (R) validator  or  you want update (U) the "
                f"registration. Valid "
                f"options: [R/U]?{bcolors.ENDC}")
            if ask_registration_or_update.upper() == "R":
                registertion_action_command = "RegisterValidator"
            elif ask_registration_or_update.upper() == "U":
                registertion_action_command = "UpdateValidator"
            else:
                print("Entered value is invalid")
                sys.exit()

            validator_name = input(f"{bcolors.OKBLUE}Name of your validator:")
            validator_url = input(f"{bcolors.OKBLUE}Info URL of your validator:{bcolors.ENDC}")
            register_action = Account.get_register_validator_action(validator_name, validator_url,
                                                                    registertion_action_command, validator_id)
            request_data["params"]["actions"].append(register_action)
        return request_data

    @staticmethod
    def add_update_rake(request_data, validator_id):
        print("--------Validator fees-----\n")

        print(
            f"{bcolors.WARNING}\nValidator fee may be decreased at any time, but increasing it incurs a delay of "
            f"approx. 2 weeks. Please set it carefully{bcolors.ENDC}")
        ask_validator_fee_setup = input("Do you want to setup or update validator fees [Y/n]?:")
        if Helpers.check_Yes(ask_validator_fee_setup):

            percentage = Helpers.check_percentage_input()

            update_rake = Account.get_update_rake_action(percentage, validator_id)
            request_data["params"]["actions"].append(update_rake)
        return request_data



    @staticmethod
    def setup_update_delegation(request_data, validator_id):
        print("--------Validator fees-----\n")
        print(
            f"{bcolors.WARNING}\nEnabling allowDelegation means anyone can delegate stake to your node. Disabling it "
            f"later will not remove this stake.{bcolors.ENDC}")
        ask_allow_delegation = input("\nSetup or update delegation [Y/n]?")
        if Helpers.check_Yes(ask_allow_delegation):
            allow_delegation = input("\nDo you want allow delegation [Y/n]")
            if allow_delegation.lower() in ("yes", "true", "y"):
                update_allow_delegation_flag = Account.get_update_allow_delegation_flag_action(True,
                                                                                               validator_id)
            elif allow_delegation.lower() in ("no", "false", "n"):
                update_allow_delegation_flag = Account.get_update_allow_delegation_flag_action(False,
                                                                                               validator_id)
            else:
                print("Invalid key entered. Existing the registration process")
                sys.exit()

            request_data["params"]["actions"].append(update_allow_delegation_flag)
        return request_data

    @staticmethod
    def add_change_ownerid(request_data, validator_id):
        print("--------Change owner id-----\n")
        print(
            f"{bcolors.WARNING}\nPlease ensure you set owner account to a valid Radix account that you control (such "
            f"as one created with the Desktop Wallet), as this will also be where any validator fee emissions will be "
            f"credited. It is strongly advised to NOT use the Radix account of your node itself.{bcolors.ENDC} ")
        ask_add_or_change_ownerid = input("\nAdd or Change owner id [Y/n]?")
        if Helpers.check_Yes(ask_add_or_change_ownerid):
            owner_id = input("Enter the owner id:").strip
            update_validator_owner_address = Account.get_update_validator_owner_address_action(owner_id, validator_id)
            request_data["params"]["actions"].append(update_validator_owner_address)

        return request_data
