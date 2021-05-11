from argparse import ArgumentParser
import os
import subprocess
import os.path
from pathlib import Path
import requests
import pprint, json
from requests.auth import HTTPBasicAuth
import urllib3
import getpass

urllib3.disable_warnings()

cli = ArgumentParser()
subparsers = cli.add_subparsers(dest="subcommand")
cwd = os.getcwd()


def argument(*name_or_flags, **kwargs):
    return list(name_or_flags), kwargs


def subcommand(args=[], parent=subparsers):
    def decorator(func):
        parser = parent.add_parser(func.__name__.replace("_", "-"), description=func.__doc__)
        for arg in args:
            parser.add_argument(*arg[0], **arg[1])
        parser.set_defaults(func=func)

    return decorator


def cli_version():
    return "test-version"


def printCommand(cmd):
    print('-----------------------------')
    if type(cmd) is list:
        print('Running command :' + ' '.join(cmd))
        print('-----------------------------')
    else:
        print('Running command ' + cmd)
        print('-----------------------------')


def run_shell_command(cmd, env=None, shell=False, fail_on_error=True, quite=False):
    printCommand(cmd)
    if env:
        result = subprocess.run(cmd, env=env, shell=shell)
    else:
        result = subprocess.run(cmd, shell=shell)
    if fail_on_error and result.returncode != 0:
        print("""
            Command failed. Exiting...
        """)
        quit()
    return result


class Base:
    @staticmethod
    def install_dependecies():
        run_shell_command(['sudo', 'apt', 'update'])
        run_shell_command(['sudo', 'apt', 'install', 'docker.io'])
        run_shell_command(['sudo', 'apt', 'install', 'wget', 'unzip'])
        run_shell_command(['sudo', 'apt', 'install', 'docker-compose'])
        run_shell_command(['sudo', 'apt', 'install', 'rng-tools'])
        run_shell_command(['sudo', 'rngd', '-r', '/dev/random'])

    @staticmethod
    def add_user_docker_group():

        run_shell_command(['sudo', 'groupadd', 'docker'], fail_on_error=False)
        is_in_docker_group = run_shell_command('groups | grep docker', shell=True, fail_on_error=False)
        if is_in_docker_group.returncode != 0:
            run_shell_command(['sudo', 'usermod', '-aG', 'docker', os.environ.get('USER')])
            print('Exit ssh login and relogin back for user addition to group "docker" to take effect')

    @staticmethod
    def fetch_universe_json(trustenode, extraction_path="."):
        run_shell_command(
            ['wget', '--no-check-certificate', '-O', f'{extraction_path}/universe.json',
             'https://' + trustenode + '/universe.json'])

    @staticmethod
    def generatekey(keyfile_path, keyfile_name="validator.ks"):
        print('-----------------------------')
        if os.path.isfile(f'{keyfile_path}/validator.ks'):
            print("Node key file already exist")
            keystore_password = getpass.getpass("Enter the password of the existing keystore file 'validator.ks':")
        else:
            print(f"""
            Generating new keystore file. Don't forget to backup the key from location {keyfile_path}/validator.ks
            """)
            keystore_password = getpass.getpass("Enter the password of the new file 'validator.ks':")
            run_shell_command(['docker', 'run', '--rm', '-v', keyfile_path + ':/keygen/key',
                               'radixdlt/keygen:1.0-beta.31',
                               '--keystore=/keygen/key/validator.ks',
                               '--password=' + keystore_password], quite=True
                              )
            run_shell_command(['sudo', 'chmod', '644', f'{keyfile_path}/validator.ks'])

        return keystore_password


class Docker(Base):

    @staticmethod
    def setup_nginx_Password():
        print('-----------------------------')
        print('Setting up nginx')
        nginx_password = getpass.getpass("Enter your nginx password: ")
        run_shell_command(['docker', 'run', '--rm', '-v',
                           os.getcwd().rsplit('/', 1)[-1] + '_nginx_secrets:/secrets',
                           'radixdlt/htpasswd:v1.0.0',
                           'htpasswd', '-bc', '/secrets/htpasswd.admin', 'admin', nginx_password])
        print(
            """
            Setup NGINX_ADMIN_PASSWORD environment variable using below command . Replace the string 'nginx_password_of_your_choice' with your password

            echo 'export NGINX_ADMIN_PASSWORD="nginx_password_of_your_choice"' >> ~/.bashrc
            """)
        return nginx_password

    @staticmethod
    def run_docker_compose_up(keystore_password, composefile, trustednode):
        run_shell_command(['docker-compose', '-f', composefile, 'up', '-d'],
                          env={
                              "RADIXDLT_NETWORK_NODE": trustednode,
                              "RADIXDLT_NODE_KEY_PASSWORD": keystore_password
                          })

    @staticmethod
    def fetchComposeFile(composefileurl):
        run_shell_command(['wget', '-O', composefileurl.rsplit('/', 1)[-1], composefileurl])

    @staticmethod
    def run_docker_compose_down(composefile, removevolumes):
        Helpers.docker_compose_down(composefile, removevolumes)


