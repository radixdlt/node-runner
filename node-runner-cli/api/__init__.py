import os
import requests
from requests.auth import HTTPBasicAuth

from utils.utils import Helpers


class Api:

    @staticmethod
    def get_node_info():
        scheme = os.getenv("API_SCHEME", "https")
        node_host = os.getenv("NODE_END_POINT", f'{scheme}://localhost')
        user = Helpers.get_nginx_user(usertype="admin", default_username="admin")
        data = f"""
            {{
                "jsonrpc": "2.0",
                "method": "validation.get_node_info",
                "params": [],
                "id": 1
            }}
        """
        req = requests.Request('POST',
                               f"{node_host}/validation",
                               data=data,
                               auth=HTTPBasicAuth(user["name"], user["password"]))

        prepared = req.prepare()
        Helpers.send_request(prepared)
