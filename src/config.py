"""
Module containing yaml config loading.
"""
import yaml
import os

def load_config():
    """Load configuration from YAML file."""
    # This will load config from the first valid path. /etc/verity.conf has precedence above directories.
    config_paths = [
        'config.yaml',  # Current directory
        '../config.yaml',  # Parent directory (assuming script is run directly in src
        'src/config.yaml'
    ]
    
    for path in config_paths:
        if os.path.exists(path):
            with open(path, 'r') as file:
                print(f'Using configuration at {path} (Priority {config_paths.index(path)})')
                return yaml.safe_load(file)
    
    print("Warning: No configuration file found")
    return {}

config = load_config()
MAX_REQUESTS_REMAINING = int(config.get('rate_limit', {}).get('max_requests_remaining'))
LOG_SOURCE_PATH = config.get('logging', {}).get('log_path', "logs")
IMAGES_PATH = config.get('application', {}).get('images_path', "logs/images")
TEST_YAML_OUTPUT_PATH = config.get('application', {}).get('test_yaml_output_path')
PROMPT_PATH = config.get('prompt', {}).get('prompt_path', "resources/prompts")
VEC_STORE_TYPE = config.get('vectorstore', {}).get('vec_store_type', "faiss")
VEC_STORE_PATH = config.get('vectorstore', {}).get('vec_store_path')
LLM_MODEL_NAME = config.get('llm', {}).get('llm_model_name', "gpt4o")
RATE_LIMIT_INTERVAL = int(config.get('rate_limit', {}).get('rate_limit_interval_seconds'))
RESOURCE_PATH = config.get('application', {}).get('chat_flask_resource_path')
USERS_DB_PATH = config.get('user_management', {}).get('accounts_db_path')
FAKE_AUTH = bool(config.get('user_management', {}).get('dummy_authentication'))
OPENAI_API_KEY = config.get('api_keys', {}).get('openai_api_key')