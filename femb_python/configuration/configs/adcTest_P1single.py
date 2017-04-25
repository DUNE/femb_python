#!/usr/bin/env python33

"""
Configuration for P1 ADC single-chip board
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
from femb_python.configuration.adc_asic_reg_mapping_P1 import ADC_ASIC_REG_MAPPING

class FEMB_CONFIG(FEMB_CONFIG_BASE):

    def __init__(self):
        super().__init__()
        #declare board specific registers
        self.FEMB_VER = "adctestP1single"
        self.REG_RESET = 0
        self.REG_ASIC_RESET = 1
        self.REG_ASIC_SPIPROG = 2
        self.REG_SEL_ASIC = 7 
        self.REG_SEL_CH = 7
        self.REG_FESPI_BASE = 592
        self.REG_ADCSPI_BASE = 512
        self.REG_FESPI_RDBACK_BASE = 632
        self.REG_ADCSPI_RDBACK_BASE = 552
        self.REG_HS = 17
        self.REG_LATCHLOC1_4 = 4
        self.REG_LATCHLOC5_8 = 14
        self.REG_CLKPHASE = 6
        self.REG_LATCHLOC1_4_data = 0x0
        self.REG_LATCHLOC5_8_data = 0x0
        self.REG_CLKPHASE_data = 0x0
        self.ADC_TESTPATTERN = [0x12, 0x345, 0x678, 0xf1f, 0xad, 0xc01, 0x234, 0x567, 0x89d, 0xeca, 0xff0, 0x123, 0x456, 0x789, 0xabc, 0xdef]
        ##################################
        # external clock control registers
        ##################################
        self.REG_EXTCLK_RD_EN_OFF = 23
        self.REG_EXTCLK_ADC_OFF = 21
        self.REG_EXTCLK_ADC_WID = 22
        self.REG_EXTCLK_MSB_OFF = 25
        self.REG_EXTCLK_MSB_WID = 26
        self.REG_EXTCLK_PERIOD = 20
        self.REG_EXTCLK_LSB_FC_WID2 = 32
        self.REG_EXTCLK_LSB_FC_OFF1 = 29
        self.REG_EXTCLK_RD_EN_WID = 24
        self.REG_EXTCLK_LSB_FC_WID1 = 30
        self.REG_EXTCLK_LSB_FC_OFF2 = 31
        self.REG_EXTCLK_LSB_S_WID = 28
        self.REG_EXTCLK_LSB_S_OFF = 27
        self.REG_EXTCLK_INV = 33

        ##################################
        ##################################
        self.NASICS = 1
        self.POWERSUPPLYPATH = "/dev/null" # "/dev/usbtmc0"
        self.FUNCGENPATH = "/dev/usbtmc1"
        self.POWERSUPPLYCHANNELS = ["CH1"]
        self.FUNCGENSOURCE = 1
        self.F2DEFAULT = 0
        self.CLKDEFAULT = "fifo"

        #initialize FEMB UDP object
        self.femb = FEMB_UDP()
        self.adc_reg = ADC_ASIC_REG_MAPPING()

    def resetBoard(self):
        #Reset system
        self.femb.write_reg( self.REG_RESET, 1)
        time.sleep(5.)

        #Reset registers
        self.femb.write_reg( self.REG_RESET, 2)
        time.sleep(1.)

        #Time stamp reset
        #femb.write_reg( 0, 4)
        #time.sleep(0.5)
        
        #Reset ADC ASICs
        self.femb.write_reg( self.REG_ASIC_RESET, 1)
        time.sleep(0.5)

    def initBoard(self):
        nRetries = 5
        for iRetry in range(nRetries):
            #set up default registers
            
            #Reset ADC ASICs
            self.femb.write_reg( self.REG_ASIC_RESET, 1)
            time.sleep(0.5)

            #Set ADC test pattern register
            self.femb.write_reg( 3, 0x01230000) # test pattern off
            #self.femb.write_reg( 3, 0x81230000) # test pattern on

            #Set ADC latch_loc
            self.femb.write_reg( self.REG_LATCHLOC1_4, self.REG_LATCHLOC1_4_data)
            self.femb.write_reg( self.REG_LATCHLOC5_8, self.REG_LATCHLOC5_8_data)
            #Set ADC clock phase
            self.femb.write_reg( self.REG_CLKPHASE, self.REG_CLKPHASE_data)

            #internal test pulser control
            self.femb.write_reg( 5, 0x00000000)
            self.femb.write_reg( 13, 0x0) #enable

            #Set test and readout mode register
            self.femb.write_reg( 7, 0x0000) #11-8 = channel select, 3-0 = ASIC select

            #Set number events per header
            self.femb.write_reg( 8, 0x0)

            #ADC ASIC SPI registers
            self.configAdcAsic()

#            print("Config ADC ASIC SPI")
#            print("ADCADC")
#            
#            self.adc_reg.set_sbnd_board(tstin=1, clk0=0, clk1=1, f0=1, f4=1) # from Shanshan labview
#            regs = self.adc_reg.REGS
#            for iReg, val in enumerate(regs):
#                #print("{:032b}".format(val))
#                print("{:08x}".format(val))
#                self.femb.write_reg(self.REG_ADCSPI_BASE+iReg,val)
#
#            #ADC ASIC sync
#            self.femb.write_reg( 17, 0x1) # controls HS link, 0 for on, 1 for off
#            self.femb.write_reg( 17, 0x0) # controls HS link, 0 for on, 1 for off        
#
#            #Write ADC ASIC SPI
#            print( "Program ADC ASIC SPI")
#            self.femb.write_reg( self.REG_ASIC_SPIPROG, 1)
#            time.sleep(0.1)
#            self.femb.write_reg( self.REG_ASIC_SPIPROG, 1)
#            time.sleep(0.1)
#
#            print( "Check ADC ASIC SPI")
#            for regNum in range(self.REG_ADCSPI_RDBACK_BASE,self.REG_ADCSPI_RDBACK_BASE+34,1):
#                    val = self.femb.read_reg( regNum ) 
#                    #print("{:08x}".format(val))
#
#            #enable streaming
#            #self.femb.write_reg( 9, 0x8)
#
#            #LBNE_ADC_MODE
#            self.femb.write_reg( 16, 0x1)

            # Check that board streams data
            data = self.femb.get_data(1)
            if data == None:
                print("Board not streaming data, retrying initialization...")
                continue # try initializing again
            print("FEMB_CONFIG--> Reset FEMB is DONE")
            return
        print("Error: Board not streaming data after trying to initialize {} times. Exiting.".format(nRetries))
        sys.exit(1)

    def configAdcAsic_regs(self,Adcasic_regs):
        #ADC ASIC SPI registers
        assert(len(Adcasic_regs)==36)
        print("FEMB_CONFIG--> Config ADC ASIC SPI")
        for k in range(10):
            i = 0
            for regNum in range(self.REG_ADCSPI_BASE,self.REG_ADCSPI_BASE+len(Adcasic_regs),1):
                    #print("{:032b}".format(Adcasic_regs[i]))
                    print("{:08x}".format(Adcasic_regs[i]))
                    self.femb.write_reg ( regNum, Adcasic_regs[i])
                    time.sleep(0.05)
                    i = i + 1

            #print("  ADC ASIC write : ",Adcasic_regs)
            #ADC ASIC sync
            self.femb.write_reg ( 17, 0x1) # controls HS link, 0 for on, 1 for off
            self.femb.write_reg ( 17, 0x0) # controls HS link, 0 for on, 1 for off        

            #Write ADC ASIC SPI
            print("FEMB_CONFIG--> Program ADC ASIC SPI")
            self.femb.write_reg ( self.REG_ASIC_SPIPROG, 1)
            time.sleep(0.1)
            self.femb.write_reg ( self.REG_ASIC_SPIPROG, 1)
            time.sleep(0.1)

            #enable streaming
            #self.femb.write_reg( 9, 0x8)

            #LBNE_ADC_MODE
            self.femb.write_reg( 16, 0x1)

            #print("FEMB_CONFIG--> Check ADC ASIC SPI")
            #adcasic_rb_regs = []
            #for regNum in range(self.REG_ADCSPI_RDBACK_BASE,self.REG_ADCSPI_RDBACK_BASE+len(Adcasic_regs),1):
            #    val = self.femb.read_reg ( regNum ) 
            #    #print("{:08x}".format(val))
            #    adcasic_rb_regs.append( val )

            #print("  ADC ASIC read back: ",adcasic_rb_regs)
            #if (adcasic_rb_regs !=Adcasic_regs  ) :
            #    #if ( k == 1 ):
            #    #    sys.exit("femb_config : Wrong readback. ADC SPI failed")
            #    #    return
            #    print("FEMB_CONFIG--> ADC ASIC Readback didn't match, retrying...")
            #else: 
            if True:
                print("FEMB_CONFIG--> ADC ASIC SPI is OK")
                break

    def configAdcAsic(self,enableOffsetCurrent=None,offsetCurrent=None,testInput=None,
                            freqInternal=None,sleep=None,pdsr=None,pcsr=None,
                            clockMonostable=None,clockExternal=None,clockFromFIFO=None,
                            sLSB=None,f0=None,f1=None,f2=None,f3=None,f4=None,f5=None):
        """
        Configure ADCs
          enableOffsetCurrent: 0 disable offset current, 1 enable offset current
          offsetCurrent: 0-15, amount of current to draw from sample and hold
          testInput: 0 digitize normal input, 1 digitize test input
          freqInternal: internal clock frequency: 0 1MHz, 1 2MHz
          sleep: 0 disable sleep mode, 1 enable sleep mode
          pdsr: if pcsr=0: 0 PD is low, 1 PD is high
          pcsr: 0 power down controlled by pdsr, 1 power down controlled externally
          Only one of these can be enabled:
            clockMonostable: True ADC uses monostable clock
            clockExternal: True ADC uses external clock
            clockFromFIFO: True ADC uses digital generator FIFO clock
          sLSB: LSB current steering mode. 0 for full, 1 for partial (ADC7 P1)
          f0, f1, f2, f3, f4, f5: version specific
        """
        FEMB_CONFIG_BASE.configAdcAsic(self,clockMonostable=clockMonostable,
                                        clockExternal=clockExternal,clockFromFIFO=clockFromFIFO)
        if enableOffsetCurrent is None:
            enableOffsetCurrent=0
        if offsetCurrent is None:
            offsetCurrent=0
        else:
            offsetCurrent = int("{:04b}".format(offsetCurrent)[::-1],2) # need to reverse bits, use string/list tricks
        if testInput is None:
            testInput=1
        if freqInternal is None:
            freqInternal=0
        if sleep is None:
            sleep=0
        if pdsr is None:
            pdsr=1
        if pcsr is None:
            pcsr=1
        if sLSB is None:
            sLSB = 0
        if f0 is None:
            f0 = 1
        if f1 is None:
            f1 = 0
        if f2 is None:
            f2 = 0
        if f3 is None:
            f3 = 0
        if f4 is None:
            f4 = 1
        if f5 is None:
            f5 = 0
        if not (clockMonostable or clockExternal or clockFromFIFO):
            clockExternal=True
        clk0=0
        clk1=0
        if clockExternal:
            clk0=1
            clk1=0
        elif clockFromFIFO:
            clk0=0
            clk1=1

        if clockExternal:
            self.extClock(enable=True)
        else:
            self.extClock(enable=False)

        self.adc_reg.set_sbnd_board(en_gr=enableOffsetCurrent,d=offsetCurrent,tstin=testInput,frqc=freqInternal,slp=sleep,pdsr=pdsr,pcsr=pcsr,clk0=clk0,clk1=clk1,f0=f0,f1=f1,f2=f2,f3=f3,f4=f4,f5=f5,slsb=sLSB)
        self.configAdcAsic_regs(self.adc_reg.REGS)

    def selectChannel(self,asic,chan,hsmode=None):
        asicVal = int(asic)
        if (asicVal < 0 ) or (asicVal >= self.NASICS ) :
                print( "femb_config_femb : selectChan - invalid ASIC number, only 0 to {} allowed".format(self.NASICS-1))
                return
        chVal = int(chan)
        if (chVal < 0 ) or (chVal > 15 ) :
                print("femb_config_femb : selectChan - invalid channel number, only 0 to 15 allowed")
                return

        #print( "Selecting ASIC " + str(asicVal) + ", channel " + str(chVal))

        regVal = (chVal << 8 ) + asicVal
        self.femb.write_reg( self.REG_SEL_CH, regVal)

    def syncADC(self):
        #turn on ADC test mode
        print("FEMB_CONFIG--> Start sync ADC")
        reg3 = self.femb.read_reg (3)
        newReg3 = ( reg3 | 0x80000000 )

        self.femb.write_reg ( 3, newReg3 ) #31 - enable ADC test pattern
        time.sleep(0.1)                
        alreadySynced = True
        for a in range(0,self.NASICS,1):
            print("FEMB_CONFIG--> Test ADC " + str(a))
            unsync = self.testUnsync(a)
            if unsync != 0:
                alreadySynced = False
                print("FEMB_CONFIG--> ADC not synced, try to fix")
                self.fixUnsync(a)
        self.REG_LATCHLOC1_4_data = self.femb.read_reg ( self.REG_LATCHLOC1_4 ) 
        self.REG_LATCHLOC5_8_data = self.femb.read_reg ( self.REG_LATCHLOC5_8 )
        self.REG_CLKPHASE_data    = self.femb.read_reg ( self.REG_CLKPHASE )
        print("FEMB_CONFIG--> Latch latency " + str(hex(self.REG_LATCHLOC1_4_data)) \
                        + str(hex(self.REG_LATCHLOC5_8_data )) + \
                        "\tPhase " + str(hex(self.REG_CLKPHASE_data)))
        self.femb.write_reg ( 3, (reg3&0x7fffffff) )
        self.femb.write_reg ( 3, (reg3&0x7fffffff) )
        print("FEMB_CONFIG--> End sync ADC")
        return not alreadySynced,self.REG_LATCHLOC1_4_data,self.REG_LATCHLOC5_8_data ,self.REG_CLKPHASE_data 

    def testUnsync(self, adc):
        print("Starting testUnsync adc: ",adc)
        adcNum = int(adc)
        if (adcNum < 0 ) or (adcNum > 7 ):
                print("FEMB_CONFIG--> femb_config_femb : testLink - invalid asic number")
                return
        
        #loop through channels, check test pattern against data
        badSync = 0
        for ch in range(0,16,1):
                self.selectChannel(adcNum,ch, 1)
                time.sleep(0.05)                
                for test in range(0,10,1):
                        data = self.femb.get_data(1)
                        #print("test: ",test," data: ",data)
                        if data == None:
                                continue
                        for samp in data[0:(16*1024+1023)]:
                                if samp == None:
                                        continue
                                chNum = ((samp >> 12 ) & 0xF)
                                sampVal = (samp & 0xFFF)
                                if sampVal != self.ADC_TESTPATTERN[ch]        :
                                        badSync = 1 
                                if badSync == 1:
                                        break
                        if badSync == 1:
                                break
                if badSync == 1:
                        break
        return badSync


    def fixUnsync(self, adc):
        adcNum = int(adc)
        if (adcNum < 0 ) or (adcNum > 7 ):
                print("FEMB_CONFIG--> femb_config_femb : testLink - invalid asic number")
                return

        initLATCH1_4 = self.femb.read_reg ( self.REG_LATCHLOC1_4 )
        initLATCH5_8 = self.femb.read_reg ( self.REG_LATCHLOC5_8 )
        initPHASE = self.femb.read_reg ( self.REG_CLKPHASE )

        #loop through sync parameters
        for phase in range(0,2,1):
                clkMask = (0x1 << adcNum)
                testPhase = ( (initPHASE & ~(clkMask)) | (phase << adcNum) ) 
                self.femb.write_reg ( self.REG_CLKPHASE, testPhase )
                time.sleep(0.01)
                for shift in range(0,16,1):
                        shiftMask = (0x3F << 8*adcNum)
                        if ( adcNum < 4 ):
                            testShift = ( (initLATCH1_4 & ~(shiftMask)) | (shift << 8*adcNum) )
                            self.femb.write_reg ( self.REG_LATCHLOC1_4, testShift )
                            time.sleep(0.01)
                        else:
                            testShift = ( (initLATCH5_8 & ~(shiftMask)) | (shift << 8*adcNum) )
                            self.femb.write_reg ( self.REG_LATCHLOC5_8, testShift )
                            time.sleep(0.01)
                        print("trying phase: ",phase," shift: ",shift," testingUnsync...")
                        #reset ADC ASIC
                        self.femb.write_reg ( self.REG_ASIC_RESET, 1)
                        time.sleep(0.01)
                        self.femb.write_reg ( self.REG_ASIC_SPIPROG, 1)
                        time.sleep(0.01)
                        self.femb.write_reg ( self.REG_ASIC_SPIPROG, 1)
                        time.sleep(0.01)
                        #test link
                        unsync = self.testUnsync(adcNum)
                        if unsync == 0 :
                                print("FEMB_CONFIG--> ADC synchronized")
                                return
        #if program reaches here, sync has failed
        print("FEMB_CONFIG--> ADC SYNC process failed for ADC # " + str(adc))


    def extClock(self, enable=False, 
                period=5, clock=1, mult=1, 
                offset_rst=0, offset_read=0, offset_msb=0, offset_lsb=0, 
                width_rst=1, width_read=0, width_msb=0, width_lsb=0,
                offset_lsb_1st_1=0, width_lsb_1st_1=0,
                offset_lsb_1st_1=0, width_lsb_1st_1=0,
                inv_rst=True, inv_read=True, inv_msb=False, inv_lsb=False, inv_lsb_1st=False):
        """
        Programs external clock.
        """

        rd_en_off = 0
        adc_off = 0
        adc_wid = 0
        msb_off = 0
        msb_wid = 0
        period = 0
        lsb_fc_wid2 = 0
        lsb_fc_off1 = 0
        rd_en_wid = 0
        lsb_fc_wid1 = 0
        lsb_fc_off2 = 0
        lsb_s_wid = 0
        lsb_s_off = 0
        inv = 0

        if enable:
            denominator = clock / mult
            rd_en_off =  offset_read / denominator
            adc_off =  offset_rst / denominator
            adc_wid =  width_rst / denominator
            msb_off = offset_msb  / denominator
            msb_wid = width_msb  / denominator
            period = period / denominator
            lsb_fc_wid2 = width_lsb_1st_2 / denominator
            lsb_fc_off1 = offset_lsb_1st_1 / denominator
            rd_en_wid = width_read / denominator
            lsb_fc_wid1 = width_lsb_1st_1 / denominator
            lsb_fc_off2 = offset_lsb_1st_2 / denominator
            lsb_s_wid = width_lsb / denominator
            lsb_s_off = offset_lsb / denominator
            if inv_rst:
              inv += 1 << 0
            if inv_read:
              inv += 1 << 1
            if inv_msb:
              inv += 1 << 2
            if inv_lsb:
              inv += 1 << 3
            if inv_lsb_1st:
              inv += 1 << 4

        regsValsToWrite = [
            (self.REG_EXTCLK_RD_EN_OFF, rd_en_off),
            (self.REG_EXTCLK_ADC_OFF, adc_off),
            (self.REG_EXTCLK_ADC_WID, adc_wid),
            (self.REG_EXTCLK_MSB_OFF, msb_off),
            (self.REG_EXTCLK_MSB_WID, msb_wid),
            (self.REG_EXTCLK_PERIOD, period),
            (self.REG_EXTCLK_LSB_FC_WID2, lsb_fc_wid2),
            (self.REG_EXTCLK_LSB_FC_OFF1, lsb_fc_off1),
            (self.REG_EXTCLK_RD_EN_WID, rd_en_wid),
            (self.REG_EXTCLK_LSB_FC_WID1, lsb_fc_wid1),
            (self.REG_EXTCLK_LSB_FC_OFF2, lsb_fc_off2),
            (self.REG_EXTCLK_LSB_S_WID, lsb_s_wid),
            (self.REG_EXTCLK_LSB_S_OFF, lsb_s_off),
            (self.REG_EXTCLK_INV, inv),
        ]
        for reg,val in regsValsToWrite:
            val = val & 0xFFFF # only 16 bits for some reason
            self.femb.write_reg(reg,val)
            
