import os

from github import github
from utils.utils import Helpers, run_shell_command, bcolors


class Prompts:

    @staticmethod
    def check_default(answer, default):
        if answer == "":
            return default
        else:
            return answer

    @staticmethod
    def ask_postgress_password():
        answer = Helpers.input_guestion("\nPOSTGRES USER PASSWORD: Type in Postgress database password:")
        return answer

    @staticmethod
    def get_postgress_user():
        print("\nPOSTGRES USER: This is super admin user which is setup or going to be created if it is local setup.")
        answer = Helpers.input_guestion(
            "Default value for Postgres user is `postgres`. Press Enter to accept default"
            " or Type in Postgress username:")
        return Prompts.check_default(answer, "postgres")

    @staticmethod
    def ask_postgress_location():
        Helpers.section_headline("POSTGRES SETTINGS")
        print("\nGateway uses POSTGRES as a datastore. \nIt can be run as container on same machine "
              "(although not advised) as a local setup or use a remote managed POSTGRES.")
        answer = Helpers.input_guestion(
            "\nPress ENTER to use default value 'local' setup or type in 'remote': ")

        local_or_remote = Prompts.check_default(answer, 'local')
        if local_or_remote == "local":
            default_postgres_dir = f"{Helpers.get_home_dir()}/postgresdata"
            print(f"\nFor local setup which runs container, "
                  f"postgres data needs to be externally mounted from a folder.")
            postgres_mount = Helpers.input_guestion(
                f"\nPress Enter to store POSTGRES data on folder  \"{bcolors.OKBLUE}{default_postgres_dir}{bcolors.ENDC}\""
                f" Or type in the absolute path for the folder:")
            return "local", Prompts.check_default(postgres_mount, default_postgres_dir), "postgres_db:5432"

        else:
            hostname = input("\nFor the remote managed postgres, Enter the host name of server hosting postgress:")
            port = input("\nEnter the port the postgres process is listening on the server:")
            return "remote", None, f"{hostname}:{port}"

    @staticmethod
    def ask_postgress_volume_location():
        answer = input("")

    @staticmethod
    def get_postgress_dbname():
        answer = Helpers.input_guestion("\nPOSTGRES DB: Default value is 'radix-ledger'. "
                                        "Press Enter to accept default or type in Postgress database name:")
        return Prompts.check_default(answer, "radix-ledger")

    @staticmethod
    def get_CoreApiAddress():
        Helpers.section_headline("CORE API NODE DETAILS")
        print(
            "\nThis will be node either running locally or remote using which Gateway aggregator will stream ledger data"
            f"\nCORE API ADDRESS: Default settings use local node  and the default value is {bcolors.OKBLUE}http://core:3333{bcolors.ENDC} ")
        answer = Helpers.input_guestion(
            "Press ENTER to accept default Or Type in remote CoreApi "
            f"address in format of url like {bcolors.FAIL}http(s)://<host and port>:{bcolors.ENDC}")
        return Prompts.check_default(answer, 'http://core:3333')

    @staticmethod
    def get_CopeAPINodeName():
        print("\nNODE NAME: This can be any string and logs would refer this name on related info/errors")
        answer = Helpers.input_guestion(
            "Default value is 'core'. Press ENTER to accept default value or type in new name':")
        return Prompts.check_default(answer, 'core')

    @staticmethod
    def get_TrustWeighting():
        answer = input(
            "Type in TrustWeight settings. This is used by data_aggregator.  "
            "\nDefault is 1, press 'ENTER' to accept default:")
        return Prompts.check_default(answer, 1)

    @staticmethod
    def get_RequestWeighting():
        answer = input(
            "Type in RequestWeighting settings.This is used by gateway_api."
            "\nDefault is 1, press 'ENTER' to accept default:")
        return Prompts.check_default(answer, 1)

    @staticmethod
    def get_coreAPINodeEnabled():
        answer = input(
            "Is this node enabled for gateway. Press Enter to accept default as true [true/false]:")
        return Prompts.check_default(answer, "true")

    @staticmethod
    def get_basic_auth():
        print("Core API node is setup on different machine. It would require Nginx admin user and password.")
        admin = input(
            "Type in the username. Press 'ENTER' for default value 'admin':")
        password = input(
            "Type in the password:")
        return {"name": Prompts.check_default(admin, "admin"), "password": password}

    @staticmethod
    def get_disablehttpsVerfiy():
        answer = input(
            "If the core api node has self signed certificate, Press 'ENTER' to accept 'true'. otherwise type 'false' "
            "[true/false]:")
        return Prompts.check_default(answer, "true")

    @staticmethod
    def get_gateway_release(gateway_or_aggregator):
        latest_gateway_release = github.latest_release("radixdlt/radixdlt-network-gateway")
        Helpers.section_headline("GATEWAY RELEASE")

        print(f"Latest release for {gateway_or_aggregator} is {latest_gateway_release}")
        answer = input(
            f"Press Enter to accept the latest or  type in {gateway_or_aggregator} release tag:")
        return Prompts.check_default(answer, latest_gateway_release)

    @staticmethod
    def check_for_gateway():
        Helpers.section_headline("NETWORK GATEWAY SETTINGS")
        print(
            "\nFor more info on NETWORK GATEWAY refer https://docs.radixdlt.com/main/node-and-gateway/network-gateway.html"
            "\nDo you want to setup NETWORK GATEWAY on this machine? ")

        answer = Helpers.input_guestion("Default is No[N], Press ENTER to accept default or type in [Y/N]")
        return Helpers.check_Yes(Prompts.check_default(answer, "N"))

    @staticmethod
    def check_for_fullnode():
        Helpers.section_headline("FULL NODE")
        print(
            f"\nDo you want to setup a fullnode or a validator? For more information refer "
            "https://docs.radixdlt.com/main/node-and-gateway/node-introduction.html#_what_is_a_radix_node")
        answer = Helpers.input_guestion(
            "Default is Y to setup fullnode , Press ENTER to accept default or type in [Y/N]:")
        return Helpers.check_Yes(Prompts.check_default(answer, "Y"))

    @staticmethod
    def ask_enable_transaction():
        Helpers.section_headline("TRANSACTION API")
        print(
            "\nTransactions API on fullnodes are disabled. For it act as node that can stream transactions to a Gateway, it needs to be enabled."
            "\nTo enable this, it requires to be set to true,")
        answer = Helpers.input_guestion("\nPress 'ENTER' to accept 'false'. otherwise type 'true' [true/false]:")
        return Prompts.check_default(answer, "false")

    @staticmethod
    def ask_keyfile_path():
        Helpers.section_headline("KEYSTORE FILE")
        print(
            f"\nThe keystore file is the identity of the node and a very important file."
            f"\nIf you are planning to run a validator,  make sure you definitely backup this keystore file"
        )
        y_n = Helpers.input_guestion("\nDo you have a keystore file that you want to use [Y/N]?")
        if Helpers.check_Yes(Prompts.check_default(y_n, "N")):
            return input(
                f"{bcolors.WARNING}Enter the absolute path of the folder, just the folder, where the keystore file is located:{bcolors.ENDC}")
        else:
            radixnode_dir = f"{Helpers.get_home_dir()}/node-config"
            print(
                f"\nDefault folder location for Keystore file will be: {bcolors.OKBLUE}{radixnode_dir}{bcolors.ENDC}")
            answer = Helpers.input_guestion(
                'Press ENTER to accept default. otherwise enter the absolute path of the new folder:')
            # TODO this needs to moved out of init
            run_shell_command(f'mkdir -p {radixnode_dir}', shell=True, quite=True)
            return Prompts.check_default(answer, radixnode_dir)

    @staticmethod
    def ask_keyfile_name():
        default_keyfile_name = "node-keystore.ks"
        value = input(
            f"\n{bcolors.WARNING}Type in name of keystore file. Otherwise press 'Enter' to use default value '{default_keyfile_name}':{bcolors.ENDC}").strip()
        if value != "":
            keyfile_name = value
        else:
            keyfile_name = default_keyfile_name

        return keyfile_name

    @staticmethod
    def ask_trusted_node():
        input("Fullnode needs details another node to connect to network. "
              "\nTo connect to MAINNET details on these node can be found here "
              "- https://docs.radixdlt.com/main/node-and-gateway/cli-install-node-docker.html#_install_the_node"
              "\nType in the node you want to connect to")

    @staticmethod
    def ask_existing_compose_file(default_compose_file="radix-fullnode-compose.yml"):
        Helpers.section_headline("NEW or EXISTING SETUP")
        y_n = input(f"\n{bcolors.WARNING}Is this first time you running the node on this machine [Y/N]:{bcolors.ENDC}")
        if Helpers.check_Yes(y_n):
            return None
        else:
            prompt_answer = input(
                f"\nSo you have existing docker compose file. Is it in location '{bcolors.OKBLUE}{os.getcwd()}/{default_compose_file}{bcolors.ENDC}'?"
                f"\nIf so, press 'ENTER' or type in absolute path to file:")
            if prompt_answer == "":
                return f"{os.getcwd()}/{default_compose_file}"
            else:
                return prompt_answer

    @staticmethod
    def ask_enable_nginx(service='CORE'):
        Helpers.section_headline(f"NGINX SETUP FOR {service} NODE")
        print(f"\n {service} API can be protected by running Nginx infront of it.")
        answer = Helpers.input_guestion(
            "Default value is 'true' to enable it. "
            "Press Enter to accept default or type to choose [true/false]:")
        return Prompts.check_default(answer, "true")

    @staticmethod
    def get_nginx_release():
        latest_nginx_release = github.latest_release("radixdlt/radixdlt-nginx")
        Helpers.section_headline("NGINX CONFIG")
        print(f"Latest release of nginx is {bcolors.OKBLUE}{latest_nginx_release}{bcolors.ENDC}.")
        answer = Helpers.input_guestion(
            f"\nPress Enter to accept default or Type in radixdlt/radixdlt-nginx release tag:")
        return Prompts.check_default(answer, latest_nginx_release)