class SystemD(Base):

    @staticmethod
    def install_java():
        run_shell_command('sudo apt install -y openjdk-11-jdk', shell=True)

    @staticmethod
    def setup_user():
        user_exists = run_shell_command("cat /etc/passwd | grep radixdlt", shell=True, fail_on_error=False)
        if user_exists.returncode != 0:
            run_shell_command('sudo useradd -m -s /bin/bash radixdlt ', shell=True)
        run_shell_command(['sudo', 'usermod', '-aG', 'docker', 'radixdlt'])

    @staticmethod
    def create_service_user_password():
        run_shell_command('sudo passwd radixdlt', shell=True)

    @staticmethod
    def sudoers_instructions():
        print("""
            1. Execute following setups so that radixdlt user can use sudo commands without password
            
                $ sudo su 
                
                $ echo "radixdlt ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/radixdlt
        """)
        print("""
            2. After the above step logout.
             Then login using account radixdlt and the password you setup just now. To login using password, you need to enable it in /etc/ssh/sshd_config.
             Instead, we suggest, for you to setup password less ssh login by copying the public key to
             /home/radixdlt/.ssh/authorized_keys
            3. Also copy the nodecli.py to the home directory of radixdlt (/home/radixdlt)
        """)

    @staticmethod
    def make_etc_directory():
        run_shell_command('sudo mkdir -p /etc/radixdlt/', shell=True)
        run_shell_command('sudo chown radixdlt:radixdlt -R /etc/radixdlt', shell=True)

    @staticmethod
    def make_data_directory():
        run_shell_command('sudo mkdir -p /data', shell=True)
        run_shell_command('sudo chown radixdlt:radixdlt /data', shell=True)

    @staticmethod
    def generatekey(keyfile_path, keyfile_name="validator.ks"):
        run_shell_command(f'mkdir -p {keyfile_path}', shell=True)
        keystore_password = Base.generatekey(keyfile_path)
        return keystore_password

    @staticmethod
    def fetch_universe_json(trustenode, extraction_path):
        Base.fetch_universe_json(trustenode, extraction_path)

    @staticmethod
    def set_environment_variables(keystore_password, node_secrets_dir):
        command = f"""
        cat > {node_secrets_dir}/environment << EOF
        JAVA_OPTS="-server -Xms2g -Xmx2g -XX:+HeapDumpOnOutOfMemoryError -Djavax.net.ssl.trustStore=/etc/ssl/certs/java/cacerts -Djavax.net.ssl.trustStoreType=jks -Djava.security.egd=file:/dev/urandom -Dcom.sun.management.jmxremote.port=9010 -DLog4jContextSelector=org.apache.logging.log4j.core.async.AsyncLoggerContextSelector -Dcom.sun.management.jmxremote.rmi.port=9010 -Dcom.sun.management.jmxremote.authenticate=false -Dcom.sun.management.jmxremote.ssl=false -Djava.rmi.server.hostname=core -agentlib:jdwp=transport=dt_socket,address=50505,suspend=n,server=y"
        RADIX_NODE_KEYSTORE_PASSWORD={keystore_password}
        """
        run_shell_command(command, shell=True)

    @staticmethod
    def setup_default_config(trustednode, hostip, node_dir):
        command = f"""
        cat > {node_dir}/default.config << EOF
            ntp=false
            ntp.pool=pool.ntp.org
            universe.location=/etc/radixdlt/node/universe.json
            node.key.path=/etc/radixdlt/node/secrets/validator.ks
            network.tcp.listen_port=30001
            network.tcp.broadcast_port=30000
            network.seeds={trustednode}:30000
            host.ip={hostip}
            db.location=/data
            node_api.port=3334
            client_api.enable=false
            client_api.port=8081
            log.level=debug
        """
        run_shell_command(command, shell=True)

    @staticmethod
    def setup_service_file(node_version_dir, node_dir="/etc/radixdlt/node",
                           node_secrets_path="/etc/radixdlt/node/secrets", ):

        command = f"""
        sudo cat > /etc/systemd/system/radixdlt-node.service << EOF
            [Unit]
            Description=Radix DLT Validator
            After=local-fs.target
            After=network-online.target
            After=nss-lookup.target
            After=time-sync.target
            After=systemd-journald-dev-log.socket
            Wants=network-online.target
            
            [Service]
            EnvironmentFile={node_secrets_path}/environment
            User=radixdlt
            WorkingDirectory={node_dir}
            ExecStart={node_dir}/{node_version_dir}/bin/radixdlt
            SuccessExitStatus=143
            TimeoutStopSec=10
            Restart=on-failure
            
            [Install]
            WantedBy=multi-user.target
        """
        run_shell_command(command, shell=True)

    @staticmethod
    def download_binaries(binarylocationUrl, node_dir, node_version):
        run_shell_command(
            ['wget', '--no-check-certificate', '-O', 'radixdlt-dist.zip', binarylocationUrl])
        run_shell_command('unzip radixdlt-dist.zip', shell=True)
        run_shell_command(f'mkdir -p {node_dir}/{node_version}', shell=True)
        run_shell_command(f'mv radixdlt-{node_version}/* {node_dir}/{node_version}', shell=True)

    @staticmethod
    def start_node_service():
        run_shell_command('sudo chown radixdlt:radixdlt -R /etc/radixdlt', shell=True)
        run_shell_command('sudo systemctl start radixdlt-node.service', shell=True)
        run_shell_command('sudo systemctl enable radixdlt-node.service', shell=True)

    @staticmethod
    def install_nginx():
        run_shell_command('sudo apt install -y nginx apache2-utils', shell=True)
        run_shell_command('sudo rm -rf /etc/nginx/{sites-available,sites-enabled}', shell=True)

    @staticmethod
    def setup_nginx_config(nginx_config_location_Url, node_type, nginx_etc_dir):
        run_shell_command(
            ['wget', '--no-check-certificate', '-O', 'radixdlt-nginx.zip', nginx_config_location_Url])
        run_shell_command(f'sudo unzip radixdlt-nginx.zip -d {nginx_etc_dir}', shell=True)
        run_shell_command(f'sudo mv {nginx_etc_dir}/nginx-{node_type}.conf  /etc/nginx/nginx.conf', shell=True)
        run_shell_command(f'sudo mkdir -p /var/cache/nginx/radixdlt-hot', shell=True)

    @staticmethod
    def create_ssl_certs(secrets_dir):

        if os.path.isfile(f'{secrets_dir}/server.key') and os.path.isfile(f'{secrets_dir}/server.pem'):
            print(f"Files  {secrets_dir}/server.key and os.path.isfile(f'{secrets_dir}/server.pem already exists")
            answer = input("Do you want to regenerate y/n :")
            if answer == "y":
                run_shell_command(f"""
                     sudo openssl req  -nodes -new -x509 -nodes -subj '/CN=localhost' \
                      -keyout "{secrets_dir}/server.key" \
                      -out "{secrets_dir}/server.pem"
                     """, shell=True)
        else:
            run_shell_command(f"""
                 sudo openssl req  -nodes -new -x509 -nodes -subj '/CN=localhost' \
                  -keyout "{secrets_dir}/server.key" \
                  -out "{secrets_dir}/server.pem"
            """, shell=True)

        if os.path.isfile(f'{secrets_dir}/dhparam.pem'):
            print(f"File {secrets_dir}/dhparam.pem already exists")
            answer = input("Do you want to regenerate y/n :")
            if answer == "y":
                run_shell_command(f"sudo openssl dhparam -out {secrets_dir}/dhparam.pem  4096", shell=True)
        else:
            print("Generating a dhparam.pem file")
            run_shell_command(f"sudo openssl dhparam -out {secrets_dir}/dhparam.pem  4096", shell=True)

    @staticmethod
    def setup_nginx_password(secrets_dir):
        run_shell_command(f'sudo mkdir -p {secrets_dir}', shell=True)
        print('-----------------------------')
        print('Setting up nginx')
        run_shell_command(f'sudo touch {secrets_dir}/htpasswd.admin', fail_on_error=True, shell=True)
        run_shell_command(f'sudo htpasswd -c {secrets_dir}/htpasswd.admin admin', shell=True)
        print(
            """
            Setup NGINX_ADMIN_PASSWORD environment variable using below command . Replace the string 'nginx_password_of_your_choice' with your password

            $ echo 'export NGINX_ADMIN_PASSWORD="nginx_password_of_your_choice"' >> ~/.bashrc
            $ source ~/.bashrc
            """)

    @staticmethod
    def start_nginx_service():
        run_shell_command(f'sudo systemctl start nginx', shell=True)
        run_shell_command('sudo systemctl enable nginx', shell=True)
        run_shell_command('sudo systemctl restart nginx', shell=True)

    @staticmethod
    def checkUser():
        result = run_shell_command(f'whoami | grep radixdlt', shell=True)
        if result.returncode != 0:
            print(" You are not logged as radixdlt user. Logout and login as radixdlt user")
            quit()
        else:
            print("User on the terminal is radixdlt")

    @staticmethod
    def create_initial_service_file():
        run_shell_command("sudo touch /etc/systemd/system/radixdlt-node.service", shell=True)
        run_shell_command("sudo chown radixdlt:radixdlt /etc/systemd/system/radixdlt-node.service", shell=True)


