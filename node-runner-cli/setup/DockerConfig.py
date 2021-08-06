import os

from env_vars import COMPOSE_FILE_OVERIDE
from setup import Base
from utils.utils import Helpers


class KeyDetails:
    keyfile_path = None
    keyfile_name = None


class DefaultDockerSettings:
    automode = False
    nodetype = "fullnode"
    composefileurl = None
    keydetails = KeyDetails()
    core_release = None
    data_directory = None
    genesis_json_location = None


class DockerConfig:
    settings = DefaultDockerSettings()

    def __init__(self, automode):
        self.settings.automode = automode

    def set_composefile_url(self):
        self.settings.composefileurl = \
            os.getenv(COMPOSE_FILE_OVERIDE,
                      f"https://raw.githubusercontent.com/radixdlt/node-runner/{Helpers.cli_version()}/node-runner-cli/release_ymls/radix-{self.settings.nodetype}-compose.yml")
        print(f"Going to setup node type {self.settings.nodetype} from location {self.settings.composefileurl}.\n")

    def set_node_type(self, nodetype):
        self.settings.nodetype = nodetype

    def set_keydetails(self):
        if not self.settings.keydetails.keyfile_path:
            self.settings.keydetails.keyfile_path = Helpers.get_keyfile_path()
        if not self.settings.keydetails.keyfile_name:
            self.settings.keydetails.keyfile_name = Helpers.get_keyfile_name()

    def set_core_release(self, release):
        self.settings.core_release = release

    def set_data_directory(self):
        if not self.settings.data_directory:
            self.settings.data_directory = Base.get_data_dir()

    def set_network_id(self):
        if not self.settings.network_id:
            self.settings.network_id = Base.get_network_id()
        self.settings.genesis_json_location = Base.path_to_genesis_json(self.settings.network_id)
