from config.BaseConfig import BaseConfig
from setup import Base
from utils.Prompts import Prompts


class NginxConfig(BaseConfig):
    protect_gateway = None
    protect_core = None
    release = None


class CommonDockerSettings(BaseConfig):
    network_id: int = None
    network_name: str = None
    genesis_json_location: str = None
    nginx_settings: NginxConfig = NginxConfig({})

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
            if attr in ['nginx_settings']:
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

    def ask_network_id(self):
        if not self.network_id:
            self.set_network_id(Base.get_network_id())
        self.set_genesis_json_location(Base.path_to_genesis_json(self.network_id))

    def ask_nginx_release(self):
        self.nginx_settings.release = Prompts.get_nginx_release()

    def ask_enable_nginx_for_core(self):
        self.nginx_settings.protect_core = Prompts.ask_enable_nginx(service="CORE")

    def ask_enable_nginx_for_gateway(self):
        self.nginx_settings.protect_gateway = Prompts.ask_enable_nginx(service="GATEWAY")
