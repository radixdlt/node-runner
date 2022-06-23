import sys

import requests
import os
import os.path
from pathlib import Path

import yaml

from config.Renderer import Renderer
from env_vars import NODE_END_POINT, NODE_HOST_IP_OR_NAME, COMPOSE_HTTP_TIMEOUT
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
    def template_prometheus_yml(monitoring_config, monitoring_config_dir):
        render_template = Renderer().load_file_based_template("prometheus.yml.j2").render(monitoring_config).to_yaml()

        yaml.add_representer(type(None), Helpers.represent_none)

        Path(f"{monitoring_config_dir}/prometheus").mkdir(parents=True, exist_ok=True)
        prometheus_file_location = f"{monitoring_config_dir}/prometheus/prometheus.yml"
        Helpers.section_headline("Promtheus config is Generated as below")

        print(f"\n{yaml.dump(render_template)}"
              f"\n\n Saving to file {prometheus_file_location} ")

        with open(prometheus_file_location, 'w') as f:
            yaml.dump(render_template, f, default_flow_style=False, explicit_start=True, allow_unicode=True)

    @staticmethod
    def merge_auth_config(default_prometheus_yaml, node_ip):
        user = Helpers.get_nginx_user("metrics", "metrics")
        # TODO fix the issue where volumes array gets merged correctly
        scrape_config = yaml.safe_load(f"""
            scrape_configs:
              - job_name: mynode
                metrics_path: /prometheus/metrics
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
    def setup_datasource(default_datasource_cfg_url, monitoring_config_dir):
        req = requests.Request('GET', f'{default_datasource_cfg_url}')
        prepared = req.prepare()
        resp = Helpers.send_request(prepared, print_response=False)
        Path(f"{monitoring_config_dir}/grafana/provisioning/datasources").mkdir(parents=True, exist_ok=True)
        with open(f"{monitoring_config_dir}/grafana/provisioning/datasources/datasource.yml", 'wb') as f:
            f.write(resp.content)

    @staticmethod
    def template_datasource(monitoring_config_dir):
        render_template = Renderer().load_file_based_template("datasource.yml.j2").render({}).to_yaml()
        Path(f"{monitoring_config_dir}/grafana/provisioning/datasources").mkdir(parents=True, exist_ok=True)
        file_location = f"{monitoring_config_dir}/grafana/provisioning/datasources/datasource.yml"
        Helpers.section_headline("Downloading datasource for grafana")
        Helpers.dump_rendered_template(render_template, file_location)

    @staticmethod
    def setup_dashboard(default_dashboard_cfg_url, files, monitoring_config_dir):
        for file in files:
            req = requests.Request('GET', f'{default_dashboard_cfg_url}/{file}')
            prepared = req.prepare()
            resp = Helpers.send_request(prepared, print_response=False)
            Path(f"{monitoring_config_dir}/grafana/provisioning/dashboards").mkdir(parents=True, exist_ok=True)
            with open(f"{monitoring_config_dir}/grafana/provisioning/dashboards/{file}", 'wb') as f:
                f.write(resp.content)

    @staticmethod
    def template_dashboards(files, monitoring_config_dir):
        Helpers.section_headline("Downloading Dashboard files for grafana")

        Path(f"{monitoring_config_dir}/grafana/provisioning/dashboards").mkdir(parents=True, exist_ok=True)
        for file in files:
            render_template = Renderer().load_file_based_template(f"{file}.j2").render({}).to_yaml()
            file_location = f"{monitoring_config_dir}/grafana/provisioning/dashboards/{file}"
            if file.endswith('.yml') or file.endswith('.yaml'):
                Helpers.dump_rendered_template(render_template, file_location, quiet=True)
            if file.endswith('.json'):
                import json
                with open(file_location, 'w') as fp:
                    json.dump(render_template, fp)

    @staticmethod
    def setup_external_volumes():
        run_shell_command(["docker", "volume", "create", "prometheus_tsdb"])
        run_shell_command(["docker", "volume", "create", "grafana-storage"])

    @staticmethod
    def setup_monitoring_containers(default_monitoring_cfg_url, monitoring_config_dir):
        req = requests.Request('GET', f'{default_monitoring_cfg_url}')
        prepared = req.prepare()
        resp = Helpers.send_request(prepared, print_response=False)
        Path(monitoring_config_dir).mkdir(parents=True, exist_ok=True)
        with open(f"{monitoring_config_dir}/node-monitoring.yml", 'wb') as f:
            f.write(resp.content)

    @staticmethod
    def template_monitoring_containers(monitoring_config_dir):
        render_template = Renderer().load_file_based_template("node-monitoring.yml.j2").render({}).to_yaml()
        Path(monitoring_config_dir).mkdir(parents=True, exist_ok=True)
        file_location = f"{monitoring_config_dir}/node-monitoring.yml"
        Helpers.section_headline("Docker compose for monitoring containers")
        Helpers.dump_rendered_template(render_template, file_location)

    @staticmethod
    def start_monitoring(composefile, auto_approve=False):
        print(f"----- output of node monitoring docker compose file {composefile}")
        run_shell_command(f"cat {composefile}", shell=True)
        start_monitoring_answer = ""
        if auto_approve:
            print("In Auto mode -  Updating the monitoring as per above docker compose file")
        else:
            start_monitoring_answer = input(
                f"Do you want to start monitoring using file {composefile} [Y/n]?")
        if Helpers.check_Yes(start_monitoring_answer) or auto_approve:
            run_shell_command(f'docker-compose -f {composefile} up -d',
                              env={
                                  COMPOSE_HTTP_TIMEOUT: os.getenv(COMPOSE_HTTP_TIMEOUT, "200")
                              }, shell=True)
        else:
            print(f"""Exiting the command ..
                     Once you verified the file {composefile}, you can start the monitoring by running
                     $ radixnode monitoring start -f {composefile}
             """)

    @staticmethod
    def stop_monitoring(composefile, remove_volumes):
        Helpers.docker_compose_down(composefile, remove_volumes)
