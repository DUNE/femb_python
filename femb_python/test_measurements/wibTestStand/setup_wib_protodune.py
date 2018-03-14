from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import
from builtins import hex
from builtins import range
from builtins import str
from future import standard_library
standard_library.install_aliases()
from builtins import object
import sys
import string
from subprocess import call
from time import sleep
import os
import ntpath
import glob
import struct

def main():

    from ...configuration import CONFIG
    femb_config = CONFIG()
    femb_config.initWibRCE()
    femb_config.initWibUDP()

if __name__ == '__main__':
    main()
