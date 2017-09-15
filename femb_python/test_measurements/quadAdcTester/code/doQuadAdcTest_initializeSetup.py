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

def completeFailure():
    print("\n")
    print("-------------------")
    print("\n")
    print( "FAILED TO INITILIAZE TEST SETUP!" )
    print("\n")
    print("-------------------")
    print("\n")

def totalVictory():
    print("\n")
    print("-------------------")
    print("\n")
    print( "TEST SETUP INITIALIZED!" )
    print("\n")
    print("-------------------")
    print("\n")

def main( isCold=False ):

    if (isCold != True) and (isCold != False) :
        print("Invalid input temperature parameter, will assume room temperature")
        isCold = False

    #initialize board
    femb_config = CONFIG()
    femb_config.COLD = isCold
    femb_config.enableTest = 1
    #femb_config.isExternalClock = True
    #femb_config.is1MHzSAMPLERATE = False #COOL

    print("\n")
    print("Running test setup initialization process")
    print("Configuration parameters:")
    femb_config.printParameters()

    #initialize readout to known working state
    print("Initializing board")
    initStatus = femb_config.initBoard()
    if initStatus == False :
        #setup in bad state
        completeFailure()
        return
    asicStatus = [1,1,1]
    initStatus = femb_config.initAsic(0)
    if initStatus == False :
        print( "Could not initialize ASIC ", 0 )
        asicStatus[0] = 0
    initStatus = femb_config.initAsic(1)
    if initStatus == False :
        print( "Could not initialize ASIC ", 1 )
        asicStatus[1] = 0
    initStatus = femb_config.initAsic(2)
    if initStatus == False :
        print( "Could not initialize ASIC ", 2 )
        asicStatus[2] = 0

    #use external pulser
    femb_config.setFPGADac(0,1,0,0) # write regs 4 and 5

    #ideally check if function generator exists here...

    #initialize funciton generator
    funcgen = Keysight_33600A("/dev/usbtmc0",1) #hardcoded to usbtmc0
    xLow = 0.1
    xHigh = 1.3
    offsetV = (xLow + xHigh)*0.5
    amplitudeV = (xHigh - xLow)*0.5
    freq = 20173
    funcgen.startSin(freq,amplitudeV,offsetV)

    #setup is in good state
    totalVictory()
    print("ASIC STATUS","\t",asicStatus)

if __name__ == '__main__':
    main()
