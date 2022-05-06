import os

from env_vars import COMPOSE_FILE_OVERIDE
from setup import Base
from utils.utils import Helpers


class Subscriptable:
    def __class_getitem__(cls, item):
        return cls._get_child_dict()[item]

    @classmethod
    def _get_child_dict(cls):
        return {k: v for k, v in cls.__dict__.items() if not k.startswith('_')}


class KeyDetails(Subscriptable):
    keyfile_path = None
    keyfile_name = None
    keygen_tag = None
    keystore_password = None


class DefaultDockerSettings(Subscriptable):
    nodetype = "fullnode"
    composefileurl = None
    keydetails = KeyDetails()
    core_release = None
    data_directory = None
    genesis_json_location = None
    enable_transaction = False
    network_id = None
    existing_docker_compose = "radix-fullnode-compose.yml"


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
        if not self.core_node_settings.keydetails.keygen_tag:
            self.core_node_settings.keydetails.keygen_tag = self.core_node_settings.core_release

        keystore_password, file_location = Base.generatekey(
            keyfile_path=self.core_node_settings.keydetails.keyfile_path,
            keyfile_name=self.core_node_settings.keydetails.keyfile_name,
            keygen_tag=self.core_node_settings.keydetails.keygen_tag)
        self.core_node_settings.keydetails.keystore_password = keystore_password

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
