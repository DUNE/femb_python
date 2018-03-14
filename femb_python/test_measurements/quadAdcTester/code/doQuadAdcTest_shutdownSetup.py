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

#import femb_python package modules
from femb_python.configuration import CONFIG
from femb_python.test_instrument_interface.keysight_33600A import Keysight_33600A

def main():

    femb_config = CONFIG()

    #initialize readout to known working state
    print("Turn off ASICs")
    femb_config.turnOffAsics()

    #ideally check if function generator exists here...

    #initialize funciton generator
    funcgen = Keysight_33600A("/dev/usbtmc0",1) #hardcoded to usbtmc0
    funcgen.stop()

if __name__ == '__main__':
    main()
