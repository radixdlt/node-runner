import unittest
import warnings

from core_client.model.construction_build_response import ConstructionBuildResponse
from core_client.model.entity_response import EntityResponse
from core_client.model.key_list_response import KeyListResponse
from core_client.model.key_sign_response import KeySignResponse
from core_client.model.mempool_response import MempoolResponse
from core_client.model.network_configuration_response import NetworkConfigurationResponse
from core_client.model.network_status_response import NetworkStatusResponse

from api.Action import Action
from api.CoreApiHelper import CoreApiHelper
from github.github import latest_release


class GitHubTests(unittest.TestCase):

    def test_latest_release(self):
        latest_release()


class ApiTests(unittest.TestCase):
    """
    Below tests require environment variables exported before in hand. Below are the environment variables to export
    NODE_END_POINT=https://35.154.183.163
    DISABLE_VERSION_CHECK=true
    NGINX_ADMIN_PASSWORD=<Admin password for above node>
    NGINX_METRICS_PASSWORD=<metrics password for above node>
    NGINX_SUPERADMIN_PASSWORD=<superadmin password for above node>
    """

    core_api_helper = CoreApiHelper(False)

    @classmethod
    def setUpClass(cls):
        warnings.simplefilter("ignore")

    def test_network_configuration(self):
        self.assertIsInstance(self.core_api_helper.network_configuration(), NetworkConfigurationResponse)

    def test_network_status(self):
        self.assertIsInstance(self.core_api_helper.network_status(), NetworkStatusResponse)

    def test_key_list(self):
        self.assertIsInstance(self.core_api_helper.key_list(), KeyListResponse)

    def test_mempool(self):
        self.assertIsInstance(self.core_api_helper.mempool(), MempoolResponse)

    def test_entity(self):
        key_list_response: KeyListResponse = self.core_api_helper.key_list(True)
        response = self.core_api_helper.entity(key_list_response.public_keys[0].identifiers.validator_entity_identifier,
                                               True)
        self.assertIsInstance(response, EntityResponse)

    @unittest.skip("Needs enough balance")
    def test_construction_build(self):
        key_list_response: KeyListResponse = self.core_api_helper.key_list()
        validator_info: EntityResponse = self.core_api_helper.entity(
            key_list_response.public_keys[0].identifiers.validator_entity_identifier)
        actions = [Action().set_validator_registeration(False)]
        response = self.core_api_helper.construction_build(actions)
        self.assertIsInstance(response, ConstructionBuildResponse)

    @unittest.skip("Needs enough balance")
    def test_key_sign(self):
        key_list_response: KeyListResponse = self.core_api_helper.key_list()
        validator_info: EntityResponse = self.core_api_helper.entity(
            key_list_response.public_keys[0].identifiers.validator_entity_identifier)
        actions = [Action().set_validator_registeration(False)]
        build_response = self.core_api_helper.construction_build(actions)
        response = self.core_api_helper.key_sign(build_response.unsigned_transaction)
        self.assertIsInstance(response, KeySignResponse)


if __name__ == '__main__':
    unittest.main(warnings='ignore')
