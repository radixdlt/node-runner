from urllib.parse import urlparse

from utils.Prompts import Prompts
from utils.utils import Helpers


class PostGresSettings:
    postgres_user: str = None
    postgres_password: str = None
    postgres_dbname: str = "radixdlt_ledger"
    data_mount_path: str = None
    setup: str = None
    host: str = None

    def __init__(self, settings: dict):
        for key, value in settings.items():
            setattr(self, key, value)

    def __iter__(self):
        for attr, value in self.__dict__.items():
            yield attr, value

    def ask_postgress_settings(self):
        self.setup, self.data_mount_path, self.host = Prompts.ask_postgress_location()
        self.postgres_user = Prompts.get_postgress_user()
        self.postgres_password = Prompts.ask_postgress_password()
        self.postgres_dbname = Prompts.get_postgress_dbname()


class CoreApiNode:
    Name = None
    CoreApiAddress = None
    TrustWeighting = None
    RequestWeighting = None
    Enabled = None
    basic_auth_user = None
    basic_auth_password = None

    def __init__(self, settings: dict):
        for key, value in settings.items():
            setattr(self, key, value)

    def __iter__(self):
        for attr, value in self.__dict__.items():
            if attr in ['auth_header']:
                yield attr, Helpers.get_basic_auth_header({
                    "name": self.basic_auth_user,
                    "password": self.basic_auth_password
                })
            else:
                yield attr, value


class DataAggregatorSetting:
    release: str = None
    repo: str = "radixdlt/ng-data-aggregator"
    docker_image: str = None
    restart: str = "unless-stopped"
    PrometheusMetricsPort: str = "1234"
    DisableCoreApiHttpsCertificateChecks: str = None
    NetworkName: str = None
    coreApiNode: CoreApiNode = CoreApiNode({})

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
        if not coreApiNode.TrustWeighting:
            coreApiNode.TrustWeighting = Prompts.get_TrustWeighting()
        if not coreApiNode.RequestWeighting:
            coreApiNode.RequestWeighting = Prompts.get_RequestWeighting()
        if not coreApiNode.Enabled:
            coreApiNode.Enabled = Prompts.get_coreAPINodeEnabled()
        self.coreApiNode = coreApiNode

    def set_basic_auth(self, url):
        parsed_url = urlparse(url)
        if parsed_url.scheme == "https":
            auth = Prompts.get_basic_auth()
            self.coreApiNode.basic_auth_password = auth["password"]
            self.coreApiNode.basic_auth_user = auth["name"]
            self.set_disablehttpsVerify()

    def set_disablehttpsVerify(self):
        self.DisableCoreApiHttpsCertificateChecks = Prompts.get_disablehttpsVerfiy()

    def __iter__(self):
        for attr, value in self.__dict__.items():
            if attr in ['postgresSettings', 'coreApiNode']:
                yield attr, dict(value)
            else:
                yield attr, value


class GatewayAPIDockerSettings:
    release: str = None
    repo: str = "radixdlt/ng-gateway-api"
    docker_image: str = None
    NetworkName = None
    postgresSettings: PostGresSettings = PostGresSettings({})
    coreApiNode: CoreApiNode = CoreApiNode({})
    image = "radixdlt/ng-data-aggregator:1.1.2"
    restart = "unless-stopped"
    PrometheusMetricsPort = "1234"

    def ask_gateway_release(self):
        self.release = Prompts.get_gateway_release("gateway_api")
        self.docker_image = f"{self.repo}:{self.release}"

    def set_core_api_node_setings(self, coreApiNode: CoreApiNode):
        self.coreApiNode = coreApiNode

    def __iter__(self):
        for attr, value in self.__dict__.items():
            if attr in ['postgresSettings', 'coreApiNode']:
                yield attr, dict(value)
            else:
                yield attr, value


class GatewayDockerSettings:
    data_aggregator = DataAggregatorSetting()
    gateway_api = GatewayAPIDockerSettings()
    postgres_db = PostGresSettings({})
