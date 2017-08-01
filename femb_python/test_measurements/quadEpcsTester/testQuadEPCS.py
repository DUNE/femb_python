from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import
from builtins import hex
from builtins import open
from builtins import range
from builtins import int
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
import json

from femb_python.configuration import CONFIG
from femb_python.write_data import WRITE_DATA

def main():

    femb_config = CONFIG()
    femb_config.initBoard()

    #check status
    #femb_config.readStatus(2)
    #femb_config.readFlash(2)
    #femb_config.eraseFlash(3)
    #femb_config.readFlash(3)
    femb_config.programFlash(3)
    femb_config.readFlash(3)
    
if __name__ == '__main__':
    main()
