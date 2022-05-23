import sys
from pathlib import Path

import yaml

from config.BaseConfig import BaseConfig
from config.CommonDockerSettings import CommonDockerSettings
from config.GatewayDockerConfig import GatewayDockerSettings
from setup import Base
from utils.Prompts import Prompts


class KeyDetails(BaseConfig):
    keyfile_path: str = None
    keyfile_name: str = None
    keygen_tag: str = None
    keystore_password: str = None


class CoreDockerSettings(BaseConfig):
    nodetype: str = "fullnode"
    composefileurl: str = None
    keydetails: KeyDetails = KeyDetails({})
    core_release: str = None
    data_directory: str = None
    enable_transaction: str = False
    existing_docker_compose: str = None
    trusted_node: str = None

    def __iter__(self):
        class_variables = {key: value
                           for key, value in self.__class__.__dict__.items()
                           if not key.startswith('__') and not callable(value)}
        for attr, value in class_variables.items():
            if attr in ['keydetails']:
                yield attr, dict(self.__getattribute__(attr))
            elif self.__getattribute__(attr):
                yield attr, self.__getattribute__(attr)

    def set_node_type(self, nodetype="fullnode"):
        self.nodetype = nodetype

    def ask_keydetails(self):
        keydetails = self.keydetails
        if not keydetails.keyfile_path:
            keydetails.keyfile_path = Prompts.ask_keyfile_path()
        if not keydetails.keyfile_name:
            keydetails.keyfile_name = Prompts.ask_keyfile_name()
        if not keydetails.keygen_tag:
            keydetails.keygen_tag = self.core_release

        keystore_password, file_location = Base.generatekey(
            keyfile_path=keydetails.keyfile_path,
            keyfile_name=keydetails.keyfile_name,
            keygen_tag=keydetails.keygen_tag)
        keydetails.keystore_password = keystore_password
        self.keydetails = keydetails

    def set_core_release(self, release):
        self.core_release = release

    def ask_data_directory(self):
        if not self.data_directory:
            self.data_directory = Base.get_data_dir(create_dir=False)

    def ask_enable_transaction(self):
        self.enable_transaction = Prompts.ask_enable_transaction()

    def ask_existing_docker_compose_file(self):
        self.existing_docker_compose = Prompts.ask_existing_compose_file()

    def set_trusted_node(self, trusted_node):
        # Prompts.ask_trusted_node()
        self.trusted_node = trusted_node


class DockerConfig:
    core_node_settings: CoreDockerSettings = CoreDockerSettings({})
    common_settings: CommonDockerSettings = CommonDockerSettings({})
    gateway_settings: GatewayDockerSettings = GatewayDockerSettings({})

    def __init__(self, release: str):
        self.core_node_settings.core_release = release

    def loadConfig(self, file):
        my_file = Path(file)
        if not my_file.is_file():
            sys.exit("Unable to find config file"
                     "Run `radixnode docker init` to setup one")
        with open(file, 'r') as file:
            config_yaml = yaml.safe_load(file)
            core_node = config_yaml["core_node"]
            common_settings = config_yaml["common_config"]
            self.core_node_settings.core_release = core_node.get("core_release", None)
            self.core_node_settings.data_directory = core_node.get("data_directory", None)
            self.core_node_settings.genesis_json_location = core_node.get("genesis_json_location", None)
            self.core_node_settings.enable_transaction = core_node.get("enable_transaction", False)
            self.common_settings = CommonDockerSettings(
                {"network_id": common_settings.get("network_id", "1")})
            self.core_node_settings.keydetails = KeyDetails(core_node.get("keydetails", None))
            self.core_node_settings.trusted_node = core_node.get("trusted_node", None)
            self.core_node_settings.existing_docker_compose = core_node.get("existing_docker_compose", None)
