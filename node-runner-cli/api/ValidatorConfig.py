from typing import List

from api.Action import Action
from utils.utils import bcolors, Helpers


class ValidatorConfig:
    @staticmethod
    def registeration(actions: List):
        value_to_set = None
        print("\n--------Registration-----\n")
        Helpers.print_coloured_line(f"Current registration status: {validator_info['registered']}",
                                    bcolors.OKBLUE)
        ask_registration = input(
            Helpers.print_coloured_line(
                "\nEnter the new registration setting [true/false].Press enter if no change required ",
                bcolors.BOLD, return_string=True))
        registration_action_command = None
        if ask_registration.lower() == "true" or ask_registration.lower() == "false":
            value_to_set = bool(ask_registration)
            actions.append(Action().set_validator_registeration(value_to_set))
        else:
            Helpers.print_coloured_line("There are no changes to apply or user input is wrong", bcolors.WARNING)

        return actions

    @staticmethod
    def validator_metadata(actions: List):
        print("\n--------Update validator meta info-----\n")
        Helpers.print_coloured_line(f"Current name: {validator_info['name']}", bcolors.OKBLUE)
        Helpers.print_coloured_line(f"Current url: {validator_info['url']}", bcolors.OKBLUE)
        ask_add_or_change_info = input("\nDo you want add/change the validator name and info url [Y/n]?")
        if Helpers.check_Yes(ask_add_or_change_info):
            Helpers.print_coloured_line(f"Current registration status: {validator_info['registered']}",
                                        bcolors.OKBLUE)

            registration_action_command = "UpdateValidatorMetadata"

            validator_name = input(
                Helpers.print_coloured_line(f"Enter the Name of your validator to be updated:", bcolors.OKBLUE,
                                            return_string=True))
            validator_url = input(
                Helpers.print_coloured_line(f"Enter Info URL of your validator to be updated:", bcolors.OKBLUE,
                                            return_string=True))

            update_validator_meta_action = Account.update_meta_validator_action(validator_name, validator_url,
                                                                                registration_action_command,
                                                                                validator_info['address'])
            request_data["params"]["actions"].append(update_validator_meta_action)
        return request_data
