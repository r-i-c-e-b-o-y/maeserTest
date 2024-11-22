"""
Module containing yaml config loading.
"""
import yaml
import os

def load_config():
    """Load configuration from YAML file."""
    # This will load config from the first valid path. /etc/verity.conf has precedence above directories.
    config_paths = [
        '/etc/verity.conf',  # System-wide configuration
        '/etc/verity.yaml',  # System-wide configuration
        '/opt/verity/verity.conf',
        '/opt/verity/verity.yaml',
        '/opt/verity/config.yaml',
        'verity.yaml',  # Current directory
        '../verity.yaml',  # Parent directory (assuming script is run directly in src/)
        'config.yaml',  # Current directory
        '../config.yaml',  # Parent directory (assuming script is run directly in src/)
    ]
    
    for path in config_paths:
        if os.path.exists(path):
            with open(path, 'r') as file:
                print(f'Using configuration at {path} (Priority {config_paths.index(path)})')
                return yaml.safe_load(file)
    
    print("Warning: No configuration file found")
    return {}

config = load_config()
MAX_REQUESTS_REMAINING = int(config.get('rate_limit', {}).get('max_requests_remaining', 10))
LOG_SOURCE_PATH = config.get('logging', {}).get('log_path', "logs")
IMAGES_PATH = config.get('application', {}).get('images_path', "logs/images")
TEST_YAML_OUTPUT_PATH = config.get('application', {}).get('test_yaml_output_path', "logs/test_output.yaml")
PROMPT_PATH = config.get('prompt', {}).get('prompt_path', "resources/prompts")
VEC_STORE_TYPE = config.get('vectorstore', {}).get('vec_store_type', "faiss")
VEC_STORE_PATH = config.get('vectorstore', {}).get('vec_store_path', "resources/vectorstore")
LLM_MODEL_NAME = config.get('llm', {}).get('llm_model_name', "gpt4o")
RATE_LIMIT_INTERVAL = int(config.get('rate_limit', {}).get('rate_limit_interval_seconds', 60))
RESOURCE_PATH = config.get('application', {}).get('chat_flask_resource_path', "resources/web")
USERS_DB_PATH = config.get('user_management', {}).get('accounts_db_path', "chat_logs/chat_history/users.db")
FAKE_AUTH = bool(config.get('user_management', {}).get('dummy_authentication', False))
OPENAI_API_KEY = config.get('api_keys', {}).get('openai_api_key', "")