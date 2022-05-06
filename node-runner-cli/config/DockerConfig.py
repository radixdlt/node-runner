import os

from env_vars import COMPOSE_FILE_OVERIDE
from setup import Base
from utils.utils import Helpers


class KeyDetails:
    keyfile_path = None
    keyfile_name = None


class DefaultDockerSettings:
    nodetype = "fullnode"
    composefileurl = None
    keydetails = KeyDetails()
    core_release = None
    data_directory = None
    genesis_json_location = None
    enable_transaction = False


class DockerConfig:
    core_node_settings = DefaultDockerSettings()

    def set_composefile_url(self):
        self.core_node_settings.composefileurl = \
            os.getenv(COMPOSE_FILE_OVERIDE,
                      f"https://raw.githubusercontent.com/radixdlt/node-runner/{Helpers.cli_version()}/node-runner-cli/release_ymls/radix-{self.core_node_settings.nodetype}-compose.yml")
        print(
            f"Going to setup node type {self.core_node_settings.nodetype} from location {self.core_node_settings.composefileurl}.\n")

    def set_node_type(self, nodetype):
        self.core_node_settings.nodetype = nodetype

    def set_keydetails(self):
        if not self.core_node_settings.keydetails.keyfile_path:
            self.core_node_settings.keydetails.keyfile_path = Helpers.get_keyfile_path()
        if not self.core_node_settings.keydetails.keyfile_name:
            self.core_node_settings.keydetails.keyfile_name = Helpers.get_keyfile_name()

    def set_core_release(self, release):
        self.core_node_settings.core_release = release

    def set_data_directory(self):
        if not self.core_node_settings.data_directory:
            self.core_node_settings.data_directory = Base.get_data_dir()

    def set_network_id(self):
        if not self.core_node_settings.network_id:
            self.core_node_settings.network_id = Base.get_network_id()
        self.core_node_settings.genesis_json_location = Base.path_to_genesis_json(self.core_node_settings.network_id)

    def set_enable_transaction(self, enabletransactions):
        self.core_node_settings.enable_transaction = enabletransactions
