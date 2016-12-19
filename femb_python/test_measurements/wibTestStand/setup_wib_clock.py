from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
import sys
import string
from subprocess import call
from time import sleep
import os
import ntpath
import glob
import struct

def main():

    from femb_python.configuration.femb_config_wib_sbnd import FEMB_CONFIG
    femb_config = FEMB_CONFIG()
    femb_config.initWib()

if __name__ == '__main__':
    main()
