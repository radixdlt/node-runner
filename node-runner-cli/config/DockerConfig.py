import os
import sys
from pathlib import Path

import yaml

from config.BaseConfig import BaseConfig, SetupMode
from config.CommonDockerSettings import CommonDockerSettings
from config.GatewayDockerConfig import GatewayDockerSettings
from env_vars import MOUNT_LEDGER_VOLUME
from setup import Base
from utils.Prompts import Prompts
from utils.utils import Helpers


class KeyDetails(BaseConfig):
    keyfile_path: str = Helpers.get_default_node_config_dir()
    keyfile_name: str = "node-keystore.ks"
    keygen_tag: str = None
    keystore_password: str = None


class CoreDockerSettings(BaseConfig):
    nodetype: str = "fullnode"
    composefileurl: str = None
    keydetails: KeyDetails = KeyDetails({})
    core_release: str = None
    repo: str = "radixdlt/radixdlt-core"
    data_directory: str = f"{Helpers.get_home_dir()}/data"
    enable_transaction: str = "false"
    trusted_node: str = None
    java_opts: str = "--enable-preview -server -Xms8g -Xmx8g  " \
                     "-XX:MaxDirectMemorySize=2048m " \
                     "-XX:+HeapDumpOnOutOfMemoryError -XX:+UseCompressedOops " \
                     "-Djavax.net.ssl.trustStore=/etc/ssl/certs/java/cacerts " \
                     "-Djavax.net.ssl.trustStoreType=jks -Djava.security.egd=file:/dev/urandom " \
                     "-DLog4jContextSelector=org.apache.logging.log4j.core.async.AsyncLoggerContextSelector"

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

    def ask_keydetails(self, ks_password=None, new_keystore=False):
        keydetails = self.keydetails
        if "DETAILED" in SetupMode.instance().mode:
            keydetails.keyfile_path = Prompts.ask_keyfile_path()
            keydetails.keyfile_name = Prompts.ask_keyfile_name()

        keystore_password, file_location = Base.generatekey(
            keyfile_path=keydetails.keyfile_path,
            keyfile_name=keydetails.keyfile_name,
            keygen_tag=keydetails.keygen_tag, ks_password=ks_password, new=new_keystore)
        keydetails.keystore_password = keystore_password
        self.keydetails = keydetails

    def set_core_release(self, release):
        self.core_release = release
        self.keydetails.keygen_tag = self.core_release

    def ask_data_directory(self):
        if "DETAILED" in SetupMode.instance().mode:
            self.data_directory = Base.get_data_dir(create_dir=False)
        if os.environ.get(MOUNT_LEDGER_VOLUME, "true").lower() == "false":
            self.data_directory = None
        if self.data_directory:
            Path(self.data_directory).mkdir(parents=True, exist_ok=True)

    def ask_enable_transaction(self):
        if "DETAILED" in SetupMode.instance().mode:
            self.enable_transaction = Prompts.ask_enable_transaction()
        elif "GATEWAY" in SetupMode.instance().mode:
            self.enable_transaction = "true"

    def set_trusted_node(self, trusted_node):
        if not trusted_node:
            trusted_node = Prompts.ask_trusted_node()
        self.trusted_node = trusted_node

    def create_config(self, release, trustednode, ks_password, new_keystore):

        self.set_core_release(release)
        self.set_trusted_node(trustednode)
        self.ask_keydetails(ks_password, new_keystore)
        self.ask_data_directory()
        self.ask_enable_transaction()
        return self


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
            self.core_node_settings.existing_docker_compose = core_node.get("docker_compose", None)
