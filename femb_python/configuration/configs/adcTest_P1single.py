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
import os.path
import subprocess
from femb_python.femb_udp import FEMB_UDP
from femb_python.configuration.config_base import FEMB_CONFIG_BASE, FEMBConfigError, SyncADCError, InitBoardError, ConfigADCError, ReadRegError
from femb_python.configuration.adc_asic_reg_mapping_P1 import ADC_ASIC_REG_MAPPING
from femb_python.test_instrument_interface.keysight_33600A import Keysight_33600A
from femb_python.test_instrument_interface.rigol_dp800 import RigolDP800

class FEMB_CONFIG(FEMB_CONFIG_BASE):

    def __init__(self,exitOnError=True):
        super().__init__(exitOnError=exitOnError)
        #declare board specific registers
        self.FEMB_VER = "adctestP1single"
        self.REG_RESET = 0
        self.REG_ASIC_RESET = 1
        self.REG_ASIC_SPIPROG = 2
        self.REG_SEL_CH = 7
        self.REG_HS = 17
        self.REG_FESPI_BASE = 0x250 # 592 in decimal
        self.REG_ADCSPI_BASE = 0x200 # 512 in decimal
        self.REG_FESPI_RDBACK_BASE = 0x278 # 632 in decimal
        self.REG_ADCSPI_RDBACK_BASE = 0x228 # 552 in decimal
        self.REG_LATCHLOC1_4 = 4
        self.REG_LATCHLOC5_8 = 14
        self.REG_CLKPHASE = 6

        self.REG_LATCHLOC1_4_data = 0x6
        self.REG_LATCHLOC5_8_data = 0x0
        self.REG_CLKPHASE_data = 0xfffc0000

        self.REG_LATCHLOC1_4_data_1MHz = 0x5
        self.REG_LATCHLOC5_8_data_1MHz = 0x0
        self.REG_CLKPHASE_data_1MHz = 0xffff0000

        self.REG_LATCHLOC1_4_data_cold = 0x6
        self.REG_LATCHLOC5_8_data_cold = 0x0
        self.REG_CLKPHASE_data_cold = 0xfffc0000

        self.REG_LATCHLOC1_4_data_1MHz_cold = 0x4
        self.REG_LATCHLOC5_8_data_1MHz_cold = 0x0
        self.REG_CLKPHASE_data_1MHz_cold = 0xfffc0001

        self.ADC_TESTPATTERN = [0x12, 0x345, 0x678, 0xf1f, 0xad, 0xc01, 0x234, 0x567, 0x89d, 0xeca, 0xff0, 0x123, 0x456, 0x789, 0xabc, 0xdef]

        ##################################
        # external clock control registers
        ##################################
        self.FPGA_FREQ_MHZ = 200 # frequency of FPGA clock in MHz
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
        self.FUNCGENINTER = Keysight_33600A("/dev/usbtmc1",1)
        self.POWERSUPPLYINTER = RigolDP800("/dev/usbtmc0",["CH2","CH3","CH1"]) # turn on CH2 first
        self.F2DEFAULT = 0
        self.CLKDEFAULT = "fifo"

        ## Firmware update related variables
        self.FIRMWAREPATH2MHZ = "/opt/sw/releases/femb_firmware-0.1.0/adc_tester/S7_2M_SBND_FPGA.sof"
        self.FIRMWAREPATH1MHZ = "/opt/sw/releases/femb_firmware-0.1.0/adc_tester/S7_1M_SBND_FPGA.sof"
        self.FIRMWAREPROGEXE = "/opt/sw/intelFPGA/17.0/qprogrammer/bin/quartus_pgm"
        #self.FIRMWAREPROGCABLE = "USB-Blaster"
        self.FIRMWAREPROGCABLE = "USB-BlasterII"
        self.SAMPLERATE = 2e6

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

            readback = self.femb.read_reg(0)
            if readback is None:
                if self.exitOnError:
                    print("FEMB_CONFIG: Error reading register 0, Exiting.")
                    sys.exit(1)
                else:
                    raise ReadRegError("Couldn't read register 0")

            #Set ADC test pattern register
            self.femb.write_reg( 3, 0x01170000) # test pattern off
            #self.femb.write_reg( 3, 0x81170000) # test pattern on

            #Set ADC latch_loc and clock phase
            latchloc1 = None
            latchloc5 = None
            clockphase = None
            if self.SAMPLERATE == 1e6:
                if self.COLD:
                    print("Using 1 MHz cold latchloc/clockphase")
                    latchloc1 = self.REG_LATCHLOC1_4_data_1MHz_cold
                    latchloc5 = self.REG_LATCHLOC5_8_data_1MHz_cold
                    clockphase = self.REG_CLKPHASE_data_1MHz_cold
                else:
                    print("Using 1 MHz warm latchloc/clockphase")
                    latchloc1 = self.REG_LATCHLOC1_4_data_1MHz
                    latchloc5 = self.REG_LATCHLOC5_8_data_1MHz
                    clockphase = self.REG_CLKPHASE_data_1MHz
            else: # use 2 MHz values
                if self.COLD:
                    print("Using 2 MHz cold latchloc/clockphase")
                    latchloc1 =  self.REG_LATCHLOC1_4_data_cold
                    latchloc5 =  self.REG_LATCHLOC5_8_data_cold
                    clockphase =  self.REG_CLKPHASE_data_cold
                else:
                    print("Using 2 MHz warm latchloc/clockphase")
                    latchloc1 = self.REG_LATCHLOC1_4_data
                    latchloc5 = self.REG_LATCHLOC5_8_data
                    clockphase = self.REG_CLKPHASE_data

            print("Initializing with Latch Loc: {:#010x} {:#010x} Clock Phase: {:#010x}".format(latchloc1,latchloc5,clockphase))
            self.femb.write_reg( self.REG_LATCHLOC1_4, latchloc1)
            self.femb.write_reg( self.REG_LATCHLOC5_8, latchloc5)
            for iTry in range(5):
                self.femb.write_reg( self.REG_CLKPHASE, ~clockphase)
                time.sleep(0.05)
                self.femb.write_reg( self.REG_CLKPHASE, ~clockphase)
                time.sleep(0.05)
                self.femb.write_reg( self.REG_CLKPHASE, clockphase)
                time.sleep(0.05)
                self.femb.write_reg( self.REG_CLKPHASE, clockphase)
                time.sleep(0.05)
                
            print("Readback: ",self.getClockStr())

            #internal test pulser control
            self.femb.write_reg( 5, 0x00000000)
            self.femb.write_reg( 13, 0x0) #enable

            #Set test and readout mode register
            self.femb.write_reg( self.REG_HS, 0x0) # 0 readout all 15 channels, 1 readout only selected one
            self.femb.write_reg( self.REG_SEL_CH, 0x0000) #11-8 = channel select, 3-0 = ASIC select

            #Set number events per header
            self.femb.write_reg( 8, 0x0)

            #Configure ADC (and external clock inside)
            try:
                self.configAdcAsic()
                #self.configAdcAsic(clockMonostable=True)
            except ReadRegError:
                continue
            # Check that board streams data
            data = self.femb.get_data(1)
            if data == None:
                print("Board not streaming data, retrying initialization...")
                continue # try initializing again
            print("FEMB_CONFIG--> Reset FEMB is DONE")
            return
        print("Error: Board not streaming data after trying to initialize {} times.".format(nRetries))
        if self.exitOnError:
            print("Exiting.")
            sys.exit(1)
        else:
            raise InitBoardError

    def configAdcAsic_regs(self,Adcasic_regs):
        #ADC ASIC SPI registers
        assert(len(Adcasic_regs)==36)
        print("FEMB_CONFIG--> Config ADC ASIC SPI")
        for k in range(10):
            i = 0
            for regNum in range(self.REG_ADCSPI_BASE,self.REG_ADCSPI_BASE+len(Adcasic_regs),1):
                    self.femb.write_reg ( regNum, Adcasic_regs[i])
                    time.sleep(0.05)
                    i = i + 1

            #print("  ADC ASIC write : ",Adcasic_regs)
            #ADC ASIC sync -- Justin: I don't think this exists anymore
            #self.femb.write_reg ( 17, 0x1) # controls HS link, 0 for on, 1 for off
            #self.femb.write_reg ( 17, 0x0) # controls HS link, 0 for on, 1 for off        

            #Write ADC ASIC SPI
            print("FEMB_CONFIG--> Program ADC ASIC SPI")
            self.femb.write_reg ( self.REG_ASIC_RESET, 1)
            time.sleep(0.1)
            self.femb.write_reg ( self.REG_ASIC_SPIPROG, 1)
            time.sleep(0.1)
            self.femb.write_reg ( self.REG_ASIC_SPIPROG, 1)
            time.sleep(0.1)

            #enable streaming
            #self.femb.write_reg( 9, 0x1)

            #LBNE_ADC_MODE
            self.femb.write_reg( 18, 0x1)

            print("FEMB_CONFIG--> Check ADC ASIC SPI")
            adcasic_rb_regs = []
            for regNum in range(self.REG_ADCSPI_RDBACK_BASE,self.REG_ADCSPI_RDBACK_BASE+len(Adcasic_regs),1):
                val = self.femb.read_reg (regNum) 
                if val is None:
                    message = "Error in FEMB_CONFIG.configAdcAsic_regs: read from board failed"
                    print(message)
                    if self.exitOnError:
                        return
                    else:
                        raise ReadRegError
                adcasic_rb_regs.append( val )

            #print("{:32}  {:32}".format("Write","Readback"))
            #print("{:8}  {:8}".format("Write","Readback"))
            # we only get 15 LSBs back so miss D0 for a channel and CLK0
            readbackMatch = True
            for regNum in range(36):
                write_val = Adcasic_regs[regNum] #& 0x7FFF
                readback_val = adcasic_rb_regs[(regNum + 9) % 36] >> 1
                # we only get the 15 LSBs back
                if readback_val != (Adcasic_regs[regNum] & 0x7FFF):
                    readbackMatch = False
                #print("{:032b}  {:032b}".format(write_val,readback_val))
                #print("{:08X}  {:08X}".format(write_val,readback_val))

            if readbackMatch:
                print("FEMB_CONFIG--> ADC ASIC SPI is OK")
                return
            else: 
                print("FEMB_CONFIG--> ADC ASIC Readback didn't match, retrying...")
        print("Error: Wrong ADC SPI readback.")
        if self.exitOnError:
            print("Exiting.")
            sys.exit(1)
        else:
            raise ConfigADCError

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
            freqInternal=1
        if sleep is None:
            sleep=0
        if pdsr is None:
            pdsr=0
        if pcsr is None:
            pcsr=0
        if sLSB is None:
            sLSB = 0
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
        # a bunch of things depend on the clock choice
        clk0=0
        clk1=0
        if clockExternal:
            clk0=1
            clk1=0
        elif clockFromFIFO:
            clk0=0
            clk1=1
        if f0 is None:
            if clockExternal:
                f0 = 1
            else:
                f0 = 0
        if clockExternal:
            self.extClock(enable=True)
        else:
            self.extClock(enable=False)

        self.adc_reg.set_sbnd_board(en_gr=enableOffsetCurrent,d=offsetCurrent,tstin=testInput,frqc=freqInternal,slp=sleep,pdsr=pdsr,pcsr=pcsr,clk0=clk0,clk1=clk1,f0=f0,f1=f1,f2=f2,f3=f3,f4=f4,f5=f5,slsb=sLSB)
        self.configAdcAsic_regs(self.adc_reg.REGS)

    def selectChannel(self,asic,chan,hsmode=1):
        """
        asic is chip number 0 to 7
        chan is channel within asic from 0 to 15
        hsmode: if 0 then streams all channels of a chip, if 1 only te selected channel. defaults to 1
        """
        hsmodeVal = int(hsmode) & 1;
        asicVal = int(asic)
        if (asicVal < 0 ) or (asicVal >= self.NASICS ) :
                print( "femb_config_femb : selectChan - invalid ASIC number, only 0 to {} allowed".format(self.NASICS-1))
                return
        chVal = int(chan)
        if (chVal < 0 ) or (chVal > 15 ) :
                print("femb_config_femb : selectChan - invalid channel number, only 0 to 15 allowed")
                return

        #print( "Selecting ASIC " + str(asicVal) + ", channel " + str(chVal))

        self.femb.write_reg ( self.REG_HS, hsmodeVal)
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
        latchloc1_4 = self.femb.read_reg ( self.REG_LATCHLOC1_4 ) 
        latchloc5_8 = self.femb.read_reg ( self.REG_LATCHLOC5_8 )
        clkphase    = self.femb.read_reg ( self.REG_CLKPHASE )
        if self.SAMPLERATE == 1e6:
            if self.COLD:
                self.REG_LATCHLOC1_4_data_1MHz_cold = latchloc1_4
                self.REG_LATCHLOC5_8_data_1MHz_cold = latchloc5_8
                self.REG_CLKPHASE_data_1MHz_cold    = clkphase
            else:
                self.REG_LATCHLOC1_4_data_1MHz = latchloc1_4
                self.REG_LATCHLOC5_8_data_1MHz = latchloc5_8
                self.REG_CLKPHASE_data_1MHz    = clkphase
        else: # 2 MHz
            if self.COLD:
                self.REG_LATCHLOC1_4_data_cold = latchloc1_4
                self.REG_LATCHLOC5_8_data_cold = latchloc5_8
                self.REG_CLKPHASE_data_cold    = clkphase
            else:
                self.REG_LATCHLOC1_4_data = latchloc1_4
                self.REG_LATCHLOC5_8_data = latchloc5_8
                self.REG_CLKPHASE_data    = clkphase
        print("FEMB_CONFIG--> Latch latency {:#010x} {:#010x} Phase: {:#010x}".format(latchloc1_4,
                        latchloc5_8, clkphase))
        self.femb.write_reg ( 3, (reg3&0x7fffffff) )
        self.femb.write_reg ( 3, (reg3&0x7fffffff) )
        print("FEMB_CONFIG--> End sync ADC")
        return not alreadySynced,latchloc1_4,latchloc5_8 ,clkphase

    def testUnsync(self, adc):
        print("Starting testUnsync adc: ",adc)
        adcNum = int(adc)
        if (adcNum < 0 ) or (adcNum > 7 ):
                print("FEMB_CONFIG--> femb_config_femb : testLink - invalid asic number")
                return

        #loop through channels, check test pattern against data
        syncDataCounts = [{} for i in range(16)] #dict for each channel
        for ch in range(0,16,1):
                self.selectChannel(adcNum,ch, 1)
                time.sleep(0.05)                
                for test in range(0,10,1):
                        data = self.femb.get_data(2056)
                        #print("test: ",test," data: ",data)
                        if data == None:
                            continue
                        for samp in data[0:(16*1024+1023)]:
                                if samp == None:
                                        continue
                                #chNum = ((samp >> 12 ) & 0xF)
                                sampVal = (samp & 0xFFF)
                                #if sampVal != self.ADC_TESTPATTERN[ch]        :
                                #        badSync = 1 
                                if sampVal in syncDataCounts[ch]:
                                    syncDataCounts[ch][sampVal] += 1
                                else:
                                    syncDataCounts[ch][sampVal] = 1
        # check jitter
        badSync = 0
        maxCodes = [None]*16
        for ch in range(0,16,1):
            sampSum = sum(syncDataCounts[ch])
            maxCode = None
            nMaxCode = 0
            for code in syncDataCounts[ch]:
                nThisCode = syncDataCounts[ch][code]
                if nThisCode > nMaxCode:
                    nMaxCode = nThisCode
                    maxCode = code
            maxCodes[ch] = maxCode
            if len(syncDataCounts[ch]) > 1:
                badSync = 1
                frac = nMaxCode / float(sampSum)
                print("Sync Error: Jitter for Ch {:2}: {:8.4%} (:5/5)".format(ch,frac,nMaxCode,sampSum))
        for ch in range(0,16,1):
            maxCode = maxCodes[ch]
            correctCode = self.ADC_TESTPATTERN[ch]
            if maxCode is None:
                badSync = 1
                print("Sync Error: no data for ch {:2}".format(ch))
            elif maxCode != correctCode:
                badSync = 1
                print("Sync Error: mismatch for ch {:2}: expected {:#03x} observed {:#03x}".format(ch,correctCode,maxCode))
        return badSync


    def fixUnsync(self, adc):
        adcNum = int(adc)
        if (adcNum < 0 ) or (adcNum > 7 ):
                print("FEMB_CONFIG--> femb_config_femb : testLink - invalid asic number")
                return

        initLATCH1_4 = self.femb.read_reg ( self.REG_LATCHLOC1_4 )
        initLATCH5_8 = self.femb.read_reg ( self.REG_LATCHLOC5_8 )
        initPHASE = self.femb.read_reg ( self.REG_CLKPHASE )

        phases = [0,1]
        if self.COLD:
            phases = [0,1,0,1,0]

        #loop through sync parameters
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
            for phase in phases:
                clkMask = (0x1 << adcNum)
                testPhase = ( (initPHASE & ~(clkMask)) | (phase << adcNum) ) 
                self.femb.write_reg ( self.REG_CLKPHASE, testPhase )
                time.sleep(0.01)
                print("try shift: {} phase: {} testingUnsync...".format(shift,phase))
                print("     initPHASE: {:#010x}, phase: {:#010x}, testPhase: {:#010x}".format(initPHASE,phase,testPhase))
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
        print("Error: FEMB_CONFIG--> ADC SYNC process failed for ADC # " + str(adc))
        print("Setting back to original values: LATCHLOC1_4: {:#010x}, LATCHLOC5_8: {:#010x}, PHASE: {:#010x}".format,initLATCH1_4,initLATCH5_8,initPHASE)
        self.femb.write_reg ( self.REG_LATCHLOC1_4, initLATCH1_4 )
        self.femb.write_reg ( self.REG_LATCHLOC5_8, initLATCH5_8 )
        self.femb.write_reg ( self.REG_CLKPHASE, initPHASE )
        if self.exitOnError:
            sys.exit(1)
        else:
            raise SyncADCError

    def extClock(self, enable=False, 
                period=500, mult=1, 
                offset_rst=0, offset_read=480, offset_msb=230, offset_lsb=480,
                width_rst=50, width_read=20, width_msb=270, width_lsb=20,
                offset_lsb_1st_1=50, width_lsb_1st_1=190,
                offset_lsb_1st_2=480, width_lsb_1st_2=20,
                inv_rst=True, inv_read=True, inv_msb=False, inv_lsb=False, inv_lsb_1st=False):
        """
        Programs external clock. All non-boolean arguments except mult are in nanoseconds
        """

        rd_en_off = 0
        adc_off = 0
        adc_wid = 0
        msb_off = 0
        msb_wid = 0
        period_val = 0
        lsb_fc_wid2 = 0
        lsb_fc_off1 = 0
        rd_en_wid = 0
        lsb_fc_wid1 = 0
        lsb_fc_off2 = 0
        lsb_s_wid = 0
        lsb_s_off = 0
        inv = 0

        if enable:
            clock = 1./self.FPGA_FREQ_MHZ * 1000. # clock now in ns
            #print("FPGA Clock freq: {} MHz period: {} ns".format(self.FPGA_FREQ_MHZ,clock))
            #print("ExtClock option mult: {}".format(mult))
            #print("ExtClock option period: {} ns".format(period))
            #print("ExtClock option offset_read: {} ns".format(offset_read))
            #print("ExtClock option offset_rst: {} ns".format(offset_rst))
            #print("ExtClock option offset_msb: {} ns".format(offset_msb))
            #print("ExtClock option offset_lsb: {} ns".format(offset_lsb))
            #print("ExtClock option offset_lsb_1st_1: {} ns".format(offset_lsb_1st_1))
            #print("ExtClock option offset_lsb_1st_2: {} ns".format(offset_lsb_1st_2))
            #print("ExtClock option width_read: {} ns".format(width_read))
            #print("ExtClock option width_rst: {} ns".format(width_rst))
            #print("ExtClock option width_msb: {} ns".format(width_msb))
            #print("ExtClock option width_lsb: {} ns".format(width_lsb))
            #print("ExtClock option width_lsb_1st_1: {} ns".format(width_lsb_1st_1))
            #print("ExtClock option width_lsb_1st_2: {} ns".format(width_lsb_1st_2))
            #print("ExtClock option inv_rst: {}".format(inv_rst))
            #print("ExtClock option inv_read: {}".format(inv_read))
            #print("ExtClock option inv_msb: {}".format(inv_msb))
            #print("ExtClock option inv_lsb: {}".format(inv_lsb))
            #print("ExtClock option inv_lsb_1st: {}".format(inv_lsb_1st))
            denominator = clock/mult
            #print("ExtClock denominator: {} ns".format(denominator))
            period_val = period // denominator
            rd_en_off =  offset_read // denominator
            adc_off =  offset_rst // denominator
            adc_wid =  width_rst // denominator
            msb_off = offset_msb  // denominator
            msb_wid = width_msb  // denominator
            lsb_fc_wid2 = width_lsb_1st_2 // denominator
            lsb_fc_off1 = offset_lsb_1st_1 // denominator
            rd_en_wid = width_read // denominator
            lsb_fc_wid1 = width_lsb_1st_1 // denominator
            lsb_fc_off2 = offset_lsb_1st_2 // denominator
            lsb_s_wid = width_lsb // denominator
            lsb_s_off = offset_lsb // denominator
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
            ("rd_en_off",self.REG_EXTCLK_RD_EN_OFF, rd_en_off),
            ("adc_off",self.REG_EXTCLK_ADC_OFF, adc_off),
            ("adc_wid",self.REG_EXTCLK_ADC_WID, adc_wid),
            ("msb_off",self.REG_EXTCLK_MSB_OFF, msb_off),
            ("msb_wid",self.REG_EXTCLK_MSB_WID, msb_wid),
            ("period",self.REG_EXTCLK_PERIOD, period_val),
            ("lsb_fc_wid2",self.REG_EXTCLK_LSB_FC_WID2, lsb_fc_wid2),
            ("lsb_fc_off1",self.REG_EXTCLK_LSB_FC_OFF1, lsb_fc_off1),
            ("rd_en_wid",self.REG_EXTCLK_RD_EN_WID, rd_en_wid),
            ("lsb_fc_wid1",self.REG_EXTCLK_LSB_FC_WID1, lsb_fc_wid1),
            ("lsb_fc_off2",self.REG_EXTCLK_LSB_FC_OFF2, lsb_fc_off2),
            ("lsb_s_wid",self.REG_EXTCLK_LSB_S_WID, lsb_s_wid),
            ("lsb_s_off",self.REG_EXTCLK_LSB_S_OFF, lsb_s_off),
            ("inv",self.REG_EXTCLK_INV, inv),
        ]
        for name,reg,val in regsValsToWrite:
            val = int(val) & 0xFFFF # only 16 bits for some reason
            #print("ExtClock Register {0:12} number {1:3} set to {2:5} = {2:#06x}".format(name,reg,val))
            self.femb.write_reg(reg,val)

    def programFirmware(self, firmware):
        """
        Programs the FPGA using the firmware file given.
        """
        if self.FIRMWAREPROGCABLE == "USB-BlasterII":
            # this programmer is too fast for our board 
            # (or linux or something) so we have to slow it down
            jtagconfig_commandline = os.path.dirname(self.FIRMWAREPROGEXE)
            jtagconfig_commandline = os.path.join(jtagconfig_commandline,"jtagconfig")
            jtagconfig_commandline += " --setparam 1 JtagClock 6M"
            print(jtagconfig_commandline)
            subprocess.run(jtagconfig_commandline.split(),check=True)
        commandline = "{} -c {} -m jtag -o p;{}".format(self.FIRMWAREPROGEXE,self.FIRMWAREPROGCABLE,firmware)
        commandlinelist = commandline.split()
        print(commandline)
        print(commandlinelist)
        subprocess.run(commandlinelist,check=True)

    def checkFirmwareProgrammerStatus(self):
        """
        Prints a debug message for the firmware programmer
        """
        jtagconfig_commandline = os.path.dirname(self.FIRMWAREPROGEXE)
        jtagconfig_commandline = os.path.join(jtagconfig_commandline,"jtagconfig")
        if self.FIRMWAREPROGCABLE == "USB-BlasterII":
            # this programmer is too fast for our board 
            # (or linux or something) so we have to slow it down
            jtagconfig_commandline_speed = jtagconfig_commandline +" --setparam 1 JtagClock 6M"
            print(jtagconfig_commandline_speed)
            subprocess.run(jtagconfig_commandline_speed.split())
        subprocess.run(jtagconfig_commandline.split())

    def programFirmware1Mhz(self):
        self.programFirmware(self.FIRMWAREPATH1MHZ)
        self.SAMPLERATE = 1e6

    def programFirmware2Mhz(self):
        self.programFirmware(self.FIRMWAREPATH2MHZ)
        self.SAMPLERATE = 2e6

    def getClockStr(self):
        latchloc1 = self.femb.read_reg(self.REG_LATCHLOC1_4)
        latchloc5 = self.femb.read_reg(self.REG_LATCHLOC5_8)
        clkphase = self.femb.read_reg(self.REG_CLKPHASE)
        if latchloc1 is None:
            return "Register Read Error"
        if latchloc5 is None:
            return "Register Read Error"
        if clkphase is None:
            return "Register Read Error"
        return "Latch Loc: {:#010x} {:#010x} Clock Phase: {:#010x}".format(latchloc1,latchloc5,clkphase)
