#!/usr/bin/env python33

"""
Configuration for quad EPCS Flash memory tester
"""

from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals
from __future__ import absolute_import
from builtins import range
from builtins import int
from builtins import hex
from builtins import str
from future import standard_library
standard_library.install_aliases()
from builtins import object
import sys 
import string
import time
from femb_python.femb_udp import FEMB_UDP
from femb_python.configuration.config_base import FEMB_CONFIG_BASE

class FEMB_CONFIG(FEMB_CONFIG_BASE):

    #__INIT__#
    def __init__(self):
        #declare basic system parameters
        self.NEPCS = 4

        #set up UDP interface
        self.femb = FEMB_UDP()

        #declare board specific registers
        self.FEMB_VER = "QUAD_EPCS"
        self.REG_RESET = 0

    def resetBoard(self):
        print("Reset")

    def initBoard(self):
        print("Initialize")

        #check if FEMB register interface is working
        print("Checking register interface")
        regVal = self.femb.read_reg(257)
        if regVal == None:
            print("Error - FEMB register interface is not working.")
            print(" Will not initialize FEMB.")       
            return

        #check WIB fw version reg
        firmwareVerReg = (regVal & 0xFFF)
        if firmwareVerReg != 0x101:
            print('Error initializing board - Invalid firmware and/or register read error')
            return

    def checkStatus(self):
        #chip 0 only here
        #set status op code
        self.femb.write_reg(1,0x5)
    
        #start EPCS operation
        self.femb.write_reg(1,0x105)
        #self.femb.write_reg_bits(1 , 8, 0x1, 1 )

        #wait a bit
        time.sleep(0.001)

        #stop EPCS operation
        self.femb.write_reg(1,0x5)
        #self.femb.write_reg_bits(1 , 8, 0x1, 1 )

        #read status bit
        regVal = self.femb.read_reg(3)
        if regVal == None:
            return

        print("STATUS BIT ",regVal)
