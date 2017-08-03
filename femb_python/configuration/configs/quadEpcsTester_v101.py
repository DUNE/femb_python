#!/usr/bin/env python33

"""
Configuration for quad EPCS Flash memory tester
"""
import sys 
import time

from femb_python.femb_udp import FEMB_UDP
from femb_python.configuration.config_base import FEMB_CONFIG_BASE

class FEMB_CONFIG(FEMB_CONFIG_BASE):

    #__INIT__#
    def __init__(self):
        #set up UDP interface
        self.femb = FEMB_UDP()

    def initBoard(self):
        print("\nInitializing board and checking register interface\n")

        #check if FEMB register interface is working
        regVal = self.femb.read_reg(257)
        if regVal == None:
            print("Error!! FEMB register interface is not working, will not initialize FEMB.")
            print("Is the power supply turned on?\n")
            sys.exit(1)

        #check WIB fw version reg
        firmwareVerReg = (regVal & 0xFFF)
        if firmwareVerReg != 0x101:
            print('Error initializing board!! Invalid firmware and/or register read error.\n')
            sys.exit(1)

    def readStatus(self, epcsNum = 0):
        #EPCS OP Code
        op_reg = 1 + 3*epcsNum
        #EPCS Status
        status_reg = 3 + 3*epcsNum
        
        #set status op code
        self.femb.write_reg(op_reg,0x5)
        #start EPCS operation
        self.femb.write_reg(op_reg,0x105)
        time.sleep(0.1)
        #stop EPCS operation
        self.femb.write_reg(op_reg,0x5)

        #read status bit
        statusVal = self.femb.read_reg(status_reg)
        if statusVal == None:
            print("Error!! Status is None.")
            return

        print("STATUS BIT: ",statusVal)
        return statusVal

    def readFlash(self, epcsNum = 0, pageNum = 0):
        print("\nReading flash %s, page %s" %(epcsNum, pageNum))
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
        time.sleep(0.1)
        self.femb.write_reg(op_reg,0x3)

        #read the value
        outputData = []
        for reg in range(read_base + 64, read_base + 64 + 64, 1):
            regVal = self.femb.read_reg(reg)
            if regVal == None:
                print("Error!! Read value is None, will continue")
                continue
            outputData.append(regVal)
        return outputData

    def eraseFlash(self, epcsNum = 0):
        print("\nErasing flash %s" %(epcsNum))
        #EPCS OP Code
        op_reg = 1 + 3*epcsNum

        #write enable
        self.femb.write_reg(op_reg,0x6)        
        self.femb.write_reg(op_reg,0x106)
        time.sleep(0.1)
        self.femb.write_reg(op_reg,0x6)

        #erase bulk
        self.femb.write_reg(op_reg,0xC7)
        self.femb.write_reg(op_reg,0x1C7)
        time.sleep(0.1)
        self.femb.write_reg(op_reg,0xC7)

        #Erase bulk cycle time for EPCS64 is 160s max
        for t in range(480): #8 mins
            status = self.readStatus(epcsNum)
            time.sleep(1)
            if(status == 0):
                self.readStatus(epcsNum)
                break
            
    def programFlash(self, epcsNum = 0, pageNum = 0, inputData = None):
        print("\nPrograming flash %s, page %s" %(epcsNum, pageNum))
 
        #EPCS OP Code
        op_reg = 1 + 3*epcsNum

        #EPCS address
        addr_reg = 2 + 3*epcsNum

        #EPCS Status
        status_reg = 3 + 3*epcsNum
                
        write_base = 512 + 256*epcsNum

        count = 0
        for reg in range(write_base, write_base + 64, 1):
            self.femb.write_reg(reg, inputData[count])
            count +=1

        #Set write enable
        self.femb.write_reg(op_reg,0x6)
        self.femb.write_reg(op_reg,0x106)
        time.sleep(0.1)
        self.femb.write_reg(op_reg,0x6)

        #set page to write
        self.femb.write_reg(addr_reg, 256*pageNum)

        #write bytes
        self.femb.write_reg(op_reg,0x2)
        self.femb.write_reg(op_reg,0x102)
        time.sleep(0.1)
        self.femb.write_reg(op_reg,0x2)

        #Write byte cycle time for EPCS64 is 5s max
        for t in range(15):
            status = self.readStatus(epcsNum)
            time.sleep(1)
            if(status == 0):
                self.readStatus(epcsNum)
                break
