# Setup core parser
import sys
from argparse import ArgumentParser

from core_client.model.construction_build_response import ConstructionBuildResponse
from core_client.model.entity_identifier import EntityIdentifier
from core_client.model.entity_response import EntityResponse
from core_client.model.key_list_response import KeyListResponse
from core_client.model.key_sign_response import KeySignResponse
from core_client.model.sub_entity import SubEntity
from core_client.model.sub_entity_metadata import SubEntityMetadata

from api.CoreApiHelper import CoreApiHelper
from api.DefaultApiHelper import DefaultApiHelper
from api.ValidatorConfig import ValidatorConfig
from commands.subcommand import get_decorator, argument
from utils.Prompts import Prompts
from utils.utils import Helpers, bcolors
from utils.utils import print_vote_and_fork_info

corecli = ArgumentParser(
    description='Subcommand to aid interaction with core api',
    usage="radixnode api core "
)
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
    """
    This command the network configuration of the network the node is connected to.
    """
    core_api_helper = CoreApiHelper(False)
    core_api_helper.network_configuration(True)


@corecommand()
def network_status(args):
    """
    This command returns the current state and status of the node's copy of the ledger
    """
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
    """
    This command helps to retrieve information about an entity.
    CAUTION - Running these commands on any node will slow down your node. If you are running a validator,
    it may miss proposals.
    The command will prompt for you to continue or not.
    For automation purpose, you can suppress the prompt exporting env variable named SUPPRESS_API_COMMAND_WARN=true
    """

    if not Prompts.warn_slow_command():
        sys.exit(1)

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
    """
    This command helps to list the details of the validator keystore on a running node using node's CORE API
    """
    core_api_helper = CoreApiHelper(False)
    core_api_helper.key_list(True)


@corecommand()
def mempool(args):
    """
    This command helps to fetch transactions in mempool
    """
    core_api_helper = CoreApiHelper(False)
    core_api_helper.mempool(True)


@corecommand([
    argument("-t", "--transactionId", required=True,
             help="transaction Id to be searched on mempool",
             action="store")
])
def mempool_transaction(args):
    """
    This command helps to fetch transaction in mempool of the node by transaction Id
    """
    core_api_helper = CoreApiHelper(False)
    core_api_helper.mempool_transaction(args.transactionId, True)


@corecommand()
def update_validator_config(args):
    """
    Utility command that helps a node runner to

    'register ' or  'unregister' or 'set validator metadata such as name/url' or 'Add or change validator fee'
    or 'Setup delegation or change owner id' or 'Prompt for voting if ready for forking'
    
    """
    health = DefaultApiHelper(verify_ssl=False).check_health()
    core_api_helper = CoreApiHelper(verify_ssl=False)

    key_list_response: KeyListResponse = core_api_helper.key_list()

    validator_info: EntityResponse = core_api_helper.entity(
        key_list_response.public_keys[0].identifiers.validator_entity_identifier)

    actions = []
    actions = ValidatorConfig.registration(actions, validator_info, health)
    actions = ValidatorConfig.validator_metadata(actions, validator_info, health)
    actions = ValidatorConfig.add_validation_fee(actions, validator_info)
    actions = ValidatorConfig.setup_update_delegation(actions, validator_info)
    actions = ValidatorConfig.add_change_ownerid(actions, validator_info)
    build_response: ConstructionBuildResponse = core_api_helper.construction_build(actions, ask_user=True)
    if build_response:
        signed_transaction: KeySignResponse = core_api_helper.key_sign(build_response.unsigned_transaction)
        core_api_helper.construction_submit(signed_transaction.signed_transaction, print_response=True)

    if health['fork_vote_status'] == 'VOTE_REQUIRED':
        print("\n------Candidate fork detected------")
        engine_configuration = core_api_helper.engine_configuration()
        print_vote_and_fork_info(health, engine_configuration)
        should_vote = input(
            f"Do you want to signal the readiness for {core_api_helper.engine_configuration().forks[-1]['name']} now? [Y/n]{bcolors.ENDC}")
        if Helpers.check_Yes(should_vote): core_api_helper.vote(print_response=True)


@corecommand()
def signal_protocol_update_readiness(args):
    """
    This command helps to signal readiness for forking if there is voting required
    """
    core_api_helper = CoreApiHelper(False)
    health = DefaultApiHelper(False).health()
    if health['fork_vote_status'] == 'VOTE_REQUIRED':
        candidate_fork_name = core_api_helper.engine_configuration()["forks"][-1]['name']
        print(
            f"{bcolors.WARNING}NOTICE: Because the validator is running software with a candidate fork ({candidate_fork_name}{bcolors.WARNING}), " +
            "by performing this action, the validator will signal the readiness to run this fork onto the ledger.\n" +
            f"If you later choose to downgrade the software to a version that no longer includes this fork configuration, you should manually retract your readiness signal by using the retract-candidate-fork-readiness-signal subcommand.{bcolors.ENDC}"
        )
        should_vote = input(
            f"Do you want to signal the readiness for {core_api_helper.engine_configuration().forks[-1]['name']} now? [Y/n]{bcolors.ENDC}")
        if Helpers.check_Yes(should_vote): core_api_helper.vote(print_response=True)
    else:
        print(f"{bcolors.WARNING}There's no need to signal the readiness for any candidate fork.{bcolors.ENDC}")


@corecommand()
def retract_protocol_update_readiness(args):
    """
    This command helps to withdraw from voting for the fork
    """
    core_api_helper = CoreApiHelper(False)
    should_vote = input(
        f"This action will retract your candidate fork readiness signal (if there was one), continue? [Y/n]{bcolors.ENDC}")
    if Helpers.check_Yes(should_vote): core_api_helper.withdraw_vote(print_response=True)