class Helpers:
    @staticmethod
    def is_json(myjson):
        try:
            json_object = json.loads(myjson)
        except ValueError as e:
            return False
        return True

    @staticmethod
    def pretty_print_request(req):
        print('{}\n{}\r\n{}\r\n\r\n{}\n{}'.format(
            '-----------Request-----------',
            req.method + ' ' + req.url,
            '\r\n'.join('{}: {}'.format(k, v) for k, v in req.headers.items()),
            req.body,
            '-------------------------------'
        ))

    @staticmethod
    def send_request(prepared, print_request=False, print_response=True):
        if print_request:
            Helpers.pretty_print_request(prepared)
        s = requests.Session()
        resp = s.send(prepared, verify=False)
        if Helpers.is_json(resp.content):
            print(json.dumps(resp.json()))
        else:
            print(resp.content)
        return resp.content

    @staticmethod
    def get_nginx_user():
        nginx_admin_password = 'NGINX_ADMIN_PASSWORD'
        if os.environ.get('%s' % nginx_admin_password) is None:
            print("""
            ------
            NGINX_ADMIN_PASSWORD is missing !
            Setup NGINX_ADMIN_PASSWORD environment variable using below command . Replace the string 'nginx_password_of_your_choice' with your password

            echo 'export NGINX_ADMIN_PASSWORD="nginx_password_of_your_choice"' >> ~/.bashrc
            """)
            quit()
        else:
            return dict({
                "name": "admin",
                "password": os.environ.get("%s" % nginx_admin_password)
            })

    @staticmethod
    def docker_compose_down(composefile, remove_volumes):
        command = ['docker-compose', '-f', composefile, 'down']
        if remove_volumes:
            command.append('-v')
        run_shell_command(command)

    @staticmethod
    def get_public_ip():
        return requests.get('https://api.ipify.org').text


