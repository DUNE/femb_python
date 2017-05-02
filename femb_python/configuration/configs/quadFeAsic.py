#!/usr/bin/env python33

"""
Configuration for QUAD ADC Test Board
"""

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import
from builtins import super
from builtins import int
from builtins import range
from builtins import hex
from builtins import str
from future import standard_library
standard_library.install_aliases()
from builtins import object
import sys 
import string
import time
import copy
from femb_python.femb_udp import FEMB_UDP
from femb_python.configuration.config_base import FEMB_CONFIG_BASE

class FEMB_CONFIG(FEMB_CONFIG_BASE):

    def __init__(self):
        super().__init__()
        #declare board specific registers
        self.FEMB_VER = "quadasictest"
        self.NASICS = 4
        self.NASICCH = 16

        self.REG_RESET = 0
        self.REG_DAC_VALUE = 1
        self.REG_SET_DAC = 2
        self.REG_START = 3
        self.REG_SEL_ASIC = 4
        self.REG_SEL_CH = 4
        self.REG_ASIC_RESET = 5
        self.REG_ASIC_SPIPROG = 5
        self.REG_SAMPLE_STOP = 6
        self.REG_TP_PERIOD_P = 7
        self.REG_TP_PERIOD_N = 7
        self.REG_TP_MODE = 9
        self.REG_TST_SW = 12
        self.REG_LED_CNTL = 13
        self.REG_FESPI_BASE = 20
        self.REG_FRAME_SIZE = 40
        self.REG_DAC_ADC_EN = 60

        #initialize FEMB UDP object
        self.femb = FEMB_UDP()

    def resetBoard(self):
        #Reset system
        #self.femb.write_reg( self.REG_RESET, 1)
        time.sleep(1.)
        #print("RESET")

    def initBoard(self):
        print("Initialize board")

        #Set DAC to 0
        self.femb.write_reg( self.REG_SET_DAC , 0x0 )
        self.femb.write_reg( self.REG_DAC_ADC_EN , 0 )

        #disable LEDs
        self.femb.write_reg( self.REG_LED_CNTL , 0 )

        #Set FE ASIC cntrl reg to 0
        self.femb.write_reg( self.REG_ASIC_RESET , 0 )

        #select channel
        self.selectChannel(2,0)

        #reset pulser regs
        self.femb.write_reg( self.REG_TP_PERIOD_P , 0 )
        self.femb.write_reg( self.REG_TP_MODE , 0 )

        #turn on ASICs
        self.femb.write_reg( self.REG_TST_SW, 0x0)
        self.femb.write_reg( self.REG_START, 1)

        #reset ASICs
        #self.femb.write_reg( self.REG_RESET, 2)

        #configure ASICs to default
        print("Config FE ASIC SPI")
        for regNum in range(self.REG_FESPI_BASE,self.REG_FESPI_BASE+20,1):
          self.femb.write_reg( regNum, 0x81818181)
        self.femb.write_reg( self.REG_FESPI_BASE+4, 0xA00 )
        self.femb.write_reg( self.REG_FESPI_BASE+9, 0xA00 )
        self.femb.write_reg( self.REG_FESPI_BASE+14, 0xA00 )
        self.femb.write_reg( self.REG_FESPI_BASE+19, 0xA00 )

        self.femb.write_reg( self.REG_ASIC_SPIPROG, 0)
        self.femb.write_reg( self.REG_ASIC_SPIPROG, 1)
        self.femb.write_reg( self.REG_ASIC_SPIPROG, 0)
    
    def selectChannel(self,asic,chan,hsmode=None):
        asicVal = int(asic)
        if (asicVal < 0 ) or (asicVal >= self.NASICS ) :
                print( "femb_config_femb : selectChan - invalid ASIC number, only 0 to {} allowed".format(self.NASICS-1))
                return
        chVal = int(chan)
        if (chVal < 0 ) or (chVal > self.NASICCH ) :
                print("femb_config_femb : selectChan - invalid channel number, only 0 to 15 allowed")
                return

        print( "Selecting ASIC " + str(asicVal) + ", channel " + str(chVal))

        #note need to add 1 to asicVal
        asicVal = asicVal + 1

        regVal = (asicVal << 8 ) + chVal
        self.femb.write_reg( self.REG_SEL_CH, regVal)

    def configFeAsic(self,gain,shape,base):
        print("CONFIG ASICs")
        #configure ASICs to default
        """
        print("Config FE ASIC SPI")
        for regNum in range(self.REG_FESPI_BASE,self.REG_FESPI_BASE+20,1):
          self.femb.write_reg( regNum, 0x81818181)
        self.femb.write_reg( self.REG_FESPI_BASE+4, 0xA00 )
        self.femb.write_reg( self.REG_FESPI_BASE+9, 0xA00 )
        self.femb.write_reg( self.REG_FESPI_BASE+14, 0xA00 )
        self.femb.write_reg( self.REG_FESPI_BASE+19, 0xA00 )

        #do configuration
        self.femb.write_reg( self.REG_ASIC_SPIPROG, 0)
        self.femb.write_reg( self.REG_ASIC_SPIPROG, 1)
        self.femb.write_reg( self.REG_ASIC_SPIPROG, 0)
        """

        #channel specific variables
        testVal = 1
        baseVal = 1 #0 = 900mV, 1 = 200mV
        gainVal = 2 
        shapeVal = 1
        acdcVal = 0 #AC = 0, DC = 1
        bufVal = 1 #0 = OFF, 1 = ON

        if (testVal < 0 ) or (testVal > 1):
                return
        if (baseVal < 0 ) or (baseVal > 1):
                return
        if (gainVal < 0 ) or (gainVal > 3):
                return
        if (shapeVal < 0 ) or (shapeVal > 3):
                return
        if (acdcVal < 0 ) or (acdcVal > 1):
                return
        if (bufVal < 0 ) or (bufVal > 1):
                return

        chReg = 0
        #test capacitor, bit 7
        chReg = chReg + ((testVal & 0x01)<<7)

        #baseline control, bit 6
        chReg = chReg +  ((baseVal & 0x01)<<6)
 
        #gain control, bits 4-5
        gainArray = [0,2,1,3]
        chReg = chReg + ((gainArray[gainVal] & 0x03)<<4)

        #shape control, bits 2-3
        shapeArray = [2,0,3,1] #I don't know why
        chReg = chReg + ((shapeArray[shapeVal] & 0x03)<<2)

        #AC/DC control, bits 1
        chReg = chReg + ((acdcVal & 0x01)<<1)

        #buffer control, bit 0
        chReg = chReg + ((bufVal & 0x01)<<0)

        #construct the channel word
        chWord = (chReg << 24 ) + (chReg << 16) + (chReg << 8 ) + chReg

        asicReg = 0
        
        #leakage control 1, bit 0
 
        #leakage control 2, bit 4

        #monitor contronl, bits 1-2

        #internal DAC enable, bit 8

        #external DAC enable, bit 9

        #DAC OUTPUT??? bits 8-9 , 0xA00 = external DAC

        #DAC value, bits 12-15, might be 10-15
 
        #write ASIC SPI registers, note all ASICs+channels configured the same
        for regNum in range(self.REG_FESPI_BASE,self.REG_FESPI_BASE+20,1):
          #print( str(regNum) + "\t" + str(hex(chWord)) )
          self.femb.write_reg( regNum, chWord)

        self.femb.write_reg( self.REG_ASIC_SPIPROG, 0)
        self.femb.write_reg( self.REG_ASIC_SPIPROG, 1)
        self.femb.write_reg( self.REG_ASIC_SPIPROG, 0)

        """
        self.femb.write_reg( self.REG_TP_MODE, 0x9) #pulser enabled
        asicWord = 0xF90

        #reconfigure ASICs
        self.femb.write_reg( self.REG_FESPI_BASE+4, asicWord )
        self.femb.write_reg( self.REG_FESPI_BASE+9, asicWord )
        self.femb.write_reg( self.REG_FESPI_BASE+14, asicWord )
        self.femb.write_reg( self.REG_FESPI_BASE+19, asicWord )

        self.femb.write_reg( self.REG_ASIC_SPIPROG, 0)
        self.femb.write_reg( self.REG_ASIC_SPIPROG, 1)
        self.femb.write_reg( self.REG_ASIC_SPIPROG, 0)

        #disable old DAC
        self.femb.write_reg( self.REG_TP_PERIOD_P, 0x01000100)
        self.femb.write_reg( self.REG_DAC_VALUE , 0 )
        self.femb.write_reg( self.REG_SET_DAC , 0x0 ) #not necessary?
        self.femb.write_reg( self.REG_SET_DAC , 0x1 ) #not necessary?
        self.femb.write_reg( self.REG_SET_DAC , 0x0 ) #not necessary?
        """

    def setInternalPulser(self,enable,dac):
        enableVal = int(enable)
        if (enableVal < 0 ) or (enableVal > 1 ) :
                print( "femb_config_femb : setInternalPulser - invalid enable value")
                return
        dacVal = int(dac)
        if ( dacVal < 0 ) or ( dacVal > 0x3F ) :
                print( "femb_config_femb : setInternalPulser - invalid dac value")
                return

        if enableVal == 1 :
                self.femb.write_reg( self.REG_TP_MODE, 0x9) #pulser enabled
        else :
                self.femb.write_reg( self.REG_TP_MODE, 0x0) #pulser disabled
                dacVal = 0

        dacVal = (dacVal & 0x3F)
        newDacVal = int('{:08b}'.format(dacVal)[::-1], 2)

        #asicWord = 0
        #asicWord = newDacVal
        asicWord = ((newDacVal << 8 ) & 0xFFFF)
        if enableVal == 1 :
                asicWord = asicWord + (0x1 << 8)

        #print("ASIC WORD " + str(hex(asicWord)) )

        #reconfigure ASICs
        self.femb.write_reg( self.REG_FESPI_BASE+4, asicWord )
        self.femb.write_reg( self.REG_FESPI_BASE+9, asicWord )
        self.femb.write_reg( self.REG_FESPI_BASE+14, asicWord )
        self.femb.write_reg( self.REG_FESPI_BASE+19, asicWord )

        self.femb.write_reg( self.REG_ASIC_SPIPROG, 0)
        self.femb.write_reg( self.REG_ASIC_SPIPROG, 1)
        self.femb.write_reg( self.REG_ASIC_SPIPROG, 0)

        #disable old DAC
        self.femb.write_reg( self.REG_TP_PERIOD_P, 0x01000100)
        self.femb.write_reg( self.REG_DAC_VALUE , 0 )
        self.femb.write_reg( self.REG_SET_DAC , 0x0 ) #not necessary?
        self.femb.write_reg( self.REG_SET_DAC , 0x1 ) #not necessary?
        self.femb.write_reg( self.REG_SET_DAC , 0x0 ) #not necessary?

    def setDacPulser(self,enable,dac):
        enableVal = int(enable)
        if (enableVal < 0 ) or (enableVal > 1 ) :
                print( "femb_config_femb : setDacPulser - invalid enable value")
                return
        dacVal = int(dac)
        if ( dacVal < 0 ) or ( dacVal > 0xFFFF ) :
                print( "femb_config_femb : setDacPulser - invalid dac value")
                return

        if enableVal == 1 :
                self.femb.write_reg( self.REG_TP_MODE, 0x8) #pulser enabled
        else :
                self.femb.write_reg( self.REG_TP_MODE, 0x0) #pulser disabled

        self.femb.write_reg( self.REG_TP_PERIOD_P, 0x01000100)
        self.femb.write_reg( self.REG_DAC_VALUE , dacVal )
        self.femb.write_reg( self.REG_SET_DAC , 0x0 ) #not necessary?
        self.femb.write_reg( self.REG_SET_DAC , 0x1 ) #not necessary?
        self.femb.write_reg( self.REG_SET_DAC , 0x0 ) #not necessary?
