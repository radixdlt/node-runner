import os

import yaml

from env_vars import PROMPT_FEEDS


class QuestionKeys:
    select_network = "select_network"
    first_time_config = "first_time_config"
    have_existing_compose = "have_existing_compose"
    setup_fullnode = "setup_fullnode"
    input_seednode = "input_seednode"
    have_keystore_file = "have_keystore_file"
    input_path_keystore = "input_path_keystore"
    enter_keystore_name = "enter_keystore_name"
    input_ledger_path = "input_ledger_path"
    input_transaction_api = "input_transaction_api"
    core_nginx_setup = "core_nginx_setup"
    gateway_nginx_setup = "gateway_nginx_setup"
    setup_gateway = "setup_gateway"
    input_nginx_release = "input_nginx_release"
    input_core_api_address = "input_core_api_address"
    basic_auth_user = "basic_auth_user"
    basic_auth_password = "basic_auth_password"
    core_api_disable_https_verify = "core_api_disable_https_verify"
    core_api_node_name = "core_api_node_name"
    postgres_location = "postgres_location"
    postgres_db_host = "postgres_db_host"
    postgres_db_port = "postgres_db_port"
    postgres_db_user = "postgres_db_user"
    postgres_db_name = "postgres_db_name"
    postgres_db_password = "postgres_db_password"
    gateway_release = "gateway_release"
    aggregator_release = "aggregator_release"

class PromptFeeder:
    _instance = None
    mode = None
    prompts_feed = []

    def __init__(self):
        raise RuntimeError('Call instance() instead')

    @classmethod
    def load_prompt_feeds(cls):
        feed_prompts_file = os.getenv(PROMPT_FEEDS, None)

        if feed_prompts_file and os.path.exists(feed_prompts_file):
            with open(feed_prompts_file, "r") as file:
                prompt_feeds = yaml.safe_load(file)
                return prompt_feeds
        return []

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls.prompts_feed = cls.load_prompt_feeds()
            cls._instance = cls.__new__(cls)
        return cls._instance

    @classmethod
    def get_answer(cls, question_key):
        if len(cls.prompts_feed) != 0:
            first, *remaining = cls.prompts_feed
            cls.prompts_feed = remaining
            return first.get(question_key)
        return None
