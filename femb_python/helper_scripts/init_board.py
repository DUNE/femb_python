from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
from ..configuration import CONFIG, get_env_config_file

def main():
    config_file = get_env_config_file()
    femb_config = CONFIG(config_file)
    femb_config.initBoard()
