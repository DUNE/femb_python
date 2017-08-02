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
import time
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

    for iFlash in range(4):
        femb_config.readStatus(iFlash)
        femb_config.eraseFlash(iFlash)
        femb_config.readStatus(iFlash)
        for iPage in range(10):
            femb_config.readFlash(iFlash, iPage)
            femb_config.programFlash(iFlash, iPage)
            femb_config.readFlash(iFlash, iPage)
    
if __name__ == '__main__':
    main()
