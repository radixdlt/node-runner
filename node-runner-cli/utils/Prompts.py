import os

from utils.utils import Helpers, run_shell_command


class Prompts:

    @staticmethod
    def check_default(answer, default):
        if answer == "":
            return default
        else:
            return answer

    @staticmethod
    def ask_postgress_password():
        answer = input("\nPOSTGRES USER PASSWORD: Type in Postgress database password:")
        return answer

    @staticmethod
    def get_postgress_user():
        answer = input("\nPOSTGRES USER: Default value for Postgres user is `postgres`. Press Enter to accept default"
                       " or Type in Postgress username:")
        return Prompts.check_default(answer, "postgres")

    @staticmethod
    def ask_postgress_location():
        answer = input(
            "\n------ POSTGRES settings for Gateway ----\n"
            "\nGateway uses POSTGRES as a datastore. \nIt can be run as container on same machine "
            "(although not advised) or use a remote managed POSTGRES."
            "\nPress ENTER to use default 'local' setup or type in 'remote': ")
        local_or_remote = Prompts.check_default(answer, 'local')
        if local_or_remote == "local":
            default_postgres_dir = f"{Helpers.get_home_dir()}/postgresdata"
            postgres_mount = input(f"\nFor local setup which runs container, "
                                   f"postgres data needs to be externally mounted from a folder."
                                   f"\nPress Enter to store POSTGRES data on folder  \"{default_postgres_dir}\""
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
        answer = input("\nPOSTGRES DB: Default value is 'radix-ledger'. "
                       "Press Enter to accept default or type in Postgress database name:")
        return Prompts.check_default(answer, "radix-ledger")

    @staticmethod
    def get_CoreApiAddress():
        answer = input("\n------ Core API to read Transactions ----\n"
                       "\nThis will be node either running locally or remote. "
                       "\nDefault settings use local node  and the default value is `http://core:3333`. "
                       "Press ENTER to accept default Or Type in remote CoreApi "
                       "address in format of url like http(s)://<host and port>:")
        return Prompts.check_default(answer, 'http://core:3333')

    @staticmethod
    def get_CopeAPINodeName():
        answer = input(
            "\nNODE NAME: This can be any string and logs would refer this name on related info/errors"
            "\nDefault value is 'core'. Press ENTER to accept default value or type in new name':")
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
        # TODO add code to pull latest release
        answer = input(f"\n-----------Gateway release for {gateway_or_aggregator} -------\n"
                       f"Type in {gateway_or_aggregator} release tag:")
        return answer

    @staticmethod
    def check_for_gateway():
        print("\n===========Network Gateway settings =================\n")
        print(
            "\nDo you want to setup NETWORK GATEWAY on this machine? "
            "\nFor more info refer https://docs.radixdlt.com/main/node-and-gateway/network-gateway.html")
        answer = input("Default is No[N], Press ENTER to accept default or type in [Y/N]")
        return Helpers.check_Yes(Prompts.check_default(answer, "N"))

    @staticmethod
    def check_for_fullnode():
        print("\n===========Full node settings =================")
        print(
            "\nDo you want to setup fullnode or a validator?  "
            "\nFor more information refer "
            "https://docs.radixdlt.com/main/node-and-gateway/node-introduction.html#_what_is_a_radix_node")
        answer = input("Default is Y, Press ENTER to accept default or type in [Y/N]:")
        return Helpers.check_Yes(Prompts.check_default(answer, "Y"))

    @staticmethod
    def ask_enable_transaction():
        answer = input(
            "\n---------TRANSACTION API --------"
            "\nTransactions API on fullnodes are disabled. To enable this, it requires to be set to true,"
            "\nPress 'ENTER' to accept 'false'. otherwise type 'true' [true/false]:")
        return Prompts.check_default(answer, "false")

    @staticmethod
    def ask_keyfile_path():
        print(f"\n------ KEYSTORE FILE ----"
              f"\nThe keystore file is very important and it is the identity of the node."
              f"\nIf you are planning to run a validator, defintely make sure you backup this keystore file"
              )
        y_n = input("\nDo you have a keystore file that you want to use [Y/N]?")
        if Helpers.check_Yes(Prompts.check_default(y_n, "N")):
            return input("Enter the absolute path of the folder, just the folder, where the keystore file is located:")
        else:
            radixnode_dir = f"{Helpers.get_home_dir()}/node-config"
            answer = input(
                f"\nDefault folder location for Keystore file will be: {radixnode_dir}"
                "\nPress 'ENTER' to accept default. otherwise enter the absolute path of the new folder:")
            # TODO this needs to moved out of init
            run_shell_command(f'mkdir -p {radixnode_dir}', shell=True, quite=True)
            return str(radixnode_dir)

    @staticmethod
    def ask_keyfile_name():
        default_keyfile_name = "node-keystore.ks"
        value = input(
            f"\nType in name of keystore file. Otherwise press 'Enter' to use default value '{default_keyfile_name}':").strip()
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
        y_n = input("\n----------NEW or EXISTING SETUP ------- \n"
                    "\nIs this first time you running the node on this machine [Y/N]")
        if Helpers.check_Yes(y_n):
            return None
        else:
            prompt_answer = input(
                f"\nSo you have existing docker compose file. Is it in location '{os.getcwd()}/{default_compose_file}'?"
                f"\nIf so, press 'ENTER' or type in absolute path to file:")
            if prompt_answer == "":
                return f"{os.getcwd()}/{default_compose_file}"
            else:
                return prompt_answer
