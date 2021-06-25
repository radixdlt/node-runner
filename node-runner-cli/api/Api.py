import os
class API:

    @staticmethod
    def get_host_info():
        scheme = os.getenv("API_SCHEME", "https")
        node_host = os.getenv("NODE_END_POINT", f'{scheme}://localhost')
        return node_host
