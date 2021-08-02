import sys

import requests
import os
import os.path
from pathlib import Path

import yaml

from env_vars import NODE_END_POINT, NODE_HOST_IP_OR_NAME
from utils.utils import Helpers, run_shell_command


class Monitoring:

    @staticmethod
    def setup_prometheus_yml(default_prometheus_yaml_url):
        req = requests.Request('GET', f'{default_prometheus_yaml_url}')
        prepared = req.prepare()

        resp = Helpers.send_request(prepared, print_response=False)

        if not resp.ok:
            print(f" Errored downloading file {default_prometheus_yaml_url}. Exitting ... ")
            sys.exit()

        default_prometheus_yaml = yaml.safe_load(resp.content)
        prometheus_yaml = Monitoring.merge_auth_config(default_prometheus_yaml, Monitoring.get_node_host_ip())

        def represent_none(self, _):
            return self.represent_scalar('tag:yaml.org,2002:null', '')

        yaml.add_representer(type(None), represent_none)
        Path("monitoring/prometheus").mkdir(parents=True, exist_ok=True)

        with open("monitoring/prometheus/prometheus.yml", 'w') as f:
            yaml.dump(prometheus_yaml, f, default_flow_style=False, explicit_start=True, allow_unicode=True)

    @staticmethod
    def merge_auth_config(default_prometheus_yaml, node_ip):
        user = Helpers.get_nginx_user("metrics", "metrics")
        # TODO fix the issue where volumes array gets merged correctly
        scrape_config = yaml.safe_load(f"""
            scrape_configs:
              - job_name: mynode
                scheme: https
                basic_auth:
                  username: {user["name"]}
                  password: {user["password"]}
                tls_config:
                  insecure_skip_verify: true
                static_configs:
                  - targets:
                      - {node_ip}
           """)
        final_conf = Helpers.merge(scrape_config, default_prometheus_yaml)
        return final_conf

    @staticmethod
    def setup_datasource(default_datasource_cfg_url):
        req = requests.Request('GET', f'{default_datasource_cfg_url}')
        prepared = req.prepare()
        resp = Helpers.send_request(prepared, print_response=False)
        Path("monitoring/grafana/provisioning/datasources").mkdir(parents=True, exist_ok=True)
        with open("monitoring/grafana/provisioning/datasources/datasource.yml", 'wb') as f:
            f.write(resp.content)

    @staticmethod
    def setup_dashboard(default_dashboard_cfg_url, files):
        for file in files:
            req = requests.Request('GET', f'{default_dashboard_cfg_url}/{file}')
            prepared = req.prepare()
            resp = Helpers.send_request(prepared, print_response=False)
            Path("monitoring/grafana/provisioning/dashboards").mkdir(parents=True, exist_ok=True)
            with open(f"monitoring/grafana/provisioning/dashboards/{file}", 'wb') as f:
                f.write(resp.content)

    @staticmethod
    def setup_external_volumes():
        run_shell_command(["docker", "volume", "create", "prometheus_tsdb"])
        run_shell_command(["docker", "volume", "create", "grafana-storage"])

    @staticmethod
    def setup_monitoring_containers(default_monitoring_cfg_url):
        req = requests.Request('GET', f'{default_monitoring_cfg_url}')
        prepared = req.prepare()
        resp = Helpers.send_request(prepared, print_response=False)
        Path("monitoring").mkdir(parents=True, exist_ok=True)
        with open("monitoring/node-monitoring.yml", 'wb') as f:
            f.write(resp.content)

    @staticmethod
    def start_monitoring(composefile):
        print(f"----- output of node monitoring docker compose file {composefile}")
        run_shell_command(f"cat {composefile}", shell=True)
        start_monitoring_answer = input(
            f"Do you want to start monitoring using file {composefile} [Y/n]?")
        if Helpers.check_Yes(start_monitoring_answer):
            user = Helpers.get_nginx_user(usertype="metrics", default_username="metrics")
            node_endpoint = Monitoring.get_node_host_ip()
            run_shell_command(f'docker-compose -f {composefile} up -d',
                              env={
                                  "BASIC_AUTH_USER_CREDENTIALS": f'{user["name"]}:{user["password"]}',
                                  f"{NODE_END_POINT}": node_endpoint
                              }, shell=True)
        else:
            print(f"""Exiting the command ..
                     Once you verified the file {composefile}, you can start the monitoring by running
                     $ radixnode monitoring start -f {composefile}
             """)

    @staticmethod
    def get_node_host_ip():
        if os.environ.get('%s' % NODE_HOST_IP_OR_NAME) is None:
            print(
                f"{NODE_HOST_IP_OR_NAME} environment not setup. Fetching the IP of node assuming the monitoring is run on the same machine machine as "
                "the node.")
            ip = Helpers.get_public_ip()
            node_endpoint = f"{ip}"
        else:
            node_endpoint = os.environ.get(NODE_HOST_IP_OR_NAME)
        return node_endpoint

    @staticmethod
    def stop_monitoring(composefile, remove_volumes):
        Helpers.docker_compose_down(composefile, remove_volumes)

