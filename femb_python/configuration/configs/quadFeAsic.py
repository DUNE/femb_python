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
        self.femb.write_reg( self.REG_RESET, 1)
        time.sleep(5.)

    def initBoard(self):
        print("Initialize board")

        #Set DAC to 0
        self.femb.write_reg( self.REG_SET_DAC , 0x1000 )
        self.femb.write_reg( self.REG_DAC_ADC_EN , 1 )

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
        self.femb.write_reg( self.REG_FESPI_BASE+4, 0x800 )
        self.femb.write_reg( self.REG_FESPI_BASE+9, 0x800 )
        self.femb.write_reg( self.REG_FESPI_BASE+14, 0x800 )
        self.femb.write_reg( self.REG_FESPI_BASE+19, 0x800 )

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

        regVal = (asicVal << 8 ) + chVal
        self.femb.write_reg( self.REG_SEL_CH, regVal)

