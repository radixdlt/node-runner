from urllib.parse import urlparse

from config.BaseConfig import BaseConfig
from utils.Prompts import Prompts
from utils.utils import Helpers


class PostGresSettings(BaseConfig):
    user: str = None
    password: str = None
    dbname: str = "radixdlt_ledger"
    data_mount_path: str = None
    setup: str = None
    host: str = None

    def ask_postgress_settings(self):
        self.setup, self.data_mount_path, self.host = Prompts.ask_postgress_location()
        self.user = Prompts.get_postgress_user()
        self.password = Prompts.ask_postgress_password()
        self.dbname = Prompts.get_postgress_dbname()


class CoreApiNode(BaseConfig):
    Name = None
    CoreApiAddress = None
    TrustWeighting = 1
    RequestWeighting = 1
    Enabled = "true"
    basic_auth_user = None
    basic_auth_password = None
    auth_header = None
    DisableCoreApiHttpsCertificateChecks: str = None

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
        self.DisableCoreApiHttpsCertificateChecks = Prompts.get_disablehttpsVerfiy()


class DataAggregatorSetting:
    release: str = None
    repo: str = "radixdlt/ng-data-aggregator"
    docker_image: str = None
    restart: str = "unless-stopped"
    PrometheusMetricsPort: str = "1234"
    NetworkName: str = None
    coreApiNode: CoreApiNode = CoreApiNode({})

    def __init__(self, settings: dict):
        for key, value in settings.items():
            setattr(self, key, value)

    def ask_gateway_release(self):
        self.release = Prompts.get_gateway_release("data_aggregator")
        self.docker_image = f"{self.repo}:{self.release}"

    def ask_core_api_node_settings(self):
        coreApiNode = self.coreApiNode

        if not coreApiNode.CoreApiAddress:
            coreApiNode.CoreApiAddress = Prompts.get_CoreApiAddress()
            self.set_basic_auth(coreApiNode.CoreApiAddress)
        if not coreApiNode.Name:
            coreApiNode.Name = Prompts.get_CopeAPINodeName()
        self.coreApiNode = coreApiNode

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
    docker_image: str = None
    coreApiNode: CoreApiNode = CoreApiNode({})
    restart = "unless-stopped"
    PrometheusMetricsPort = "1234"
    EnableSwagger = "true"
    MaxPageSize = "30"

    def ask_gateway_release(self):
        self.release = Prompts.get_gateway_release("gateway_api")
        self.docker_image = f"{self.repo}:{self.release}"

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
