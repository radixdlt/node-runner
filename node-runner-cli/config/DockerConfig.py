import os
from operator import itemgetter

import yaml

from env_vars import COMPOSE_FILE_OVERIDE
from github.github import latest_release
from setup import Base
from utils.utils import Helpers


class KeyDetails():
    keyfile_path = None
    keyfile_name = None
    keygen_tag = None
    keystore_password = None

    def __init__(self, key_details):
        self.keyfile_path = key_details.get("keyfile_path", None)
        self.keyfile_name = key_details.get("keyfile_name", None)
        self.keygen_tag = key_details.get("keygen_tag", None)
        self.keystore_password = key_details.get("keystore_password", None)

    def __iter__(self):
        yield 'keyfile_path', self.keyfile_path
        yield 'keyfile_name', self.keyfile_name
        yield 'keygen_tag', self.keygen_tag
        yield 'keystore_password', self.keystore_password


class DefaultDockerSettings():
    nodetype = "fullnode"
    composefileurl = None
    keydetails = KeyDetails({})
    core_release = None
    data_directory = None
    genesis_json_location = None
    enable_transaction = False
    network_id = None
    existing_docker_compose = None
    trusted_node = None

    def __iter__(self):
        yield 'nodetype', self.nodetype
        yield 'composefileurl', self.composefileurl
        yield 'keydetails', dict(self.keydetails)
        yield 'core_release', self.core_release
        yield 'data_directory', self.data_directory
        if self.genesis_json_location:
            yield 'genesis_json_location', self.genesis_json_location
        yield 'enable_transaction', self.enable_transaction
        yield 'network_id', self.network_id
        yield 'existing_docker_compose', self.existing_docker_compose
        yield 'trusted_node', self.trusted_node


class DockerConfig:
    core_node_settings = DefaultDockerSettings()

    def __init__(self, release: str):
        self.core_node_settings.core_release = release

    def __iter__(self):
        yield 'core_node_settings', dict(self.core_node_settings)

    def set_composefile_url(self):
        cli_latest_version = latest_release("radixdlt/node-runner")
        self.core_node_settings.composefileurl = \
            os.getenv(COMPOSE_FILE_OVERIDE,
                      f"https://raw.githubusercontent.com/radixdlt/node-runner/{cli_latest_version}/node-runner-cli/release_ymls/radix-{self.core_node_settings.nodetype}-compose.yml")
        print(
            f"Going to setup node type {self.core_node_settings.nodetype} from location {self.core_node_settings.composefileurl}.\n")

    def set_node_type(self, nodetype):
        self.core_node_settings.nodetype = nodetype

    def set_keydetails(self):
        keydetails = self.core_node_settings.keydetails
        if not keydetails.keyfile_path:
            keydetails.keyfile_path = Helpers.get_keyfile_path()
        if not keydetails.keyfile_name:
            keydetails.keyfile_name = Helpers.get_keyfile_name()
        if not keydetails.keygen_tag:
            keydetails.keygen_tag = self.core_node_settings.core_release

        keystore_password, file_location = Base.generatekey(
            keyfile_path=keydetails.keyfile_path,
            keyfile_name=keydetails.keyfile_name,
            keygen_tag=keydetails.keygen_tag)
        keydetails.keystore_password = keystore_password
        self.core_node_settings.keydetails = dict(keydetails)

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

    def set_existing_docker_compose_file(self):
        self.core_node_settings.existing_docker_compose = Base.get_existing_compose_file()

    def loadConfig(self, file):
        with open(file, 'r') as file:
            config_yaml = yaml.safe_load(file)
            core_node = config_yaml["core-node"]

            self.core_node_settings.core_release = core_node.get("core_release", None)
            self.core_node_settings.composefileurl = core_node.get("composefileurl")
            self.core_node_settings.data_directory = core_node.get("data_directory", None)
            self.core_node_settings.genesis_json_location = config_yaml["core-node"].get("genesis_json_location", None)
            self.core_node_settings.enable_transaction = core_node.get("enable_transaction", False)
            self.core_node_settings.network_id = core_node.get("network_id", "1")
            self.core_node_settings.keydetails = KeyDetails(core_node.get("keydetails", None))
            self.core_node_settings.trusted_node = core_node.get("trusted_node", None)
            self.core_node_settings.existing_docker_compose = core_node.get("existing_docker_compose", None)

    def set_trusted_node(self, trusted_node):
        self.core_node_settings.trusted_node = trusted_node
