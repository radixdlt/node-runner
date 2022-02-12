# Setup core parser
import sys
from argparse import ArgumentParser

from core_client.model.construction_build_response import ConstructionBuildResponse
from core_client.model.construction_submit_response import ConstructionSubmitResponse
from core_client.model.entity_identifier import EntityIdentifier
from core_client.model.entity_response import EntityResponse
from core_client.model.key_list_response import KeyListResponse
from core_client.model.key_sign_response import KeySignResponse
from core_client.model.sub_entity import SubEntity
from core_client.model.sub_entity_metadata import SubEntityMetadata
import system_client as system_api
from api.Api import API
from api.CoreApiHelper import CoreApiHelper
from api.DefaultApiHelper import DefaultApiHelper
from commands.subcommand import get_decorator, argument
from api.ValidatorConfig import ValidatorConfig

corecli = ArgumentParser(
    description='Core Api comands')
core_parser = corecli.add_subparsers(dest="corecommand")


def corecommand(args=[], parent=core_parser):
    return get_decorator(args, parent)


def handle_core():
    args = corecli.parse_args(sys.argv[3:])
    if args.corecommand is None:
        corecli.print_help()
    else:
        args.func(args)


@corecommand()
def network_configuration(args):
    core_api_helper = CoreApiHelper(False)
    core_api_helper.network_configuration(True)


@corecommand()
def network_status(args):
    core_api_helper = CoreApiHelper(False)
    core_api_helper.network_status(True)


@corecommand([
    argument("-v", "--validator",
             help="Display entity details of validator address",
             action="store_true"),
    argument("-a", "--address",
             help="Display entity details of validator account address",
             action="store_true"),
    argument("-p", "--p2p",
             help="Display entity details of validator peer to peer address",
             action="store_true"),
    argument("-sy", "--subEntitySystem",
             help="Display entity details of validator address along with sub entity system",
             action="store_true"),
    argument("-ss", "--subPreparedStake",
             help="Display entity details of validator account address along with sub entity  prepared_stake",
             action="store_true"),
    argument("-su", "--subPreparedUnStake",
             help="Display entity details of validator account address along with sub entity  prepared_unstake",
             action="store_true"),
    argument("-se", "--subExitingStake",
             help="Display entity details of validator account address along with sub entity exiting_stake",
             action="store_true")
])
def entity(args):
    core_api_helper = CoreApiHelper(False)
    key_list_response: KeyListResponse = core_api_helper.key_list(False)
    validator_address = key_list_response.public_keys[0].identifiers.validator_entity_identifier.address
    account_address = key_list_response.public_keys[0].identifiers.account_entity_identifier.address
    if args.validator:
        if args.subEntitySystem:
            subEntity = SubEntity(address=str("system"))
            entityIdentifier = EntityIdentifier(
                address=validator_address,
                sub_entity=subEntity
            )
        else:
            entityIdentifier = EntityIdentifier(
                address=validator_address,
            )

        core_api_helper.entity(entityIdentifier, True)
        sys.exit()
    if args.address:
        if args.subPreparedStake:
            metadata = SubEntityMetadata(validator=validator_address)
            subEntity = SubEntity(address=str("prepared_stake"), metadata=metadata)
            entityIdentifier = EntityIdentifier(
                address=account_address,
                sub_entity=subEntity
            )
        if args.subPreparedUnStake:
            metadata = SubEntityMetadata(validator=validator_address)
            subEntity = SubEntity(address=str("prepared_unstake"), metadata=metadata)
            entityIdentifier = EntityIdentifier(
                address=account_address,
                sub_entity=subEntity
            )
        if args.subExitingStake:
            metadata = SubEntityMetadata(validator=validator_address)
            subEntity = SubEntity(address=str("exiting_stake"), metadata=metadata)
            entityIdentifier = EntityIdentifier(
                address=account_address,
                sub_entity=subEntity
            )
        else:
            entityIdentifier = EntityIdentifier(
                address=account_address,
            )
        core_api_helper.entity(entityIdentifier, True)
        sys.exit()
    if args.p2p:
        core_api_helper.entity(key_list_response.public_keys[0].identifiers.p2p_node, True)
        sys.exit()


@corecommand()
def key_list(args):
    core_api_helper = CoreApiHelper(False)
    core_api_helper.key_list(True)


@corecommand()
def mempool(args):
    core_api_helper = CoreApiHelper(False)
    core_api_helper.mempool(True)


@corecommand([
    argument("-t", "--transactionId", required=True,
             help="transaction Id to be searched on mempool",
             action="store")
])
def mempool_transaction(args):
    core_api_helper = CoreApiHelper(False)
    core_api_helper.mempool_transaction(args.transactionId, True)


@corecommand()
def update_validator_config(args):
    request_data = {
        "jsonrpc": "2.0",
        "method": "account.submit_transaction_single_step",
        "params": {
            "actions": []
        },
        "id": 1
    }
    node_host = API.get_host_info()
    system_config = system_api.Configuration(node_host, verify_ssl=False)

    defaultApiHelper = DefaultApiHelper(verify_ssl=False)
    defaultApiHelper.check_health()

    core_api_helper = CoreApiHelper(verify_ssl=False)
    key_list_response: KeyListResponse = core_api_helper.key_list()
    validator_info: EntityResponse = core_api_helper.entity(
        key_list_response.public_keys[0].identifiers.validator_entity_identifier)

    actions = []
    actions = ValidatorConfig.registeration(actions, validator_info)
    actions = ValidatorConfig.validator_metadata(actions, validator_info)
    actions = ValidatorConfig.add_validation_fee(actions, validator_info)
    actions = ValidatorConfig.setup_update_delegation(actions, validator_info)
    actions = ValidatorConfig.add_change_ownerid(actions, validator_info)
    build_response: ConstructionBuildResponse = core_api_helper.construction_build(actions, ask_user=True)
    signed_transaction: KeySignResponse = core_api_helper.key_sign(build_response.unsigned_transaction)
    submitted_transaction: ConstructionSubmitResponse = core_api_helper.construction_submit(
        signed_transaction.signed_transaction, print_response=True)
