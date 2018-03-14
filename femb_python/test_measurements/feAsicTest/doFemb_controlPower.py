from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import
from builtins import range
from builtins import int
from builtins import str
from builtins import hex
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

class FEMB_CONTROL_POWER(object):

    def __init__(self):
        #import femb_udp modules from femb_udp package
        self.femb_config = CONFIG()

    def power_off(self):
        print("Powering down all four ASICs")
        self.femb_config.turnOffAsics()
        
    def power_on(self):
        print("Powering up all four ASICs")        
        self.femb_config.turnOnAsics()

def main():
    '''Power off the ASICs!
    '''

    power = FEMB_CONTROL_POWER()
    #onoff = input("Turn ASICs ON or OFF: ")
    onoff = sys.argv[1]
    if (onoff == "ON"):
        power.power_on()
    elif(onoff == "OFF"):
        power.power_off()
    else:
        print("Argument must be ON or OFF...doing nothing.")
    return

if __name__ == '__main__':
    main()