@subcommand([])
def version(args):
    print(f"Cli - Version : {cli_version()}")


@subcommand([
    argument("-f", "--composefileurl", required=True, help="URl to download the docker compose file ", action="store"),
    argument("-t", "--trustednode", required=True, help="Trusted node on radix network", action="store"),
])
def start_docker(args):
    Docker.fetchComposeFile(args.composefileurl)
    keystore_password = Base.generatekey(keyfile_path=str(Path(__file__).parent.absolute()))
    Base.fetch_universe_json(args.trustednode)
    Docker.run_docker_compose_up(keystore_password, args.composefileurl.rsplit('/', 1)[-1], args.trustednode)


@subcommand([
    argument("-b", "--nodebinaryUrl", required=True, help="URL to download radix node binaries", action="store"),
    argument("-c", "--nginxconfigUrl", required=True, help="URL to nginx config", action="store"),
    argument("-t", "--trustednode", required=True, help="Trusted node on radix network", action="store"),
    argument("-n", "--nodetype", required=True, help="Type of node archive or fullnode", action="store"),
    argument("-i", "--hostip", required=True, help="Static Public IP of the node", action="store"),
])
def start_systemd(args):
    node_dir = '/etc/radixdlt/node'
    nginx_dir = '/etc/nginx'
    nginx_secrets_dir = f"{nginx_dir}/secrets"
    node_secrets_dir = f"{node_dir}/secrets"
    SystemD.checkUser()
    keystore_password = SystemD.generatekey(node_secrets_dir)
    SystemD.fetch_universe_json(args.trustednode, node_dir)
    SystemD.set_environment_variables(keystore_password, node_secrets_dir)
    SystemD.setup_default_config(trustednode=args.trustednode, hostip=args.hostip, node_dir=node_dir)
    node_version = args.nodebinaryUrl.rsplit('/', 2)[-2]
    SystemD.setup_service_file(node_version)

    SystemD.download_binaries(args.nodebinaryUrl, node_dir=node_dir, node_version=node_version)
    SystemD.setup_nginx_config(nginx_config_location_Url=args.nginxconfigUrl, node_type=args.nodetype,
                               nginx_etc_dir=nginx_dir)
    SystemD.create_ssl_certs(nginx_secrets_dir)
    SystemD.start_node_service()
    SystemD.start_nginx_service()


