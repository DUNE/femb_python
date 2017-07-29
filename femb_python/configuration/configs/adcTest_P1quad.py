#!/usr/bin/env python33

"""
Configuration for P1 ADC quad-chip board. Note that the fourth socket doesn't
have full external clock functionality because the FPGA ran out of PLLs.
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
from femb_python.configuration.adc_asic_reg_mapping_P1_singleADC import ADC_ASIC_REG_MAPPING
from femb_python.test_instrument_interface.keysight_33600A import Keysight_33600A

class FEMB_CONFIG(FEMB_CONFIG_BASE):

    def __init__(self,exitOnError=True):
        super().__init__(exitOnError=exitOnError)
        #declare board specific registers
        self.FEMB_VER = "adctestP1quad"

        self.REG_RESET = 0 # bit 0 system, 1 reg, 2 alg, 3 udp
        self.REG_PWR_CTRL = 1  # bit 0-3 pwr, 8-15 blue LEDs near buttons
        self.REG_ASIC_SPIPROG_RESET = 2 # bit 0 FE SPI, 1 ADC SPI, 4 FE ASIC RESET, 5 ADC ASIC RESET, 6 SOFT ADC RESET & SPI readback check
        self.REG_SEL_CH = 3 # bit 0-7 chip, 8-15 channel, 31 WIB mode

        self.REG_DAC1 = 4 # bit 0-15 DAC val, 16-19 tp mode select, 31 set dac
        self.REG_DAC2 = 5 # bit 0-15 tp period, 16-31 tp shift

        self.REG_ADC_TST_PATT = 6 # bit 0-11 tst patt, 16 enable
        self.REG_ADC_CLK = 7 # bit 0-3 clk phase, 8 clk speed sel
        self.REG_LATCHLOC = 8 # bit 0-7 ADC1, 8-15 ADC2, 16-23 ADC3, 24-31 ADC4

        self.REG_STOP_ADC = 9 # header check + busy check

        self.REG_UDP_FRAME_SIZE = 63 # bits 0-11
        self.REG_FIRMWARE_VERSION = 0xFF # 255 in decimal
        
        self.REG_LATCHLOC_data_2MHz = 0x0
        self.REG_LATCHLOC_data_1MHz = 0x0
        self.REG_LATCHLOC_data_2MHz_cold = 0x0
        self.REG_LATCHLOC_data_1MHz_cold = 0x0

        self.REG_CLKPHASE_data_2MHz = 0x0
        self.REG_CLKPHASE_data_1MHz = 0x0
        self.REG_CLKPHASE_data_2MHz_cold = 0x0
        self.REG_CLKPHASE_data_1MHz_cold = 0x0

        self.DEFAULT_TST_PATERN = 0x12
        self.ADC_TESTPATTERN = [0x12, 0x345, 0x678, 0xf1f, 0xad, 0xc01, 0x234, 0x567, 0x89d, 0xeca, 0xff0, 0x123, 0x456, 0x789, 0xabc, 0xdef]

        # registers 64-88 are SPI to ASICs
        # 88 is last register besides 255 which is firmware version
        self.REG_FESPI_BASE = 84 # this configures all FE ASICs
        self.REG_ADCSPI_BASES = [64,69,74,79] # for each chip

        self.REG_EXTCLK_INV = 10
        self.REG_EXTCLK_BASES = [11,20,29,38] # for each chip
        self.FPGA_FREQ_MHZ = 200 # frequency of FPGA clock in MHz

        self.REG_PLL_BASES = [17,26,35,44] # for each chip

        self.NASICS = 4
        self.FUNCGENINTER = Keysight_33600A("/dev/usbtmc1",1)
        self.F2DEFAULT = 0
        self.CLKDEFAULT = "fifo"

        self.SAMPLERATE = 2e6

        #initialize FEMB UDP object
        self.femb = FEMB_UDP()

        self.adc_regs = []
        for i in range(self.NASICS):
            self.adc_regs.append(ADC_ASIC_REG_MAPPING())

    def resetBoard(self):
        #Reset system
        self.femb.write_reg( self.REG_RESET, 1)
        time.sleep(5.)

        #Reset registers
        self.femb.write_reg( self.REG_RESET, 2)
        time.sleep(1.)

        self.femb.write_reg( self.REG_RESET, 4)
        time.sleep(1.)

    def initBoard(self):
        #set up default registers

        # test readback
        readback = self.femb.read_reg(1)
        if readback is None:
            if self.exitOnError:
                print("FEMB_CONFIG: Error reading register 0, Exiting.")
                sys.exit(1)
            else:
                raise ReadRegError("Couldn't read register 0")


        ##### Start Top-level Labview stacked sequence struct 0
        print("Firmware Version: ",self.femb.read_reg(self.REG_FIRMWARE_VERSION) & 0xFFFF)
        self.femb.write_reg(self.REG_UDP_FRAME_SIZE,0x1FB)
        time.sleep(0.05)
        self.setFPGADac(0,0,0,0) # write regs 4 and 5
        self.femb.write_reg(1,0) # pwr ctrl
        self.femb.write_reg(3, (5 << 8 )) # chn sel
        self.femb.write_reg(6,self.DEFAULT_TST_PATERN)  #tst pattern
        self.femb.write_reg(7,13)  #adc clk
        self.femb.write_reg(8,0)  #latchloc
        ##### End Top-level Labview stacked sequence struct 0

        self.turnOnAsics()

        nRetries = 1
        for iRetry in range(nRetries):

            #Reset ASICs
            self.femb.write_reg( self.REG_ASIC_SPIPROG_RESET, 0x30) # reset FE and ADC
            self.femb.write_reg( self.REG_ASIC_SPIPROG_RESET, 0x0) # zero out reg
            time.sleep(0.1)

            #Set ADC test pattern register
            self.femb.write_reg(self.REG_ADC_TST_PATT, self.DEFAULT_TST_PATERN) # test pattern off
            #self.femb.write_reg(self.REG_ADC_TST_PATT, self.DEFAULT_TST_PATERN+(1 << 16)) # test pattern on
            #Set ADC latch_loc and clock phase and sample rate
            if self.SAMPLERATE == 1e6:
                if self.COLD:
                    self.femb.write_reg( self.REG_LATCHLOC, self.REG_LATCHLOC_data_1MHz_cold)
                    self.femb.write_reg( self.REG_ADC_CLK, (self.REG_CLKPHASE_data_1MHz_cold & 0xF) | (1 << 8))
                else:
                    self.femb.write_reg( self.REG_LATCHLOC, self.REG_LATCHLOC_data_1MHz)
                    self.femb.write_reg( self.REG_ADC_CLK, (self.REG_CLKPHASE_data_1MHz & 0xF) | (1 << 8))
            else: # use 2 MHz values
                if self.COLD:
                    self.femb.write_reg( self.REG_LATCHLOC, self.REG_LATCHLOC_data_2MHz_cold)
                    self.femb.write_reg( self.REG_ADC_CLK, (self.REG_CLKPHASE_data_2MHz_cold & 0xF))
                else:
                    self.femb.write_reg( self.REG_LATCHLOC, self.REG_LATCHLOC_data_2MHz)
                    self.femb.write_reg( self.REG_ADC_CLK, (self.REG_CLKPHASE_data_2MHz & 0xF))
            self.writePLLs(0,0x20001,0)

            self.setFPGADac(0,0,0,0)

            #Configure ADC (and external clock inside)
            try:
                ##self.femb.write_reg(self.REG_FESPI_BASE,1)
                ##self.adc_regs[0].set_chip(frqc=1)
                #regsListOfLists = []
                #for chipRegConfig in self.adc_regs:
                #    #chipRegConfig.set_chip(frqc=1)
                #    regsListOfLists.append(chipRegConfig.REGS)
                #self.configAdcAsic_regs(regsListOfLists)

                self.configAdcAsic()
                #self.configAdcAsic(clockMonostable=True)
            except ReadRegError:
                continue
            print("Header & Busy Check: {0:#010x} = {0:#034b}".format(self.femb.read_reg(self.REG_STOP_ADC)))

            print("ADC Soft Reset...")
            self.femb.write_reg( self.REG_ASIC_SPIPROG_RESET, 1 << 6) # ADC soft reset
            time.sleep(0.1)
            self.femb.write_reg( self.REG_ASIC_SPIPROG_RESET, 0x0) # zero out reg
            time.sleep(0.1)

            self.printSyncRegister()
            print("Header & Busy Check: {0:#010x} = {0:#034b}".format(self.femb.read_reg(self.REG_STOP_ADC)))

            print("Set packed readout mode...")
            self.selectChannel(0,0,hsmode=0) # packed many channels
            #print("Set readout channel 0 0")
            #self.selectChannel(0,0) # single channel

            time.sleep(0.1)
            self.printSyncRegister()
            print("Header & Busy Check: {0:#010x} = {0:#034b}".format(self.femb.read_reg(self.REG_STOP_ADC)))
            time.sleep(0.1)
            print("Stop ADC...")
            self.femb.write_reg(self.REG_STOP_ADC,1)
            time.sleep(0.1)
            print("Header & Busy Check: {0:#010x} = {0:#034b}".format(self.femb.read_reg(self.REG_STOP_ADC)))
            time.sleep(0.1)
            print("Start ADC...")
            self.femb.write_reg(self.REG_STOP_ADC,0)
            time.sleep(0.1)
            print("Header & Busy Check: {0:#010x} = {0:#034b}".format(self.femb.read_reg(self.REG_STOP_ADC)))
            time.sleep(0.1)

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
        """
        Takes a list NASICS long, each a list of 5 32 bit registers.
        """
        #ADC ASIC SPI registers
        assert(type(Adcasic_regs)==list)
        assert(len(Adcasic_regs)==self.NASICS)
        print("FEMB_CONFIG--> Config ADC ASIC SPI")
        for iChip, chipRegs in enumerate(Adcasic_regs):
            assert(len(chipRegs)==5)
            for iReg in range(5):
                self.femb.write_reg(self.REG_ADCSPI_BASES[iChip]+iReg, chipRegs[iReg])
                print("{:3}  {:#010x}".format(self.REG_ADCSPI_BASES[iChip]+iReg, chipRegs[iReg]))
                time.sleep(0.05)
        
        self.femb.write_reg(self.REG_ASIC_SPIPROG_RESET,0)
        self.femb.write_reg(self.REG_ASIC_SPIPROG_RESET,3)
        time.sleep(0.1)
        self.femb.write_reg(self.REG_ASIC_SPIPROG_RESET,2)
        time.sleep(0.1)
        self.femb.write_reg(self.REG_ASIC_SPIPROG_RESET,0)

        self.printSyncRegister()

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

        regsListOfLists = []
        for chipRegConfig in self.adc_regs:
            chipRegConfig.set_chip(en_gr=enableOffsetCurrent,d=offsetCurrent,tstin=testInput,frqc=freqInternal,slp=sleep,pdsr=pdsr,pcsr=pcsr,clk0=clk0,clk1=clk1,f0=f0,f1=f1,f2=f2,f3=f3,f4=f4,f5=f5,slsb=sLSB)
            regsListOfLists.append(chipRegConfig.REGS)
        self.configAdcAsic_regs(regsListOfLists)

    def selectChannel(self,asic,chan,hsmode=1):
        """
        asic is chip number 0 to 7
        chan is channel within asic from 0 to 15
        hsmode: if 0 then WIB streaming mode, if 1 only the selected channel. defaults to 1
        """
        hsmodeVal = int(hsmode) & 1 # only 1 bit
        asicVal = int(asic)
        if (asicVal < 0 ) or (asicVal >= self.NASICS ) :
                print( "femb_config_femb : selectChan - invalid ASIC number, only 0 to {} allowed".format(self.NASICS-1))
                return
        chVal = int(chan)
        if (chVal < 0 ) or (chVal > 15 ) :
                print("femb_config_femb : selectChan - invalid channel number, only 0 to 15 allowed")
                return

        #print( "Selecting ASIC " + str(asicVal) + ", channel " + str(chVal))

        self.femb.write_reg( self.REG_STOP_ADC, 1)
        time.sleep(0.05)

        regVal = asicVal + (chVal << 8 ) + (hsmodeVal << 31)
        self.femb.write_reg( self.REG_SEL_CH, regVal)
        time.sleep(0.05)

        self.femb.write_reg( self.REG_STOP_ADC, 0)

    def syncADC(self):
        #turn on ADC test mode
        print("FEMB_CONFIG--> Start sync ADC")

        originalTestPatternReg = self.femb.read_reg (self.REG_ADC_TST_PATT)
        newReg = ( originalTestPatternReg | (1 << 16) )
        self.femb.write_reg(self.REG_ADC_TST_PATT,newReg) # - enable ADC test pattern
        time.sleep(0.1)                

        alreadySynced = True
        for a in range(0,self.NASICS,1):
            print("FEMB_CONFIG--> Test ADC " + str(a))
            unsync = self.testUnsync(a)
            if unsync != 0:
                alreadySynced = False
                print("FEMB_CONFIG--> ADC not synced, try to fix")
                self.fixUnsync(a)
        latchloc = None
        phase = None
        latchloc = self.femb.read_reg ( self.REG_LATCHLOC ) 
        clkphase = self.femb.read_reg ( self.REG_ADC_CLK ) & 0x1111
        if self.SAMPLERATE == 1e6:
            if self.COLD:
                self.REG_LATCHLOC_data_1MHz_cold = latchloc
                self.REG_CLKPHASE_data_1MHz_cold = clkphase
            else:
                self.REG_LATCHLOC_data_1MHz = latchloc
                self.REG_CLKPHASE_data_1MHz = clkphase
        else: # 2 MHz
            if self.COLD:
                self.REG_LATCHLOC_data_2MHZ_cold = latchloc
                self.REG_CLKPHASE_data_2MHZ_cold = clkphase
            else:
                self.REG_LATCHLOC_data_2MHZ = latchloc
                self.REG_CLKPHASE_data_2MHZ = clkphase
        print("FEMB_CONFIG--> Latch latency {:#010x} Phase: {:#010x}".format(
                        latchloc, clkphase))
        self.femb.write_reg ( self.REG_ADC_TST_PATT, originalTestPatternReg )
        self.femb.write_reg ( self.REG_ADC_TST_PATT, originalTestPatternReg )
        print("FEMB_CONFIG--> End sync ADC")
        return not alreadySynced,latchloc,clkphase

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

        initLATCH = self.femb.read_reg ( self.REG_LATCHLOC )
        initPHASE = self.femb.read_reg ( self.REG_ADC_CLK ) # remember bit 16 sample rate

        #phases = [0,1,0,1,0]
        phases = [0,1]

        #loop through sync parameters
        for shift in range(0,16,1):
            shiftMask = (0xFF << 8*adcNum)
            testShift = ( (initLATCH1_4 & ~(shiftMask)) | (shift << 8*adcNum) )
            self.femb.write_reg ( self.REG_LATCHLOC, testShift )
            time.sleep(0.01)
            for phase in phases:
                clkMask = (0x1 << adcNum)
                testPhase = ( (initPHASE & ~(clkMask)) | (phase << adcNum) ) 
                self.femb.write_reg ( self.REG_ADC_CLK, testPhase )
                time.sleep(0.01)
                print("try shift: {} phase: {} testingUnsync...".format(shift,phase))
                #reset ADC ASIC
                self.femb.write_reg ( self.REG_ASIC_SPIPROG_RESET, 1 << 5) # reset ADC
                time.sleep(0.01)
                self.femb.write_reg ( self.REG_ASIC_SPIPROG_RESET, 1 << 1) # prog ADC SPI
                time.sleep(0.01)
                self.femb.write_reg ( self.REG_ASIC_SPIPROG_RESET, 1 << 1) # prog ADC SPI
                time.sleep(0.01)
                #test link
                unsync = self.testUnsync(adcNum)
                if unsync == 0 :
                    print("FEMB_CONFIG--> ADC synchronized")
                    return
        #if program reaches here, sync has failed
        print("Error: FEMB_CONFIG--> ADC SYNC process failed for ADC # " + str(adc))
        print("Setting back to original values: LATCHLOC: {:#010x}, PHASE: {:#010x}".format,initLATCH,initPHASE & 0xF)
        self.femb.write_reg ( self.REG_LATCHLOC, initLATCH )
        self.femb.write_reg ( self.REG_ADC_CLK, initPHASE )
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
        IDXM = msb
        IDXL = lsb
        IDL = lsb_1st
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
            print("FPGA Clock freq: {} MHz period: {} ns".format(self.FPGA_FREQ_MHZ,clock))
            print("ExtClock option mult: {}".format(mult))
            print("ExtClock option period: {} ns".format(period))
            print("ExtClock option offset_read: {} ns".format(offset_read))
            print("ExtClock option offset_rst: {} ns".format(offset_rst))
            print("ExtClock option offset_msb: {} ns".format(offset_msb))
            print("ExtClock option offset_lsb: {} ns".format(offset_lsb))
            print("ExtClock option offset_lsb_1st_1: {} ns".format(offset_lsb_1st_1))
            print("ExtClock option offset_lsb_1st_2: {} ns".format(offset_lsb_1st_2))
            print("ExtClock option width_read: {} ns".format(width_read))
            print("ExtClock option width_rst: {} ns".format(width_rst))
            print("ExtClock option width_msb: {} ns".format(width_msb))
            print("ExtClock option width_lsb: {} ns".format(width_lsb))
            print("ExtClock option width_lsb_1st_1: {} ns".format(width_lsb_1st_1))
            print("ExtClock option width_lsb_1st_2: {} ns".format(width_lsb_1st_2))
            print("ExtClock option inv_rst: {}".format(inv_rst))
            print("ExtClock option inv_read: {}".format(inv_read))
            print("ExtClock option inv_msb: {}".format(inv_msb))
            print("ExtClock option inv_lsb: {}".format(inv_lsb))
            print("ExtClock option inv_lsb_1st: {}".format(inv_lsb_1st))
            denominator = clock/mult
            print("ExtClock denominator: {} ns".format(denominator))
            period_val = period // denominator
            print("ExtClock period: {} ns".format(period_val))

            rd_off      = int(offset_read // denominator) & 0xFFFF
            rst_off     = int(offset_rst // denominator) & 0xFFFF
            rst_wid     = int(width_rst // denominator) & 0xFFFF
            msb_off     = int(offset_msb // denominator) & 0xFFFF
            msb_wid     = int(width_msb // denominator) & 0xFFFF
            lsb_fc_wid2 = int(width_lsb_1st_2 // denominator) & 0xFFFF
            lsb_fc_off1 = int(offset_lsb_1st_1 // denominator) & 0xFFFF
            rd_wid      = int(width_read // denominator) & 0xFFFF
            lsb_fc_wid1 = int(width_lsb_1st_1 // denominator) & 0xFFFF
            lsb_fc_off2 = int(offset_lsb_1st_2 // denominator) & 0xFFFF
            lsb_wid     = int(width_lsb // denominator) & 0xFFFF
            lsb_off     = int(offset_lsb // denominator) & 0xFFFF

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


        def writeRegAndPrint(name,reg,val):
            print("ExtClock Register {0:15} number {1:3} set to {2:10} = {2:#010x}".format(name,reg,val))
            #print("ExtClock Register {0:15} number {1:3} set to {2:#034b}".format(name,reg,val))
            self.femb.write_reg(reg,val)
        writeRegAndPrint("inv", self.REG_EXTCLK_INV,inv),
        for iChip, regBase in enumerate(self.REG_EXTCLK_BASES):
            iStr = str(iChip)
            asicRegs = [
                ("RST_ADC"+iStr,(rst_wid << 16) | rst_off),
                ("READ_ADC"+iStr,(rd_wid << 16) | rd_off),
                ("IDXM_ADC"+iStr,(msb_wid << 16) | msb_off), # msb
                ("IDXL_ADC"+iStr,(lsb_wid << 16) | lsb_off), # lsb
                ("IDL1_ADC"+iStr,(lsb_fc_wid1 << 16) | lsb_fc_off1), # lsb_fc_1
                ("IDL2_ADC"+iStr,(lsb_fc_wid2 << 16) | lsb_fc_off2), # lsb_fc_1
            ]
            for iReg, tup in enumerate(asicRegs):
                name = tup[0]
                val = tup[1]
                writeRegAndPrint(name,regBase+iReg,val)

    def turnOffAsics(self):
        oldReg = self.femb.read_reg(self.REG_PWR_CTRL)
        newReg = oldReg & 0xFFFFFFF0
        self.femb.write_reg( self.REG_PWR_CTRL, newReg)
        #pause after turning off ASICs
        time.sleep(2)
        #self.femb.write_reg(self.REG_RESET, 4) # bit 2 is ASIC reset as far as I can see

    def turnOnAsic(self,asic):
        asicVal = int(asic)
        if (asicVal < 0 ) or (asicVal >= self.NASICS ) :
                print( "femb_config_femb : turnOnAsics - invalid ASIC number, only 0 to {} allowed".format(self.NASICS-1))
                return
        print( "turnOnAsic " + str(asicVal) )
        oldReg = self.femb.read_reg(self.REG_PWR_CTRL)
        newReg = oldReg | (1 << asic)
        self.femb.write_reg( self.REG_PWR_CTRL , newReg)

        time.sleep(2) #pause after turn on
        #self.femb.write_reg(self.REG_RESET, 4) # bit 2 is ASIC reset as far as I can see

    def turnOnAsics(self):
        print( "turnOnAsics 0-{}".format(int(self.NASICS -1)))

        oldReg = self.femb.read_reg(self.REG_PWR_CTRL)
        newReg = oldReg | int(2**self.NASICS - 1)
        self.femb.write_reg( self.REG_PWR_CTRL, newReg)

        #pause after turning on ASICs
        time.sleep(5)
        #self.femb.write_reg(self.REG_RESET, 4) # bit 2 is ASIC reset as far as I can see

    def printSyncRegister(self):
        reg = self.femb.read_reg(self.REG_ASIC_SPIPROG_RESET)
        if reg is None:
            print("Error: can't read back sync register")
            if self.exitOnError:
                return
            else:
                raise ReadRegError
        print("Register 2: {:#010x}".format(reg))
        print("ADC Sync Bits: {:#010b} (0 is good)".format(reg >> 24))
        print("ASIC Readback Status:")
        reg = reg >> 16
        adc0 = ((reg >> 0) & 1)== 1
        fe0 = ((reg >> 1) & 1)== 1
        adc1 = ((reg >> 2) & 1)== 1
        fe1 = ((reg >> 3) & 1)== 1
        adc2 = ((reg >> 4) & 1)== 1
        fe2 = ((reg >> 5) & 1)== 1
        adc3 = ((reg >> 6) & 1)== 1
        fe3 = ((reg >> 7) & 1)== 1

        print("  ADC 0:",adc0,"FE 0:",fe0)
        print("  ADC 1:",adc1,"FE 1:",fe1)
        print("  ADC 2:",adc2,"FE 2:",fe2)
        print("  ADC 3:",adc3,"FE 3:",fe3)

    def setFPGADac(self,amp,mode,freq,delay):
        ampRegVal = ((mode & 0xFFFF) << 16) | (amp & 0xFFFF)
        freqRegVal = ((delay & 0xFFFF) << 16) | (freq & 0xFFFF)

        self.femb.write_reg(self.REG_DAC2,freqRegVal)
        time.sleep(0.05)

        self.femb.write_reg(self.REG_DAC1,ampRegVal)
        time.sleep(0.05)
        self.femb.write_reg(self.REG_DAC1,ampRegVal & 0x80000000)
        time.sleep(0.05)
        self.femb.write_reg(self.REG_DAC1,ampRegVal)
        
    def writePLLs(self, step0, step1, step2):
        for iChip in range(3):
            self.writePLL(iChip,step0,step1,step2)

    def writePLL(self, iChip, step0, step1, step2):
        def writeRegAndPrint(name,reg,val):
            self.femb.write_reg(reg,val)
            time.sleep(0.05)
            readback = self.femb.read_reg(reg)
            print("PLL Register {0:15} number {1:3} set to {2:10} = {2:#010x}".format(name,reg,val))
            #print("PLL Register {0:15} number {1:3} set to {2:#034b}".format(name,reg,val))
            if readback == val:
                print("  Readback match")
            else:
                print("  READBACK DOESN'T MATCH! write: {:#010x} read: {:#010x}".format(val,readback))
        regBase = self.REG_PLL_BASES[iChip]
        iStr = str(iChip)
        asicRegs = [
            ("pll_STEP0_ADC"+iStr,step0),
            ("pll_STEP1_ADC"+iStr,step1),
            ("pll_STEP2_ADC"+iStr,step2),
        ]
        for iReg, tup in enumerate(asicRegs):
            name = tup[0]
            val = tup[1]
            writeRegAndPrint(name,regBase+iReg,val)

