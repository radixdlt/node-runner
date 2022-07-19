from pathlib import Path
from urllib.parse import urlparse

from config.BaseConfig import BaseConfig, SetupMode
from github import github
from utils.Prompts import Prompts
from utils.utils import Helpers


class PostGresSettings(BaseConfig):
    user: str = "postgres"
    password: str = None
    dbname: str = "radixdlt_ledger"
    setup: str = "local"
    host: str = "host.docker.internal:5432"

    def ask_postgress_settings(self, postgress_password):
        Helpers.section_headline("POSTGRES SETTINGS")
        if "DETAILED" in SetupMode.instance().mode:
            self.setup, self.host = Prompts.ask_postgress_location(self.host)
            self.user = Prompts.get_postgress_user()
            self.dbname = Prompts.get_postgress_dbname()
        if not postgress_password:
            self.password = Prompts.ask_postgress_password()
        else:
            self.password = postgress_password


class CoreApiNode(BaseConfig):
    Name = "Core"
    core_api_address = "http://core:3333"
    trust_weighting = 1
    request_weighting = 1
    enabled = "true"
    basic_auth_user = None
    basic_auth_password = None
    auth_header = None
    disable_core_api_https_certificate_checks: str = None

    def __iter__(self):
        class_variables = {key: value
                           for key, value in self.__class__.__dict__.items()
                           if not key.startswith('__') and not callable(value)}

        for attr, value in class_variables.items():
            if attr in ['auth_header'] and (self.basic_auth_user and self.basic_auth_password):
                yield attr, Helpers.get_basic_auth_header({
                    "name": self.basic_auth_user,
                    "password": self.basic_auth_password
                })
            elif self.__getattribute__(attr):
                yield attr, self.__getattribute__(attr)

    def ask_disablehttpsVerify(self):
        self.disable_core_api_https_certificate_checks = Prompts.get_disablehttpsVerfiy()


class DataAggregatorSetting:
    release: str = None
    repo: str = "radixdlt/ng-data-aggregator"
    restart: str = "unless-stopped"
    NetworkName: str = None
    coreApiNode: CoreApiNode = CoreApiNode({})

    def __init__(self, settings: dict):
        for key, value in settings.items():
            setattr(self, key, value)

    def ask_gateway_release(self):
        latest_gateway_release = github.latest_release("radixdlt/radixdlt-network-gateway")
        self.release = latest_gateway_release
        if "DETAILED" in SetupMode.instance().mode:
            self.release = Prompts.get_gateway_release("data_aggregator", latest_gateway_release)

    def ask_core_api_node_settings(self):
        if "DETAILED" in SetupMode.instance().mode:
            self.coreApiNode.core_api_address = Prompts.get_CoreApiAddress(self.coreApiNode.core_api_address)
            self.set_basic_auth(self.coreApiNode.core_api_address)
            self.coreApiNode.Name = Prompts.get_CopeAPINodeName(self.coreApiNode.Name)
            self.coreApiNode = self.coreApiNode

    def set_basic_auth(self, url):
        parsed_url = urlparse(url)
        if parsed_url.scheme == "https":
            auth = Prompts.get_basic_auth()
            self.coreApiNode.basic_auth_password = auth["password"]
            self.coreApiNode.basic_auth_user = auth["name"]
            self.coreApiNode.ask_disablehttpsVerify()

    def __iter__(self):
        class_variables = {key: value
                           for key, value in self.__class__.__dict__.items()
                           if not key.startswith('__') and not callable(value)}
        for attr, value in class_variables.items():
            if attr in ['postgresSettings', 'coreApiNode']:
                yield attr, dict(self.__getattribute__(attr))
            elif self.__getattribute__(attr):
                yield attr, self.__getattribute__(attr)


class GatewayAPIDockerSettings(BaseConfig):
    release: str = None
    repo: str = "radixdlt/ng-gateway-api"
    coreApiNode: CoreApiNode = CoreApiNode({})
    restart = "unless-stopped"
    enable_swagger = "true"
    max_page_size = "30"

    def ask_gateway_release(self):
        latest_gateway_release = github.latest_release("radixdlt/radixdlt-network-gateway")
        self.release = latest_gateway_release
        if "DETAILED" in SetupMode.instance().mode:
            self.release = Prompts.get_gateway_release("gateway_api", latest_gateway_release)

    def set_core_api_node_setings(self, coreApiNode: CoreApiNode):
        self.coreApiNode = coreApiNode

    def __iter__(self):
        class_variables = {key: value
                           for key, value in self.__class__.__dict__.items()
                           if not key.startswith('__') and not callable(value)}

        for attr, value in class_variables.items():
            if attr in ['coreApiNode']:
                yield attr, dict(self.__getattribute__(attr))
            elif self.__getattribute__(attr):
                yield attr, self.__getattribute__(attr)


class GatewayDockerSettings(BaseConfig):
    data_aggregator = DataAggregatorSetting({})
    gateway_api = GatewayAPIDockerSettings({})
    postgres_db = PostGresSettings({})

    def __iter__(self):
        class_variables = {key: value
                           for key, value in self.__class__.__dict__.items()
                           if not key.startswith('__') and not callable(value)}

        for attr, value in class_variables.items():
            if attr in ['data_aggregator', 'gateway_api', 'postgres_db']:
                yield attr, dict(self.__getattribute__(attr))
            elif self.__getattribute__(attr):
                yield attr, self.__getattribute__(attr)

    def create_config(self, postgress_password):
        self.data_aggregator.ask_core_api_node_settings()
        self.postgres_db.ask_postgress_settings(postgress_password)
        self.data_aggregator.ask_gateway_release()
        self.gateway_api.ask_gateway_release()
        self.gateway_api.set_core_api_node_setings(
            self.data_aggregator.coreApiNode)
        return self
