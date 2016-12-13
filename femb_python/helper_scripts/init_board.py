from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
from ..configuration import CONFIG

def main():
    femb_config = CONFIG()
    femb_config.resetBoard()
    femb_config.initBoard()
