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

def main():

    #initialize board
    femb_config = CONFIG()
    femb_config.COLD = True
    femb_config.doSpiWrite = False

    print("\n")
    print("Running ADC synchronization process")
    print("Configuration parameters:")
    femb_config.printParameters()

    #check if register interface still working
    regVal = femb_config.femb.read_reg(femb_config.REG_FIRMWARE_VERSION)
    if regVal == None :
        print( "Register interface error, could not synchronize ASIC " )
        return

    #do sync
    asicStatus = [1,1,1,1]
    for asic in [0,1,2,3]:
        asicNum = int(asic)
        if (asicNum < 0) or (asicNum>2) :
            continue 
        femb_config.doAdcAsicConfig(asicNum)
        if femb_config.adcSyncStatus == False :
            femb_config.fixUnsync(asicNum)
        if femb_config.adcSyncStatus == False :
            print( "Could not synchronize ASIC ", asicNum )
            asicStatus[asicNum] = 0

    print("ASIC SYNC STATUS","\t",asicStatus)

if __name__ == '__main__':
    main()