@subcommand([
    argument("-f", "--composefile", required=True, help="The name of compose file ", action="store"),
    argument("-v", "--removevolumes", help="Remove the volumes ", action="store_true"),
])
def stop_docker(args):
    if args.removevolumes:
        print(
            """ 
            Removing volumes including Nginx volume. Nginx password needs to be recreated again when you bring node up
            """)
    Docker.run_docker_compose_down(args.composefile, args.removevolumes)


@subcommand([])
def configure_docker(args):
    Base.install_dependecies()
    Base.add_user_docker_group()


@subcommand([])
def configure_systemd(args):
    Base.install_dependecies()
    SystemD.install_java()
    SystemD.setup_user()
    SystemD.make_etc_directory()
    SystemD.make_data_directory()
    SystemD.create_service_user_password()
    SystemD.create_initial_service_file()
    SystemD.sudoers_instructions()


@subcommand(
    [argument("-m", "--setupmode", required=True, help="Setup type whether it is DOCKER or SYSTEMD", action="store")])
def admin_password(args):
    if args.setupmode == "DOCKER":
        Docker.setup_nginx_Password()
    if args.setupmode == "SYSTEMD":
        SystemD.checkUser()
        SystemD.install_nginx()
        SystemD.setup_nginx_password("/etc/nginx/secrets")


"""
  Below is the list of API commands 
"""


@subcommand()
def nodeaddress(args):
    node_host = 'localhost'
    user = Helpers.get_nginx_user()
    req = requests.Request('GET',
                           f'https://{node_host}/node',
                           auth=HTTPBasicAuth(user["name"], user["password"]))
    prepared = req.prepare()
    Helpers.send_request(prepared)


@subcommand()
def peers(args):
    node_host = 'localhost'
    user = Helpers.get_nginx_user()
    req = requests.Request('GET',
                           f'https://{node_host}/system/peers',
                           auth=HTTPBasicAuth(user["name"], user["password"]))
    prepared = req.prepare()
    Helpers.send_request(prepared)


@subcommand()
def registervalidator(args):
    node_host = 'localhost'
    user = Helpers.get_nginx_user()
    validator_name = input("Name of your validator:")
    validator_url = input("Url of your validator:")
    data = f"""
    {{"actions":
        [
        {{"action":"RegisterValidator",
        "params":{{
            "name": "{validator_name}",
            "url": "{validator_url}"
            }}
        }}
        ]
    }}
    """
    req = requests.Request('POST',
                           f'https://{node_host}/node/execute',
                           data=data,
                           auth=HTTPBasicAuth(user["name"], user["password"]))
    prepared = req.prepare()

    # prepared.body = json.dumps(u"""%s""" % data)
    prepared.headers['Content-Type'] = 'application/json'
    Helpers.send_request(prepared)


@subcommand()
def showvalidator(args):
    node_host = 'localhost'
    user = Helpers.get_nginx_user()
    req = requests.Request('POST',
                           f'https://{node_host}/node/validator',
                           auth=HTTPBasicAuth(user["name"], user["password"]))
    prepared = req.prepare()

    prepared.headers['Content-Type'] = 'application/json'
    Helpers.send_request(prepared)


