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
        print("Initializing board and checking register interface")

        #check if FEMB register interface is working
        regVal = self.femb.read_reg(257)
        #print(regVal)
        if regVal == None:
            print("Error - FEMB register interface is not working.")
            print(" Will not initialize FEMB.")       
            return

        #check WIB fw version reg
        firmwareVerReg = (regVal & 0xFFF)
        if firmwareVerReg != 0x101:
            print('Error initializing board - Invalid firmware and/or register read error')
            return

    def readStatus(self, epcsNum = 0):
        #EPCS OP Code
        op_reg = 1 + 3*epcsNum
        #EPCS Status
        status_reg = 3 + 3*epcsNum
        
        #set status op code
        self.femb.write_reg(op_reg,0x5)
    
        #start EPCS operation
        self.femb.write_reg(op_reg,0x105)
        #self.femb.write_reg_bits(1 , 8, 0x1, 1 )

        #wait a bit
        time.sleep(0.001)

        #stop EPCS operation
        self.femb.write_reg(op_reg,0x5)
        #self.femb.write_reg_bits(1 , 8, 0x1, 1 )

        #read status bit
        regVal = self.femb.read_reg(status_reg)
        if regVal == None:
            return

        print("STATUS BIT ",regVal)

    def readFlash(self, epcsNum = 0, pageNum = 0):
        #EPCS OP Code
        op_reg = 1 + 3*epcsNum
        #EPCS address
        addr_reg = 2 + 3*epcsNum
        
        read_base = 512 + 256*epcsNum

        #set page to read
        self.femb.write_reg(addr_reg, 256*pageNum) #1 page = 256 byte
        
        #read bytes op code
        self.femb.write_reg(op_reg,0x3)

        #start EPCS operation
        self.femb.write_reg(op_reg,0x103)

        #stop operation
        self.femb.write_reg(op_reg,0x0)

        #wait a bit
        time.sleep(0.1)

        #read the value
        for reg in range(read_base + 64, read_base + 64 + 64,1):
            regVal = self.femb.read_reg(reg)
            if regVal == None:
                continue
            print(reg,"\t",regVal,"\t",hex(regVal))

    def eraseFlash(self, epcsNum = 0):
        #EPCS OP Code
        op_reg = 1 + 3*epcsNum

        #write enable
        self.femb.write_reg(op_reg,0x6)        
        self.femb.write_reg(op_reg,0x106)
        self.femb.write_reg(op_reg,0x0)

        #erase bulk
        self.femb.write_reg(op_reg,0xC7)
        time.sleep(0.5)        
        self.femb.write_reg(op_reg,0x1C7)
        time.sleep(0.5)
        self.femb.write_reg(op_reg,0xC7)
        self.femb.write_reg(op_reg,0x0)

        time.sleep(10)

    def programFlash(self, epcsNum = 0, pageNum = 0):
        #Note: The bytes of memory must be erased before write bytes operation is implemented

        #EPCS OP Code
        op_reg = 1 + 3*epcsNum

        #EPCS address
        addr_reg = 2 + 3*epcsNum

        #EPCS Status
        status_reg = 3 + 3*epcsNum
                
        read_base = 512 + 256*epcsNum

        for reg in range(read_base, read_base + 64, 1):
            self.femb.write_reg(reg, 0x99999999)

        #Set write enable
        self.femb.write_reg(op_reg,0x6)
        self.femb.write_reg(op_reg,0x106)
        time.sleep(1)
        self.femb.write_reg(op_reg,0x0)

        #set page to write
        self.femb.write_reg(addr_reg, 256*pageNum)

        #write bytes
        self.femb.write_reg(op_reg,0x2)
        self.femb.write_reg(op_reg,0x102)
        time.sleep(1)
        
        #read status bit
        self.femb.write_reg(op_reg,0x5)
        self.femb.write_reg(op_reg,0x105)
        time.sleep(0.5)
        self.femb.write_reg(op_reg,0x5)
        print("Status is: ", self.femb.read_reg(status_reg))

        time.sleep(1)
        self.femb.write_reg(op_reg,0x2)

        #read bytes
        self.femb.write_reg(op_reg,0x3)
        self.femb.write_reg(op_reg,0x103)
        time.sleep(1)
        self.femb.write_reg(op_reg,0x0)

        #read the value
        time.sleep(1)
        for reg in range(read_base + 64, read_base + 64 + 64, 1):
            regVal = self.femb.read_reg(reg)
            if regVal == None:
                continue
            print(reg,"\t",regVal,"\t",hex(regVal))

            
