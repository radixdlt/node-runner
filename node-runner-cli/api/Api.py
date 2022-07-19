import os

from env_vars import PRINT_RESPONSE, NGINX
from utils.utils import Helpers


class API:

    @staticmethod
    def get_host_info():
        scheme = os.getenv("API_SCHEME", "https")
        node_host = os.getenv("NODE_END_POINT", f'{scheme}://localhost')
        return node_host

    @staticmethod
    def set_basic_auth(api_client, usertype: str, username: str):
        if os.getenv(NGINX,"true") == "true":
            user = Helpers.get_nginx_user(usertype=usertype, default_username=username)
            headers = Helpers.get_basic_auth_header(user)
            api_client.set_default_header("Authorization", headers["Authorization"])
        return api_client

    @staticmethod
    def handle_response(response, print_response=False):
        if print_response or os.getenv(PRINT_RESPONSE):
            print("----response----")
            print(response)
        return response
