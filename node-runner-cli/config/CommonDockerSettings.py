import json

from config.BaseConfig import BaseConfig, SetupMode
from github import github
from setup import Base
from utils.Prompts import Prompts, Helpers


class NginxConfig(BaseConfig):
    protect_gateway: str = "true"
    gateway_behind_auth: str = "true"
    enable_transaction_api = "false"
    protect_core: str = "true"
    release = None
    repo = "radixdlt/radixdlt-nginx"


class CommonDockerSettings(BaseConfig):
    network_id: int = None
    network_name: str = None
    genesis_json_location: str = None
    nginx_settings: NginxConfig = NginxConfig({})
    docker_compose: str = f"{Helpers.get_home_dir()}/docker-compose.yml"

    def __init__(self, settings: dict):
        super().__init__(settings)
        for key, value in settings.items():
            setattr(self, key, value)

        if self.network_id:
            self.set_network_name()

    def __iter__(self):
        class_variables = {key: value
                           for key, value in self.__class__.__dict__.items()
                           if not key.startswith('__') and not callable(value)}
        for attr, value in class_variables.items():
            if attr in ['nginx_settings'] and self.__getattribute__(attr):
                yield attr, dict(self.__getattribute__(attr))
            elif self.__getattribute__(attr):
                yield attr, self.__getattribute__(attr)

    def set_network_id(self, network_id: int):
        self.network_id = network_id
        self.set_network_name()

    def set_genesis_json_location(self, genesis_json_location: str):
        self.genesis_json_location = genesis_json_location

    def set_network_name(self):
        if self.network_id == 1:
            self.network_name = "mainnet"
        elif self.network_id == 2:
            self.network_name = "stokenet"
        else:
            raise ValueError("Network id is set incorrect")

    def ask_network_id(self, network_id):
        if not network_id:
            network_id = Base.get_network_id()
        self.set_network_id(int(network_id))
        self.set_genesis_json_location(Base.path_to_genesis_json(self.network_id))

    def ask_nginx_release(self):
        latest_nginx_release = github.latest_release("radixdlt/radixdlt-nginx")
        self.nginx_settings.release = latest_nginx_release
        if "DETAILED" in SetupMode.instance().mode:
            self.nginx_settings.release = Prompts.get_nginx_release(latest_nginx_release)

    def ask_enable_nginx_for_core(self, nginx_on_core):
        if nginx_on_core:
            self.nginx_settings.protect_core = nginx_on_core
        if "DETAILED" in SetupMode.instance().mode:
            self.nginx_settings.protect_core = Prompts.ask_enable_nginx(service="CORE").lower()

    def ask_enable_nginx_for_gateway(self, nginx_on_gateway):
        if nginx_on_gateway:
            self.nginx_settings.protect_gateway = nginx_on_gateway
        if "DETAILED" in SetupMode.instance().mode:
            self.nginx_settings.protect_gateway = Prompts.ask_enable_nginx(service="GATEWAY").lower()

    def check_nginx_required(self):
        if json.loads(self.nginx_settings.protect_gateway.lower()) or json.loads(
                self.nginx_settings.protect_core.lower()):
            return True
        else:
            return False

    def ask_existing_docker_compose_file(self):
        if "DETAILED" in SetupMode.instance().mode:
            self.docker_compose = Prompts.ask_existing_compose_file()
        else:
            open(self.docker_compose, mode='a').close()
