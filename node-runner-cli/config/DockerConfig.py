import os
from operator import itemgetter

import yaml

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
    yaml_tag = u'!KeyDetails'
    yaml_loader = yaml.SafeLoader

    def __init__(self, key_details):
        self.keyfile_path = key_details.get("keyfile_path", None)
        self.keyfile_name = key_details.get("keyfile_name", None)
        self.keygen_tag = key_details.get("keygen_tag", None)
        self.keystore_password = key_details.get("keystore_password", None)

    def __repr__(self):
        return "%s(keyfile_path=%r, keyfile_name=%r,  keygen_tag=%r, keystore_password=%r )" % (
            self.__class__.__name__, self.keyfile_path,
            self.keyfile_name, self.keygen_tag, self.keystore_password)

class DefaultDockerSettings(Subscriptable):
    nodetype = "fullnode"
    composefileurl = None
    keydetails = KeyDetails({})
    core_release = None
    data_directory = None
    genesis_json_location = None
    enable_transaction = False
    network_id = None
    existing_docker_compose = "radix-fullnode-compose.yml"
    trusted_node = None


class DockerConfig:
    core_node_settings = DefaultDockerSettings()

    def __init__(self, release: str):
        self.core_node_settings.core_release = release

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
            self.core_node_settings.data_directory = Base.get_data_dir(create_dir=False)

    def set_network_id(self):
        if not self.core_node_settings.network_id:
            self.core_node_settings.network_id = Base.get_network_id()
        self.core_node_settings.genesis_json_location = Base.path_to_genesis_json(self.core_node_settings.network_id)

    def set_enable_transaction(self, enabletransactions):
        self.core_node_settings.enable_transaction = enabletransactions

    def loadConfig(self, file):
        with open(file, 'r') as file:
            config_yaml = yaml.safe_load(file)
            core_node = config_yaml["core-node"]

            self.core_node_settings.core_release = core_node.get("core_release", None)
            self.core_node_settings.data_directory = core_node.get("data_directory", None)
            self.core_node_settings.genesis_json_location = config_yaml["core-node"].get("genesis_json_location", None)
            self.core_node_settings.enable_transaction = core_node.get("enable_transaction", False)
            self.core_node_settings.network_id = core_node.get("network_id", "1")
            self.core_node_settings.keydetails = KeyDetails(core_node.get("key_details", None))
            self.core_node_settings.trusted_node = core_node.get("trusted_node", None)
            self.core_node_settings.existing_docker_compose = core_node.get("existing_docker_compose", None)
