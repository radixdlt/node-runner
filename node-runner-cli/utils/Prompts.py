from utils.utils import Helpers


class Prompts:

    @staticmethod
    def check_default(answer, default):
        if answer == "":
            return default
        else:
            return answer

    @staticmethod
    def get_postgress_password():
        answer = input("Type in Postgress database password:")
        return answer

    @staticmethod
    def get_postgress_user():
        answer = input("Type in Postgress username:")
        return answer

    @staticmethod
    def get_postgress_dbname():
        answer = input("Type in Postgress database name:")
        return answer

    @staticmethod
    def get_CoreApiAddress():
        answer = input("Type in CoreApi address in format of url like http(s)://<host and port>:")
        return answer

    @staticmethod
    def get_CopeAPINodeName():
        answer = input(
            "Type in CoreApi node name. This can be any string and logs would refer this name on related info/errors"
            "Press ENTER to accept default value `core-api`:")
        return Prompts.check_default(answer, 'core-api')

    @staticmethod
    def get_TrustWeighting():
        answer = input(
            "Type in TrustWeight settings. Default is 1, press 'ENTER' to accept default:")
        return Prompts.check_default(answer, 1)

    @staticmethod
    def get_RequestWeighting():
        answer = input(
            "Type in RequestWeighting settings. Default is 1, press 'ENTER' to accept default:")
        return Prompts.check_default(answer, 1)

    @staticmethod
    def get_coreAPINodeEnabled():
        answer = input(
            "Is this node enabled for gateway. Press Enter accept default as true [true/false]:")
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
    def get_gateway_release():
        # TODO add code to pull latest release
        answer = input("Type in gateway release tag:")
        return answer

    @staticmethod
    def check_for_gateway():
        print(
            "Do you want to setup NETWORK GATEWAY on this node? "
            "\nFor more info refer https://docs.radixdlt.com/main/node-and-gateway/network-gateway.html")
        answer = input("Press ENTER for No or type in either Y or N:")
        return Helpers.check_Yes(Prompts.check_default(answer, "N"))
