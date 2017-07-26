#!/usr/bin/env python33

"""
Configuration for ProtoDUNE FEMB + SBND WIB Setup
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
        self.NFEMBS = 4
        self.NASICS = 8
        self.NASICCH = 16

        #declare board specific registers
        self.FEMB_VER = "WIB_SBND"
        self.REG_RESET = 0
        self.REG_ASIC_RESET = 1
        self.REG_ASIC_SPIPROG = 2

        self.REG_LATCHLOC_3_TO_0 = 4
        self.REG_LATCHLOC_7_TO_4 = 14

        self.REG_FPGA_TP_EN = 16
        self.REG_ASIC_TP_EN = 16
        self.REG_DAC_SELECT = 16
        self.REG_TP = 5

        self.CLK_SELECT = 6
        self.CLK_SELECT2 = 15

        self.REG_SEL_ASIC = 7
        self.REG_SEL_ASIC_LSB = 8

        self.REG_WIB_MODE = 8
        self.REG_ADC_DISABLE = 8

        self.REG_HS_DATA = 9

        self.INT_TP_EN = 18
        self.EXT_TP_EN = 18

        #EXTERNAL CLOCK STUFF HERE

        self.REG_SPI_BASE = 512
        self.REG_SPI_RDBACK_BASE = 592

        self.fembNum = 0

        #initialize FEMB UDP object
        self.femb = FEMB_UDP()
        self.femb.UDP_PORT_WREG = 32000 #WIB PORTS
        self.femb.UDP_PORT_RREG = 32001
        self.femb.UDP_PORT_RREGRESP = 32002

        #ASIC config variables
        self.feasicLeakage = 0 #0 = 500pA, 1 = 100pA
        self.feasicLeakagex10 = 0 #0 = pA, 1 = pA*10
        self.feasicAcdc = 0 #AC = 0, DC = 1
        
        self.feasicEnableTestInput = 1 #0 = disabled, 1 = enabled
        self.feasicBaseline = 1 #0 = 200mV, 1 = 900mV
        self.feasicGain = 3 #4.7,7.8,14,25
        self.feasicShape = 2 #0.5,1,2,3
        self.feasicBuf = 0 #0 = OFF, 1 = ON

    def resetBoard(self):
        print("Reset")

    def initBoard(self):
        self.initWib()
        for femb in range(0,4,1):
            self.initFemb(femb)
        
    def initWib(self):
        #WIB initialization

        #set UDP ports to WIB registers
        self.femb.UDP_PORT_WREG = 32000
        self.femb.UDP_PORT_RREG = 32001
        self.femb.UDP_PORT_RREGRESP = 32002
        self.femb.REG_SLEEP = 0.001

        #register 2, LED
        self.femb.write_reg_bits(2 , 0, 0xFF, 0 )

        #clock select (firmware version dependent)
        #self.femb.write_reg_bits(4 , 2, 0x3, 2 )

        #initialize clock
        self.initSI5338()

        #return register interface to FEMB
        self.selectFemb(self.fembNum)

    def initFemb(self):
        if (self.fembNum < 0) or (self.fembNum >= self.NFEMBS ):
            return

        #FEMB power enable on WIB
        self.powerOnFemb(self.fembNum)

        #Make sure register interface is for correct FEMB
        self.selectFemb(self.fembNum)

        #check if FEMB register interface is working
        print("Checking register interface")
        regVal = self.femb.read_reg(6)
        if (regVal == None) or (regVal == -1):
            print("Error - FEMB register interface is not working.")
            print(" Will not initialize FEMB.")       
            return

        #turn off pulser
        self.femb.write_reg_bits( self.REG_FPGA_TP_EN, 0,0x1,0) #test pulse enable
        self.femb.write_reg_bits( self.REG_ASIC_TP_EN, 1,0x1,0) #test pulse enable
        self.femb.write_reg_bits( self.REG_DAC_SELECT, 8,0x1,0) #test pulse enable
        self.femb.write_reg_bits( self.REG_TP, 0,0x1F,0x00) #test pulse amplitude
        self.femb.write_reg_bits( self.REG_TP, 16,0xFFFF,0x100) #test pulse frequency
        self.femb.write_reg_bits( self.REG_TP, 8,0xFF,0x00) #test pulse delay

        #phase control
        self.femb.write_reg_bits(self.CLK_SELECT , 0, 0xFF, 0xDF ) #clock select
        self.femb.write_reg_bits(self.CLK_SELECT2 , 0, 0xFF, 0x20 ) #clock select 2
        self.femb.write_reg_bits(self.REG_LATCHLOC_3_TO_0 , 0, 0xFFFFFFFF, 0x00000000 ) #datashift
        self.femb.write_reg_bits(self.REG_LATCHLOC_7_TO_4 , 0, 0xFFFFFFFF, 0x00000000 ) #datashift

        #enable streaming
        self.femb.write_reg_bits(self.REG_HS_DATA , 0, 0x1, 1 ) #Enable streaming
        self.femb.write_reg_bits(self.REG_HS_DATA , 3, 0x1, 1 ) #Enable ADC data

        #Set FE ASIC SPI configuration registers
        self.configFeAsic()

        #Set ADC SPI configuration registers

        #EXTERNAL CLOCK STUFF

    #Test FEMB SPI working
    def checkFembSpi(self):        
        regVal = self.femb.read_reg(8)
        if regVal == None :
            regVal = 0
        print("About to check SPI: ", hex(regVal) )

        print("Check ASIC SPI")
        for regNum in range(self.REG_SPI_BASE,self.REG_SPI_BASE+72,1):
            val = self.femb.read_reg( regNum)
            if (val == None) or (val == -1):
                print("Error - FEMB register interface is not working.")
                continue
        #    print( str(hex(val)) )            

        print("Check ASIC SPI Readback")
        for regNum in range(self.REG_SPI_RDBACK_BASE,self.REG_SPI_RDBACK_BASE+72,1):
            val = self.femb.read_reg( regNum)
            if (val == None) or (val == -1):
                print("Error - FEMB register interface is not working.")
                continue
        #    print( str(hex(val)) )
        
        #Compare input to output
        
    #FEMB power enable on WIB
    def powerOnFemb(self,femb):
        fembVal = int(femb)
        if (fembVal < 0) or (fembVal > 3 ):
            return

        #set UDP ports to WIB registers
        self.femb.UDP_PORT_WREG = 32000
        self.femb.UDP_PORT_RREG = 32001
        self.femb.UDP_PORT_RREGRESP = 32002

        regBase = int( fembVal * 4)

        #FEMB power enable
        self.femb.write_reg_bits(8 , regBase + 0, 0x1, 1 ) #3.6V
        self.femb.write_reg_bits(8 , regBase + 1, 0x1, 1 ) #2.8V
        self.femb.write_reg_bits(8 , regBase + 2, 0x1, 1 ) #2.5V
        self.femb.write_reg_bits(8 , regBase + 3, 0x1, 1 ) #1.5V
        self.femb.write_reg_bits(8 , 16 + fembVal, 0x1, 1 ) #BIAS enable

        print("FEMB Power on: ", hex(self.femb.read_reg(8)))        
        
        #set UDP ports back to normal
        self.selectFemb(self.fembNum)

    def powerOffFemb(self,femb):
        fembVal = int(femb)
        if (fembVal < 0) or (fembVal > 3 ):
            return

        #set UDP ports to WIB registers
        self.femb.UDP_PORT_WREG = 32000
        self.femb.UDP_PORT_RREG = 32001
        self.femb.UDP_PORT_RREGRESP = 32002

        regBase = int( fembVal * 4)

        #FEMB power disable
        self.femb.write_reg_bits(8 , 16 + fembVal, 0x1, 0 ) #BIAS
        self.femb.write_reg_bits(8 , regBase + 0, 0x1, 0 ) #3.6V
        self.femb.write_reg_bits(8 , regBase + 1, 0x1, 0 ) #2.8V
        self.femb.write_reg_bits(8 , regBase + 2, 0x1, 0 ) #2.5V
        self.femb.write_reg_bits(8 , regBase + 3, 0x1, 0 ) #1.5V

        print("FEMB Power off: ", hex(self.femb.read_reg(8)))        
        
        #set UDP ports back to normal
        self.selectFemb(self.fembNum)
        
    def selectChannel(self,asic,chan):
        #print("Select channel")
        asicVal = int(asic)
        if (asicVal < 0 ) or (asicVal > self.NASICS):
            return

        #set UDP ports to WIB
        self.femb.UDP_PORT_WREG = 32000
        self.femb.UDP_PORT_RREG = 32001
        self.femb.UDP_PORT_RREGRESP = 32002

        #select ASIC
        #print("Selecting ASIC " + str(asicVal) )
        self.femb.write_reg_bits(self.REG_SEL_ASIC , self.REG_SEL_ASIC_LSB, 0xF, asicVal )

        #Note: WIB data format streams all 16 channels, don't need to select specific channel

        #set UDP ports back to normal
        self.selectFemb(self.fembNum)
    
    def configFeAsic(self):
        print("CONFIG ASICs")

        #global config varibles
        feasicLeakageVal = int( self.feasicLeakage ) #0 = 500pA, 1 = 100pA
        feasicLeakagex10Val = int( self.feasicLeakagex10 ) #0 = x1, 1 = x10
        acdcVal = int( self.feasicAcdc ) #DC = 0, AC = 1
        
        #channel specific variables
        testVal = int( self.feasicEnableTestInput )
        baseVal = int( self.feasicBaseline ) #0 = 900mV, 1 = 200mV
        gainVal = int( self.feasicGain )
        shapeVal = int( self.feasicShape )
        bufVal = int( self.feasicBuf ) #0 = OFF, 1 = ON

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
        if (feasicLeakageVal < 0 ) or (feasicLeakageVal > 1 ):
                return
        if (feasicLeakagex10Val < 0) or (feasicLeakagex10Val > 1):
                return

        chReg = 0
        #test capacitor, bit 7
        chReg = chReg + ((testVal & 0x01)<<7)

        #baseline control, bit 6
        baseVal = 1 - baseVal #assign 0 = 200mV, 1 = 900mV
        chReg = chReg +  ((baseVal & 0x01)<<6)
 
        #gain control, bits 4-5
        gainArray = [0,2,1,3]
        chReg = chReg + ((gainArray[gainVal] & 0x03)<<4)

        #shape control, bits 2-3
        shapeArray = [2,0,3,1] #I don't know why
        chReg = chReg + ((shapeArray[shapeVal] & 0x03)<<2)

        #buffer control, bit 0
        chReg = chReg + ((bufVal & 0x01)<<0)

        #construct the channel word
        chWord = (chReg << 24 ) + (chReg << 16) + (chReg << 8 ) + chReg

        asicReg = int(0)
        #asicReg = int(0x0A00)
        
        #leakage control 1, bit 0
        asicReg = asicReg + ((feasicLeakageVal & 0x01)<<0)
 
        #leakage control 2, bit 4
        asicReg = asicReg + ((feasicLeakagex10Val & 0x01)<<4)

        #AC/DC control

        #monitor control, bits 1-2

        #internal DAC enable, bit 8

        #external DAC enable, bit 9

        #DAC OUTPUT bits 8-9 , 0xA00 = external DAC

        #turn off HS data before register writes
        self.femb.write_reg_bits(9 , 0, 0x1, 0 )
        print("HS link turned off")
        time.sleep(2)

        #write SPI regs - very rough version
        chWord = (chReg << 24 ) + (chReg << 16) + (chReg << 8 ) + chReg
        for asic in range(0,self.NASICS,1):
            baseReg = self.REG_SPI_BASE + int(asic)*9
            self.femb.write_reg_bits( baseReg + 4 , 16, 0xFF, chReg ) #ch0
            self.femb.write_reg_bits( baseReg + 4 , 24, 0xFF, chReg ) #ch1
            self.femb.write_reg( baseReg + 5 ,  chWord) #ch2-5
            self.femb.write_reg( baseReg + 6 ,  chWord) #ch6-9
            self.femb.write_reg( baseReg + 7 ,  chWord) #ch10-13
            self.femb.write_reg_bits( baseReg + 8 , 0, 0xFF, chReg ) #ch14
            self.femb.write_reg_bits( baseReg + 8 , 8, 0xFF, chReg ) #ch15
            self.femb.write_reg_bits( baseReg + 8 , 16, 0xFFFF, asicReg ) #ASIC gen reg

        #run the SPI programming
        self.doAsicConfig()

        #turn HS link back on
        print("HS link turned back on")
        time.sleep(2)
        self.femb.write_reg_bits(9 , 0, 0x1, 1 )

    def doAsicConfig(self):
        #for regNum in range(self.REG_SPI_BASE,self.REG_SPI_BASE+72,1):
        #    regVal = self.femb.read_reg( regNum)
        #    print( str(regNum) + "\t" + str(hex(regVal)) )

        #Write ADC ASIC SPI
        print("Program ASIC SPI")
        self.femb.write_reg( self.REG_ASIC_RESET, 1)
        time.sleep(0.1)
        self.femb.write_reg( self.REG_ASIC_SPIPROG, 1)
        time.sleep(0.1)
        self.femb.write_reg( self.REG_ASIC_SPIPROG, 1)
        time.sleep(0.1)

        #for regNum in range(self.REG_SPI_RDBACK_BASE,self.REG_SPI_RDBACK_BASE+72,1):
        #    regVal = self.femb.read_reg( regNum)
        #    print( str(regNum) + "\t" + str(hex(regVal)) )


    def setInternalPulser(self,pulserEnable,pulseHeight):
        print("Set Pulser")

    def syncADC(self):
        print("Sync")

    def selectFemb(self, fembIn):
        fembVal = int( fembIn)
        if (fembVal < 0) or (fembVal > self.NFEMBS ):
            print("Invalid FEMB # requested")
            return
        self.fembNum = fembVal

        #set data streaming for requested FEMB
        #set UDP ports to WIB
        self.femb.UDP_PORT_WREG = 32000
        self.femb.UDP_PORT_RREG = 32001
        self.femb.UDP_PORT_RREGRESP = 32002
        self.femb.write_reg_bits(7 , 16, 0x3, self.fembNum )

        #set read/write ports
        if fembVal == 0:
            self.femb.UDP_PORT_WREG = 32016
            self.femb.UDP_PORT_RREG = 32017
            self.femb.UDP_PORT_RREGRESP = 32018

        if fembVal == 1:
            self.femb.UDP_PORT_WREG = 32032
            self.femb.UDP_PORT_RREG = 32033
            self.femb.UDP_PORT_RREGRESP = 32034

        if fembVal == 2:
            self.femb.UDP_PORT_WREG = 32048
            self.femb.UDP_PORT_RREG = 32049
            self.femb.UDP_PORT_RREGRESP = 32050

        if fembVal == 3:
            self.femb.UDP_PORT_WREG = 32064
            self.femb.UDP_PORT_RREG = 32065
            self.femb.UDP_PORT_RREGRESP = 32066

        #slow down register interface for FEMBs
        self.femb.REG_SLEEP = 0.05

    def initSI5338(self):
        #set UDP ports to WIB
        self.femb.UDP_PORT_WREG = 32000
        self.femb.UDP_PORT_RREG = 32001
        self.femb.UDP_PORT_RREGRESP = 32002
        self.femb.REG_SLEEP = 0.001
       
        #disable all outputs
        #i2c_reg_wr(i2c_bus_base_addr, si5338_i2c_addr, 230, 0x10);
        self.write_reg_SI5338(230,0x10)

        #pause lol
	#i2c_reg_wr(i2c_bus_base_addr, si5338_i2c_addr, 241, 0xE5);
        self.write_reg_SI5338(241,0xE5)

        import femb_python.configuration.femb_config_wib_sbnd_si5338_data
        for word in range(0,349,1):
            wordNum = int(word)
            addr = int(femb_python.configuration.femb_config_wib_sbnd_si5338_data.data[3*wordNum+0])
            val = int(femb_python.configuration.femb_config_wib_sbnd_si5338_data.data[3*wordNum+1])
            mask = int(femb_python.configuration.femb_config_wib_sbnd_si5338_data.data[3*wordNum+2])

            if wordNum % 10 == 0:
                print( "Writing SI5338 register # " + str(wordNum) + " out of 349") 

            if mask == 0:
                continue

            writeVal = val
            if mask != 0xFF:
                curr_val = self.read_reg_SI5338(addr)
                clear_curr_val = curr_val & (~mask)
                clear_new_val = val & mask
                writeVal = clear_curr_val | clear_new_val
            self.write_reg_SI5338(addr,writeVal)
            #print(str(addr) + "\t" + str(writeVal)) 

        #validate input clock status
	#i2c_reg_rd(i2c_bus_base_addr, si5338_i2c_addr, 218);
        clkStatus = (self.read_reg_SI5338(218) & 0x04)
        count = 0
        while count < 100:
            clkStatus = (self.read_reg_SI5338(218) & 0x04)
            if clkStatus != 0x04:
                break
            count = count + 1
        if clkStatus == 0x04:
            print( "Did not finish clock initialization")
            return

        #configure pll
        pllWord = int(femb_python.configuration.femb_config_wib_sbnd_si5338_data.data[3*49+1])
        self.write_reg_SI5338(49,(0x7F & pllWord)) 
        
        #reset the chip
        self.write_reg_SI5338(246,0x02)

        time.sleep(0.1)

        #restart lol
        self.write_reg_SI5338(241,0x65)

        #validate pll
        pllStatus = self.read_reg_SI5338(218)
        count = 0
        while count < 100:
            pllStatus = self.read_reg_SI5338(218)
            if pllStatus == 0 :
                break
            count = count + 1
        if pllStatus != 0:
            print("Did not finish clock initialization")
            return

        #copy FCAL values to active registers 
        fcalVal = self.read_reg_SI5338(235)
        self.write_reg_SI5338(45,fcalVal)
 
        fcalVal = self.read_reg_SI5338(236)
        self.write_reg_SI5338(46,fcalVal)

        fcalVal = self.read_reg_SI5338(237)
        fcalVal = ( 0x14 | ( fcalVal & 0x3) )
        self.write_reg_SI5338(47,fcalVal)

        #set pll to use FCAL values
        #i2c_reg_wr(i2c_bus_base_addr, si5338_i2c_addr, 49, 0x80|SI5338Reg[49*3+1]);
        setPllWord = ( 0x80 | pllWord )
        self.write_reg_SI5338(49, setPllWord )

        #enable outputs
        self.write_reg_SI5338(230,0x00)
        print("Done initalizing Si5338 clock")

        #set UDP ports back to normal
        self.selectFemb(self.fembNum)

    def read_reg_SI5338(self,addr):
        addrVal = int(addr)
        if (addrVal < 0 ) or (addrVal > 255):
            return
        self.femb.write_reg( 11, 0)
        self.femb.write_reg( 12, addrVal)
        self.femb.write_reg( 15, 0xE0)

        self.femb.write_reg( 10, 1)
        self.femb.write_reg( 10, 0)

        self.femb.write_reg( 11, 1)

        self.femb.write_reg( 10, 2)
        self.femb.write_reg( 10, 0)

        regVal = self.femb.read_reg(14)
        return regVal

    def write_reg_SI5338(self,addr,val):
        addrVal = int(addr)
        if (addrVal < 0 ) or (addrVal > 255):
            return
        regVal = int(val)
        if (regVal < 0 ) or (regVal > 255):
            return
        self.femb.write_reg( 11, 1)
        self.femb.write_reg( 12, addrVal)
        self.femb.write_reg( 13, regVal)

        self.femb.write_reg( 10, 1)
        self.femb.write_reg( 10, 0)

    def setFpgaPulser(self,enable,dac):
        enableVal = int(enable)
        if (enableVal < 0 ) or (enableVal > 1 ) :
            print( "femb_config_femb : setFpgaPulser - invalid enable value")
            return
        dacVal = int(dac)
        if ( dacVal < 0 ) or ( dacVal > 0x3F ) :
            print( "femb_config_femb : setFpgaPulser - invalid dac value")
            return

        #set pulser enable bit
        if enableVal == 1 :
            self.femb.write_reg( self.EXT_TP_EN, 0x2) #this register is confusing, check
        else :
            self.femb.write_reg( self.EXT_TP_EN, 0x3) #pulser disabled

        #connect channel test input to external pin
        for asic in range(0,self.NASICS,1):
            baseReg = self.REG_SPI_BASE + int(asic)*9
            if enableVal == 1:
                self.femb.write_reg_bits( baseReg + 8 , 24, 0x3, 0x2 ) #ASIC gen reg
            else:
                self.femb.write_reg_bits( baseReg + 8 , 24, 0x3, 0x0 ) #ASIC gen reg

        self.doAsicConfig()

        self.femb.write_reg_bits( self.REG_FPGA_TP_EN, 0,0x3,0x1) #test pulse enable
        self.femb.write_reg_bits( self.REG_FPGA_TP_EN, 8,0x1,1) #test pulse enable
        self.femb.write_reg_bits( self.REG_TP , 0, 0x3F, dacVal ) #TP Amplitude
        self.femb.write_reg_bits( self.REG_TP , 8, 0xFF, 219 ) #DLY
        self.femb.write_reg_bits( self.REG_TP , 16, 0xFFFF, 197 ) #FREQ

    def setInternalPulser(self,enable,dac):
        enableVal = int(enable)
        if (enableVal < 0 ) or (enableVal > 1 ) :
                print( "femb_config_femb : setInternalPulser - invalid enable value")
                return
        dacVal = int(dac)
        if ( dacVal < 0 ) or ( dacVal > 0x3F ) :
                print( "femb_config_femb : setInternalPulser - invalid dac value")
                return

        #set pulser enable bit
        if enableVal == 1 :
                self.femb.write_reg( self.INT_TP_EN, 0x2) #this register is confusing, check
        else :
                self.femb.write_reg( self.INT_TP_EN, 0x3) #pulser disabled

        dacVal = (dacVal & 0x3F)
        newDacVal = int('{:08b}'.format(dacVal)[::-1], 2)

        asicWord = ((newDacVal << 8 ) & 0xFFFF)
        if enableVal == 1 :
                asicWord = asicWord + (0x1 << 8)

        #connect channel test input to external pin
        for asic in range(0,self.NASICS,1):
            baseReg = self.REG_SPI_BASE + int(asic)*9
            if enableVal == 1:
                self.femb.write_reg_bits( baseReg + 8 , 24, 0xFF, newDacVal )
                self.femb.write_reg_bits( baseReg + 8 , 24, 0x3, 0x1 ) #ASIC gen reg
            else:
                self.femb.write_reg_bits( baseReg + 8 , 24, 0xFF, 0x0 ) #ASIC gen reg

        self.doAsicConfig()

        self.femb.write_reg_bits( self.REG_ASIC_TP_EN , 0, 0x3, 0x2 )
        self.femb.write_reg_bits( self.REG_DAC_SELECT, 8,0x1,0) #test pulse enable
        self.femb.write_reg_bits( self.REG_TP , 0, 0x3F, dacVal ) #TP Amplitude
        self.femb.write_reg_bits( self.REG_TP , 8, 0xFF, 31 ) #DLY
        self.femb.write_reg_bits( self.REG_TP , 16, 0xFFFF, 1000 ) #FREQ

    def checkFirmwareVersion(self):
        #set UDP ports to WIB
        self.femb.UDP_PORT_WREG = 32000
        self.femb.UDP_PORT_RREG = 32001
        self.femb.UDP_PORT_RREGRESP = 32002

        #check WIB fw version reg
        wibVerReg = self.femb.read_reg(255)
        if wibVerReg == None :
            return False
        wibVerReg = (wibVerReg & 0xFFF)

        #set UDP ports back to normal
        self.selectFemb(self.fembNum)
        fembVerReg = self.femb.read_reg(257)
        if fembVerReg == None :
            return False
        fembVerReg = (fembVerReg & 0xFFF)
        #print( "FEMB Firmware Version HERE : " + str(hex(fembVerReg)) )
        if wibVerReg != 0x109 :
            print("Invalid WIB firmware version detected " + str(wibVerReg) + ", this configuration requires version 0x109")
            return False
        if fembVerReg != 0x308 :
            print("Invalid FEMB firmware version detected " + str(wibVerReg) + ", this configuration requires version 0x308")
            return False
        
        print( "WIB Firmware Version : " + str(hex(wibVerReg)) )
        print( "FEMB Firmware Version : " + str(hex(fembVerReg)) )

        #good firmware id
        return True
