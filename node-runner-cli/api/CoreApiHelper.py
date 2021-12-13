import sys, json

from core_client import Configuration, ApiException
from core_client.api import network_api, entity_api, key_api, mempool_api, construction_api
from core_client.model.construction_build_request import ConstructionBuildRequest
from core_client.model.construction_build_response import ConstructionBuildResponse
from core_client.model.construction_submit_request import ConstructionSubmitRequest
from core_client.model.data import Data
from core_client.model.entity_request import EntityRequest
from core_client.model.entity_response import EntityResponse
from core_client.model.key_list_request import KeyListRequest
from core_client.model.key_list_response import KeyListResponse
from core_client.model.key_sign_request import KeySignRequest
from core_client.model.mempool_request import MempoolRequest
from core_client.model.mempool_response import MempoolResponse
from core_client.model.mempool_transaction_request import MempoolTransactionRequest
from core_client.model.network_configuration_response import NetworkConfigurationResponse
from core_client.model.network_status_request import NetworkStatusRequest
from core_client.model.operation import Operation
from core_client.model.operation_group import OperationGroup
from core_client.model.prepared_validator_registered import PreparedValidatorRegistered
from core_client.model.transaction_identifier import TransactionIdentifier
from core_client.model.validator_metadata import ValidatorMetadata
import core_client as core_api
from api.Api import API
from api.ValidatorConfig import ValidatorConfig
from utils.utils import bcolors, Helpers


class CoreApiHelper(API):
    system_config: Configuration = None
    network_identifier = None

    def __init__(self, verify_ssl):
        node_host = API.get_host_info()
        self.system_config = core_api.Configuration(node_host, verify_ssl=verify_ssl)

    def network_configuration(self, print_response=False):

        with core_api.ApiClient(self.system_config) as api_client:
            api_client = self.set_basic_auth(api_client, "admin", "admin")
            try:
                api = network_api.NetworkApi(api_client)
                response: NetworkConfigurationResponse = api.network_configuration_post(dict())
                if print_response:
                    print(response)
                return response
            except ApiException as e:
                Helpers.handleApiException(e)

    def network_status(self, print_response=False):
        with core_api.ApiClient(self.system_config) as api_client:
            api_client = self.set_basic_auth(api_client, "admin", "admin")
            try:
                api = network_api.NetworkApi(api_client)
                response = api.network_status_post(
                    NetworkStatusRequest(self.network_configuration().network_identifier))
                return self.handle_response(response, print_response)
            except ApiException as e:
                Helpers.handleApiException(e)

    def key_list(self, print_response=False):
        with core_api.ApiClient(self.system_config) as api_client:
            api_client = self.set_basic_auth(api_client, "superadmin", "superadmin")
            try:
                api = key_api.KeyApi(api_client)
                response: KeyListResponse = api.key_list_post(
                    KeyListRequest(network_identifier=self.network_configuration().network_identifier))
                return self.handle_response(response, print_response)
            except ApiException as e:
                Helpers.handleApiException(e)

    def mempool(self, print_response=False):
        with core_api.ApiClient(self.system_config) as api_client:
            api_client = self.set_basic_auth(api_client, "admin", "admin")
            try:
                api = mempool_api.MempoolApi(api_client)
                response: MempoolResponse = api.mempool_post(
                    MempoolRequest(network_identifier=self.network_configuration().network_identifier))
                return self.handle_response(response, print_response)
            except ApiException as e:
                Helpers.handleApiException(e)

    def mempool_transaction(self, transactionId: str, print_response=False):
        with core_api.ApiClient(self.system_config) as api_client:
            api_client = self.set_basic_auth(api_client, "admin", "admin")
            try:
                api = mempool_api.MempoolApi(api_client)
                response: MempoolResponse = api.mempool_transaction_post(
                    MempoolTransactionRequest(
                        network_identifier=self.network_configuration().network_identifier,
                        transaction_identifier=TransactionIdentifier(transactionId)
                    )
                )
                return self.handle_response(response, print_response)
            except ApiException as e:
                Helpers.handleApiException(e)

    def entity(self, entity_identifier, print_response=False):
        with core_api.ApiClient(self.system_config) as api_client:
            api_client = self.set_basic_auth(api_client, "admin", "admin")
            try:
                api = entity_api.EntityApi(api_client)
                entityRequest = EntityRequest(
                    network_identifier=self.network_configuration().network_identifier,
                    entity_identifier=entity_identifier
                )
                response: EntityResponse = api.entity_post(entityRequest)
                return self.handle_response(response, print_response)
            except ApiException as e:
                Helpers.handleApiException(e)

    def construction_build(self, actions, print_response=False):
        with core_api.ApiClient(self.system_config) as api_client:
            api_client = self.set_basic_auth(api_client, "admin", "admin")
            try:
                network_configuration: NetworkConfigurationResponse = self.network_configuration()
                key_list: KeyListResponse = self.key_list()
                operation_groups = ValidatorConfig.build_operations(actions, key_list)

                api = construction_api.ConstructionApi(api_client)
                build: ConstructionBuildResponse = api.construction_build_post(ConstructionBuildRequest(
                    network_identifier=network_configuration.network_identifier,
                    fee_payer=key_list.public_keys[0].identifiers.account_entity_identifier,
                    operation_groups=operation_groups
                ))
                return self.handle_response(build, print_response)

            except ApiException as e:
                Helpers.handleApiException(e)

    def key_sign(self, unsigned_transaction, print_response=False):
        with core_api.ApiClient(self.system_config) as api_client:
            api_client = self.set_basic_auth(api_client, "superadmin", "superadmin")
            try:
                network_configuration: NetworkConfigurationResponse = self.network_configuration()
                key_list: KeyListResponse = self.key_list()
                api = key_api.KeyApi(api_client)
                response = api.key_sign_post(KeySignRequest(
                    network_identifier=network_configuration.network_identifier,
                    public_key=key_list.public_keys[0].public_key,
                    unsigned_transaction=unsigned_transaction
                ))
                return self.handle_response(response, print_response)
            except ApiException as e:
                Helpers.handleApiException(e)

    def construction_submit(self, signed_transaction, print_response=False):
        with core_api.ApiClient(self.system_config) as api_client:
            api_client = self.set_basic_auth(api_client, "admin", "admin")
            try:
                api = construction_api.ConstructionApi(api_client)
                network_configuration: NetworkConfigurationResponse = self.network_configuration()
                response = api.construction_submit_post(ConstructionSubmitRequest(
                    network_identifier=network_configuration.network_identifier,
                    signed_transaction=signed_transaction
                ))
                return self.handle_response(response, print_response)
            except ApiException as e:
                Helpers.handleApiException(e)

    @staticmethod
    def set_validator_metadata(name, url):
        return lambda node_identifiers: [
            OperationGroup([
                Operation(
                    type="Data",
                    entity_identifier=node_identifiers.validator_entity_identifier,
                    data=Data(
                        action='CREATE',
                        data_object=ValidatorMetadata(
                            type="ValidatorMetadata",
                            name=name,
                            url=url
                        )
                    )
                )
            ]),
        ]

    @staticmethod
    def set_validator_registered(registered):
        return lambda node_identifiers: [
            OperationGroup([
                Operation(
                    type="Data",
                    entity_identifier=node_identifiers.validator_entity_identifier,
                    data=Data(
                        action='CREATE',
                        data_object=PreparedValidatorRegistered(
                            type="PreparedValidatorRegistered",
                            registered=registered
                        )
                    )
                )
            ])
        ]
