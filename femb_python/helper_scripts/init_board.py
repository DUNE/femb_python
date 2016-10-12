from ..configuration import CONFIG, get_env_config_file

def main():
    config_file = get_env_config_file()
    femb_config = CONFIG(config_file)
    femb_config.initBoard()