@subcommand()
def systeminfo(args):
    node_host = 'localhost'
    user = Helpers.get_nginx_user()
    req = requests.Request('GET',
                           f'https://{node_host}/system/info',
                           auth=HTTPBasicAuth(user["name"], user["password"]))
    prepared = req.prepare()

    prepared.headers['Content-Type'] = 'application/json'
    Helpers.send_request(prepared)


@subcommand()
def setup_monitoring(args):
    monitor_url_dir = f'https://raw.githubusercontent.com/radixdlt/node-runner/{cli_version()}/monitoring'
    Monitoring.setup_prometheus_yml(f"{monitor_url_dir}/prometheus/prometheus.yml")
    Monitoring.setup_datasource(f"{monitor_url_dir}/grafana/provisioning/datasources/datasource.yml")
    Monitoring.setup_dashboard(f"{monitor_url_dir}/grafana/provisioning/dashboards/",
                               ["dashboard.yml", "sample-node-dashboard.json"])
    Monitoring.setup_monitoring_containers(f"{monitor_url_dir}/node-monitoring.yml")
    Monitoring.setup_external_volumes()
    Monitoring.start_monitoring(f"monitoring/node-monitoring.yml")


@subcommand([argument("-v", "--removevolumes", help="Remove the volumes ", action="store_true")])
def stop_monitoring(args):
    Monitoring.stop_monitoring(f"monitoring/node-monitoring.yml", args.removevolumes)


class Monitoring():

    @staticmethod
    def setup_prometheus_yml(default_prometheus_yaml_url):
        req = requests.Request('GET', f'{default_prometheus_yaml_url}')
        prepared = req.prepare()

        content = Helpers.send_request(prepared, print_response=False)
        Path("monitoring/prometheus").mkdir(parents=True, exist_ok=True)
        with open("monitoring/prometheus/prometheus.yml", 'wb') as f:
            f.write(content)

    @staticmethod
    def setup_datasource(default_datasource_cfg_url):
        req = requests.Request('GET', f'{default_datasource_cfg_url}')
        prepared = req.prepare()
        content = Helpers.send_request(prepared, print_response=False)
        Path("monitoring/grafana/provisioning/datasources").mkdir(parents=True, exist_ok=True)
        with open("monitoring/grafana/provisioning/datasources/datasource.yml", 'wb') as f:
            f.write(content)

    @staticmethod
    def setup_dashboard(default_dashboard_cfg_url, files):
        for file in files:
            req = requests.Request('GET', f'{default_dashboard_cfg_url}/{file}')
            prepared = req.prepare()
            content = Helpers.send_request(prepared, print_response=False)
            Path("monitoring/grafana/provisioning/dashboards").mkdir(parents=True, exist_ok=True)
            with open(f"monitoring/grafana/provisioning/dashboards/{file}", 'wb') as f:
                f.write(content)

    @staticmethod
    def setup_external_volumes():
        run_shell_command(["docker", "volume", "create", "prometheus_tsdb"])
        run_shell_command(["docker", "volume", "create", "grafana-storage"])

    @staticmethod
    def setup_monitoring_containers(default_monitoring_cfg_url):
        req = requests.Request('GET', f'{default_monitoring_cfg_url}')
        prepared = req.prepare()
        content = Helpers.send_request(prepared, print_response=False)
        Path("monitoring").mkdir(parents=True, exist_ok=True)
        with open("monitoring/node-monitoring.yml", 'wb') as f:
            f.write(content)

    @staticmethod
    def start_monitoring(composefile):
        user = Helpers.get_nginx_user()
        node_endpoint_env = "NODE_END_POINT"
        if os.environ.get('%s' % node_endpoint_env) is None:
            ip = Helpers.get_public_ip()
            node_endpoint = f"https://{ip}"
        else:
            node_endpoint = os.environ.get(node_endpoint_env)
        run_shell_command(f'docker-compose -f {composefile} up -d',
                          env={
                              "BASIC_AUTH_USER_CREDENTIALS": f'{user["name"]}:{user["password"]}',
                              "NODE_END_POINT": node_endpoint
                          }, shell=True)

    @staticmethod
    def stop_monitoring(composefile, remove_volumes):
        Helpers.docker_compose_down(composefile, remove_volumes)


if __name__ == "__main__":
    args = cli.parse_args()
    if args.subcommand is None:
        cli.print_help()
    else:
        args.func(args)
