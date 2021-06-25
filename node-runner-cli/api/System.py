import requests
from requests.auth import HTTPBasicAuth

from api.Api import API
from utils.utils import Helpers


class System(API):
    @staticmethod
    def api_get_configuration():
        data = f"""
            {{
                "jsonrpc": "2.0",
                "method": "api.get_configuration",
                "params": [],
                "id": 1
            }}
        """
        System.post_on_system(data)

    @staticmethod
    def api_get_data():
        data = f"""
            {{
                "jsonrpc": "2.0",
                "method": "api.get_data",
                "params": [],
                "id": 1
            }}
        """
        System.post_on_system(data)

    @staticmethod
    def bft_get_configuration():
        data = f"""
            {{
                "jsonrpc": "2.0",
                "method": "bft.get_configuration",
                "params": [],
                "id": 1
            }}
        """
        System.post_on_system(data)

    @staticmethod
    def bft_get_data():
        data = f"""
            {{
                "jsonrpc": "2.0",
                "method": "bft.get_data",
                "params": [],
                "id": 1
            }}
        """
        System.post_on_system(data)

    @staticmethod
    def mempool_get_configuration():
        data = f"""
            {{
                "jsonrpc": "2.0",
                "method": "mempool.get_configuration",
                "params": [],
                "id": 1
            }}
        """
        System.post_on_system(data)

    @staticmethod
    def mempool_get_data():
        data = f"""
            {{
                "jsonrpc": "2.0",
                "method": "mempool.get_data",
                "params": [],
                "id": 1
            }}
        """
        System.post_on_system(data)

    @staticmethod
    def ledger_get_latest_proof():
        data = f"""
            {{
                "jsonrpc": "2.0",
                "method": "ledger.get_latest_proof",
                "params": [],
                "id": 1
            }}
        """
        System.post_on_system(data)

    @staticmethod
    def ledger_get_latest_epoch_proof():
        data = f"""
            {{
                "jsonrpc": "2.0",
                "method": "ledger.get_latest_epoch_proof",
                "params": [],
                "id": 1
            }}
        """
        System.post_on_system(data)

    @staticmethod
    def radix_engine_get_configuration():
        data = f"""
            {{
                "jsonrpc": "2.0",
                "method": "radix_engine.get_configuration",
                "params": [],
                "id": 1
            }}
        """
        System.post_on_system(data)

    @staticmethod
    def radix_engine_get_data():
        data = f"""
            {{
                "jsonrpc": "2.0",
                "method": "radix_engine.get_data",
                "params": [],
                "id": 1
            }}
        """
        System.post_on_system(data)

    @staticmethod
    def sync_get_configuration():
        data = f"""
            {{
                "jsonrpc": "2.0",
                "method": "sync.get_configuration",
                "params": [],
                "id": 1
            }}
        """
        System.post_on_system(data)

    @staticmethod
    def sync_get_data():
        data = f"""
            {{
                "jsonrpc": "2.0",
                "method": "sync.get_data",
                "params": [],
                "id": 1
            }}
        """
        System.post_on_system(data)

    @staticmethod
    def networking_get_configuration():
        data = f"""
            {{
                "jsonrpc": "2.0",
                "method": "networking.get_configuration",
                "params": [],
                "id": 1
            }}
        """
        System.post_on_system(data)

    @staticmethod
    def networking_get_peers():
        data = f"""
            {{
                "jsonrpc": "2.0",
                "method": "networking.get_peers",
                "params": [],
                "id": 1
            }}
        """
        System.post_on_system(data)

    @staticmethod
    def networking_get_data():
        data = f"""
            {{
                "jsonrpc": "2.0",
                "method": "networking.get_data",
                "params": [],
                "id": 1
            }}
        """
        System.post_on_system(data)

    @staticmethod
    def checkpoints_get_checkpoints():
        data = f"""
            {{
                "jsonrpc": "2.0",
                "method": "checkpoints.get_checkpoints",
                "params": [],
                "id": 1
            }}
        """
        System.post_on_system(data)

    @staticmethod
    def post_on_system(data):
        node_host = System.get_host_info()
        user = Helpers.get_nginx_user(usertype="admin", default_username="admin")

        req = requests.Request('POST',
                               f"{node_host}/system",
                               data=data,
                               auth=HTTPBasicAuth(user["name"], user["password"]))

        prepared = req.prepare()
        return Helpers.send_request(prepared)
