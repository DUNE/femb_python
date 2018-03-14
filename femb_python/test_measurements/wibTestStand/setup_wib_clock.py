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

from ...configuration import CONFIG

def main():

    femb_config = CONFIG()
    femb_config.initWib()

if __name__ == '__main__':
    main()
