import json
from typing import List

from core_client.model.entity_response import EntityResponse

from api.Action import Action
from utils.utils import Bcolors, Helpers


class ValidatorConfig:
    @staticmethod
    def registration(actions: List, validator_info: EntityResponse, health):
        value_to_set = None
        print("\n--------Registration-----\n")
        registration = [x for x in validator_info.data_objects if x.type == 'PreparedValidatorRegistered']
        Helpers.print_coloured_line(f"Current registration status: {registration[0].registered}",
                                    Bcolors.OKBLUE)
        ask_registration = input(
            Helpers.print_coloured_line(
                "\nEnter the new registration setting [true/false].Press enter if no change required ",
                Bcolors.BOLD, return_string=True))
        if ask_registration.lower() == "true" or ask_registration.lower() == "false":
            value_to_set = json.loads(ask_registration.lower())
            actions.append(Action.set_validator_registeration(value_to_set))
            return actions
        else:
            Helpers.print_coloured_line("There are no changes to apply or user input is wrong", Bcolors.WARNING)
        return actions

    @staticmethod
    def validator_metadata(actions: List, validator_info: EntityResponse, health):
        print("\n--------Update validator meta info-----\n")
        validatorMetadata = [x for x in validator_info.data_objects if x.type == 'ValidatorMetadata']
        Helpers.print_coloured_line(f"Current name: {validatorMetadata[0]['name']}", Bcolors.OKBLUE)
        Helpers.print_coloured_line(f"Current url: {validatorMetadata[0]['url']}", Bcolors.OKBLUE)
        ask_add_or_change_info = input("\nDo you want add/change the validator name and info url [Y/n]?")
        if Helpers.check_Yes(ask_add_or_change_info):
            validator_name = input(
                Helpers.print_coloured_line(f"Enter the Name of your validator to be updated:", Bcolors.OKBLUE,
                                            return_string=True))
            validator_url = input(
                Helpers.print_coloured_line(f"Enter Info URL of your validator to be updated:", Bcolors.OKBLUE,
                                            return_string=True))
            actions.append(Action.set_validator_metadata(validator_name, validator_url))
            return actions
        return actions

    @staticmethod
    def add_validation_fee(actions: List, validator_info: EntityResponse):
        print("\n--------Validator fees-----\n")

        print(
            f"{Bcolors.WARNING}\nValidator fee may be decreased at any time, but increasing it incurs a delay of "
            f"approx. 2 weeks. Please set it carefully{Bcolors.ENDC}")
        validator_fee = [x for x in validator_info.data_objects if x.type == 'PreparedValidatorFee']
        Helpers.print_coloured_line(f"Current validator fees are {int(validator_fee[0]['fee']) / 100}",
                                    Bcolors.OKBLUE)
        ask_validator_fee_setup = input("Do you want to setup or update validator fees [Y/n]?:")
        if Helpers.check_Yes(ask_validator_fee_setup):
            validatorFee = int(Helpers.check_validatorFee_input() * 100)
            actions.append(Action.set_validator_fee(validatorFee))
            return actions
        return actions

    @staticmethod
    def setup_update_delegation(actions: List, validator_info: EntityResponse):
        print("--------Allow delegation-----\n")
        print(
            f"{Bcolors.WARNING}\nEnabling allowDelegation means anyone can delegate stake to your node. Disabling it "
            f"later will not remove this stake.{Bcolors.ENDC}")
        allow_delegation = [x for x in validator_info.data_objects if x.type == 'ValidatorAllowDelegation']
        current_value: bool = allow_delegation[0]['allow_delegation']
        Helpers.print_coloured_line(
            f"\nCurrent setting for allowing delegation : {current_value}",
            Bcolors.BOLD)
        allow_delegation = input(
            Helpers.print_coloured_line(
                "\nEnter the new allow delegation setting [true/false].Press enter if no change required ",
                Bcolors.BOLD, return_string=True))
        if allow_delegation.lower() == "true":
            if not bool(current_value):
                actions.append(Action.set_validator_allow_delegation(json.loads(allow_delegation.lower())))
                return actions
            else:
                Helpers.print_coloured_line(
                    f"\nThere is no change in the delegation status from the current one {current_value}"
                    f". So not updating this action", Bcolors.WARNING)
        elif allow_delegation.lower() == "false":
            if bool(current_value):
                actions.append(Action.set_validator_allow_delegation(json.loads(allow_delegation.lower())))
                return actions
            else:
                Helpers.print_coloured_line(
                    f"\nThere is no change in the delegation status from the current one {validator_info['allowDelegation']}"
                    f"\nSo not updating this action")
        return actions

    @staticmethod
    def add_change_ownerid(actions: List, validator_info: EntityResponse):
        print("--------Change owner id-----\n")
        print(
            f"{Bcolors.WARNING}\nPlease ensure you set owner account to a valid Radix account that you control (such "
            f"as one created with the Desktop Wallet), as this will also be where any validator fee emissions will be "
            f"credited. It is strongly advised to NOT use the Radix account of your node itself.{Bcolors.ENDC} ")
        owner = [x for x in validator_info.data_objects if x.type == 'PreparedValidatorOwner']
        current_value = owner[0]["owner"]["address"]
        Helpers.print_coloured_line(f"\nCurrent settings for owner id={current_value}")

        owner_id = input("\nEnter the new owner id or press Enter not to change:").strip()
        if owner_id != "":
            if owner_id != current_value:
                actions.append(Action.set_validator_owner(owner_id))
                return actions
            Helpers.print_coloured_line("Owner entered is same . So action will not be applied", Bcolors.WARNING)

        return actions

    @staticmethod
    def build_operations(actions, key_list, ask_user=False):
        operation_groups = []
        for action in actions:
            for operation_group in action(key_list.public_keys[0].identifiers):
                operation_groups.append(operation_group)
        if ask_user:
            return ValidatorConfig.ask_permission_build(operation_groups)
        else:
            return operation_groups

    @staticmethod
    def ask_permission_build(operation_groups):
        print(f"{Bcolors.WARNING}\nAbout to update node with following operations{Bcolors.ENDC}")
        print(f"")
        print(f"{Bcolors.BOLD}{print(operation_groups)}{Bcolors.ENDC}")
        submit_changes = input(f"{Bcolors.BOLD}\nDo you want to continue [Y/n]{Bcolors.ENDC}")
        if Helpers.check_Yes(submit_changes) and len(operation_groups) != 0:
            return operation_groups
        else:
            print(f"{Bcolors.WARNING}Changes were not submitted.{Bcolors.ENDC} or there are no actions to submit")
            return operation_groups
