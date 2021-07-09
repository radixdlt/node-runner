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
        validator_id = Validation.get_validator_info_json()
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
    def get_update_rake_action(validatorFee, validator_id):
        # TODO is this validatorFee by number or decimal?
        data = {
            "type": "UpdateValidatorFee",
            "validator": validator_id,
            "validatorFee": validatorFee
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
    def register_or_update_steps(request_data, validator_info):
        ask_add_or_change_info = input("\nDo you want register or add/change the validator name and info url [Y/n]?")
        if Helpers.check_Yes(ask_add_or_change_info):

            print("\n--------Registration-----\n")
            Helpers.print_coloured_line(f"Current name: {validator_info['name']}", bcolors.OKBLUE)
            Helpers.print_coloured_line(f"Current url: {validator_info['url']}", bcolors.OKBLUE)
            Helpers.print_coloured_line(f"Current registration status: {validator_info['registered']}",
                                        bcolors.OKBLUE)

            if not bool(validator_info['registered']):
                registration_action_command = "RegisterValidator"
            else:
                registration_action_command = "UpdateValidator"

            validator_name = input(
                Helpers.print_coloured_line(f"Enter the Name of your validator to be updated:", bcolors.OKBLUE,
                                            return_string=True))
            validator_url = input(
                Helpers.print_coloured_line(f"Enter Info URL of your validator to be updated:", bcolors.OKBLUE,
                                            return_string=True))

            register_action = Account.get_register_validator_action(validator_name, validator_url,
                                                                    registration_action_command,
                                                                    validator_info['address'])
            request_data["params"]["actions"].append(register_action)
        return request_data

    @staticmethod
    def add_update_rake(request_data, validator_info):
        print("\n--------Validator fees-----\n")

        print(
            f"{bcolors.WARNING}\nValidator fee may be decreased at any time, but increasing it incurs a delay of "
            f"approx. 2 weeks. Please set it carefully{bcolors.ENDC}")
        Helpers.print_coloured_line(f"Current validator fees are {int(validator_info['validatorFee']) / 100}",
                                    bcolors.OKBLUE)
        ask_validator_fee_setup = input("Do you want to setup or update validator fees [Y/n]?:")
        if Helpers.check_Yes(ask_validator_fee_setup):
            validatorFee = Helpers.check_validatorFee_input()

            update_rake = Account.get_update_rake_action(validatorFee, validator_info['address'])
            request_data["params"]["actions"].append(update_rake)
        return request_data

    @staticmethod
    def setup_update_delegation(request_data, validator_info):
        print("--------Allow delegation-----\n")
        print(
            f"{bcolors.WARNING}\nEnabling allowDelegation means anyone can delegate stake to your node. Disabling it "
            f"later will not remove this stake.{bcolors.ENDC}")

        Helpers.print_coloured_line(f"\nCurrent setting for allowing delegation : {validator_info['allowsDelegation']}",
                                    bcolors.BOLD)
        allow_delegation = input(
            Helpers.print_coloured_line(
                "\nEnter the new allow delegation setting [true/false].Press enter if no change required ",
                bcolors.BOLD, return_string=True))
        if allow_delegation.lower() == "true":
            if not bool(validator_info['allowsDelegation']):
                request_data["params"]["actions"].append(Account.get_update_allow_delegation_flag_action(True,
                                                                                                         validator_info[
                                                                                                             'address']))
            else:
                Helpers.print_coloured_line(
                    f"\nThere is no change in the delegation status from the current one {validator_info['allowsDelegation']}"
                    f". So not updating this action", bcolors.WARNING)
        elif allow_delegation.lower() == "false":
            if bool(validator_info['allowsDelegation']):
                request_data["params"]["actions"].append(Account.get_update_allow_delegation_flag_action(False,
                                                                                                         validator_info[
                                                                                                             'address']))
            else:
                Helpers.print_coloured_line(
                    f"\nThere is no change in the delegation status from the current one {validator_info['allowsDelegation']}"
                    f"\nSo not updating this action")
        return request_data

    @staticmethod
    def add_change_ownerid(request_data, validator_info):
        print("--------Change owner id-----\n")
        print(
            f"{bcolors.WARNING}\nPlease ensure you set owner account to a valid Radix account that you control (such "
            f"as one created with the Desktop Wallet), as this will also be where any validator fee emissions will be "
            f"credited. It is strongly advised to NOT use the Radix account of your node itself.{bcolors.ENDC} ")
        Helpers.print_coloured_line(f"\nCurrent settings for owner id={validator_info['owner']}")

        owner_id = input("\nEnter the new owner id or press Enter not to change:").strip()
        if owner_id != "":
            if owner_id == validator_info['owner']:
                Helpers.print_coloured_line("Owner entered is same . So action will not be applied", bcolors.WARNING)
                return request_data
            update_validator_owner_address = Account.get_update_validator_owner_address_action(owner_id,
                                                                                               validator_info[
                                                                                                   'address'])
            request_data["params"]["actions"].append(update_validator_owner_address)

        return request_data
