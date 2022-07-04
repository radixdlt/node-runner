from urllib.parse import urlparse

from config.BaseConfig import BaseConfig, SetupMode
from utils.Prompts import Prompts
from utils.utils import Helpers, run_shell_command, bcolors


class CommonMonitoringSettings(BaseConfig):
    docker_compose_file = f"{Helpers.get_default_monitoring_config_dir()}/node-monitoring.yml"
    config_dir = Helpers.get_default_monitoring_config_dir()


class PrometheusSettings(BaseConfig):
    metrics_path = "/metrics"
    metrics_target = "localhost"
    basic_auth_password = None
    basic_auth_user = None
    scheme = "https"

    def ask_prometheus_target(self, basic_auth_password, target_name):
        self.metrics_target = f"{Helpers.get_node_host_ip()}"
        if "DETAILED" in SetupMode.instance().mode:
            url = Prompts.ask_metrics_target_details(target_name, f"https://{self.metrics_target}")
            self.set_target_details(url, target_name)

        elif self.scheme == "https":
            self.basic_auth_user = "metrics"
            if not basic_auth_password:
                self.basic_auth_password = Prompts.ask_basic_auth_password(self.basic_auth_user, target_name)
            else:
                self.basic_auth_password = basic_auth_password

    def set_target_details(self, url, target_name):
        parsed_url = urlparse(url)
        self.scheme = parsed_url.scheme
        self.metrics_target = f"{parsed_url.hostname}:{parsed_url.port}" if parsed_url.port else f"{parsed_url.hostname}"
        if parsed_url.scheme == "https":
            auth = Prompts.get_basic_auth(target_name, "metrics")
            self.basic_auth_password = auth["password"]
            self.basic_auth_user = auth["name"]


class MonitoringSettings(BaseConfig):
    core_prometheus_settings: PrometheusSettings = PrometheusSettings({})
    gateway_api_prometheus_settings: PrometheusSettings = PrometheusSettings({})
    aggregator_prometheus_settings: PrometheusSettings = PrometheusSettings({})
    common_settings: CommonMonitoringSettings = CommonMonitoringSettings({})

    def configure_core_target(self, basic_auth_password):
        self.core_prometheus_settings.ask_prometheus_target(basic_auth_password, target_name="CORE_NODE")
        self.core_prometheus_settings.metrics_path = "/prometheus/metrics"

    def configure_gateway_api_target(self, basic_auth_password):
        self.gateway_api_prometheus_settings.ask_prometheus_target(basic_auth_password, target_name="GATEWAY_API")
        self.gateway_api_prometheus_settings.metrics_path = "/gateway/metrics"

    def configure_aggregator_target(self, basic_auth_password):
        self.aggregator_prometheus_settings.ask_prometheus_target(basic_auth_password, target_name="AGGREGATOR")
        self.aggregator_prometheus_settings.metrics_path = "/aggregator/metrics"
