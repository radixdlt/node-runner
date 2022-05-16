from config.DockerConfig import CommonDockerSettings
from utils.Prompts import Prompts
from urllib.parse import urlparse

from utils.utils import Helpers


class PostGresSettings:
    postgres_user: str = None
    postgres_password: str = None
    postgres_dbname: str = "radixdlt_ledger"

    def __init__(self, settings: dict):
        for key, value in settings.items():
            setattr(self, key, value)

    def __iter__(self):
        for attr, value in self.__dict__.items():
            yield attr, value


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
    release = None
    repo = "radixdlt/ng-data-aggregator"
    docker_image = None
    restart = "unless-stopped"
    PrometheusMetricsPort = "1234"
    DisableCoreApiHttpsCertificateChecks = None
    NetworkName = None
    postgresSettings: PostGresSettings = PostGresSettings({})
    coreApiNode: CoreApiNode = CoreApiNode({})

    def ask_gateway_release(self):
        self.release = Prompts.get_gateway_release()
        self.docker_image = f"{self.repo}:{self.release}"

    def ask_postgress_settings(self):
        postgresSettings = self.postgresSettings
        postgresSettings.postgres_user = Prompts.get_postgress_user()
        postgresSettings.postgres_password = Prompts.get_postgress_password()
        postgresSettings.postgres_dbname = Prompts.get_postgress_dbname()
        self.postgresSettings = postgresSettings

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
    NetworkName = None
    postgresSettings: PostGresSettings = PostGresSettings({})
    coreApiNode: CoreApiNode = CoreApiNode({})
    image = "radixdlt/ng-data-aggregator:1.1.2"
    restart = "unless-stopped"
    PrometheusMetricsPort = "1234"

    def set_core_api_node_setings(self, coreApiNode: CoreApiNode):
        self.coreApiNode = coreApiNode

    def set_postgress_settings(self, postgresSettings):
        self.postgresSettings = postgresSettings

    def __iter__(self):
        for attr, value in self.__dict__.items():
            if attr in ['postgresSettings', 'coreApiNode']:
                yield attr, dict(value)
            else:
                yield attr, value


class GatewayDockerSettings:
    data_aggregator = DataAggregatorSetting()
    gateway_api = GatewayAPIDockerSettings()
