import json
import sys

import requests
from utils.utils import Helpers


def latest_release(repo_name="radixdlt/radixdlt"):
    req = requests.Request('GET',
                           f'https://api.github.com/repos/{repo_name}/releases/latest')

    prepared = req.prepare()
    prepared.headers['Content-Type'] = 'application/json'
    prepared.headers['user-agent'] = 'radixnode-cli'
    resp = Helpers.send_request(prepared, print_response=False)
    if not resp.ok:
        print("Failed to get latest release from github. Exitting the command...")
        sys.exit()

    json_response = json.loads(resp.content)
    return json_response["tag_name"]
