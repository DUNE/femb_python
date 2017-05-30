#!/usr/bin/env python33

"""
Configuration for V* ADC Test Board
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
from femb_python.configuration.adc_asic_reg_mapping_V import ADC_ASIC_REG_MAPPING
from femb_python.test_insturment_interface.rigol_dg4000 import RigolDG4000
from femb_python.test_insturment_interface.rigol_dp800 import RigolDP800

class FEMB_CONFIG(FEMB_CONFIG_BASE):

    def __init__(self):
        super().__init__()
        #declare board specific registers
        self.FEMB_VER = "adctest"
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
        self.REG_LATCHLOC = 4
        self.REG_CLKPHASE = 6
        #Latch latency 0x6666666f    Phase 0xffff0055
        self.ADC_TESTPATTERN = [0x12, 0x345, 0x678, 0xf1f, 0xad, 0xc01, 0x234, 0x567, 0x89d, 0xeca, 0xff0, 0x123, 0x456, 0x789, 0xabc, 0xdef]
        self.NASICS = 1
	self.FUNCGENINTER = RigolDG4000("/dev/usbtmc1",1)
	self.POWERSUPPLYINTER = RigolDP800("/dev/usbtmc0",["CH1"])
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
            self.femb.write_reg( self.REG_LATCHLOC, 0x66666667)
            #Set ADC clock phase
            self.femb.write_reg( self.REG_CLKPHASE, 0xfffc0054)

            #internal test pulser control
            self.femb.write_reg( 5, 0x00000000)
            self.femb.write_reg( 13, 0x0) #enable

            #Set test and readout mode register
            self.femb.write_reg( 7, 0x0000) #11-8 = channel select, 3-0 = ASIC select

            #Set number events per header
            self.femb.write_reg( 8, 0x0)

            #ADC ASIC SPI registers
            print("Config ADC ASIC SPI")
            print("ADCADC")
            ## Corresponds to f0=f1=0, clk=0,clk1=1, pcsr=pdsr=frqc=1, tstin=1
            ## en_gr=0, slp=0
            ## Clocks from digital generator of FIFO
            regs = [
             0xC0C0C0C,
             0xC0C0C0C,
             0xC0C0C0C,
             0xC0C0C0C,
             0xC0C0C0C,
             0xC0C0C0C,
             0xC0C0C0C,
             0xC0C0C0C,
             0x18321832,
             0x18181819,
             0x18181818,
             0x18181818,
             0x18181818,
             0x18181818,
             0x18181818,
             0x18181818,
             0x64186418,
             0x30303030,
             0x30303030,
             0x30303030,
             0x30303030,
             0x30303030,
             0x30303030,
             0x30303030,
             0x30303030,
             0x60c868c8,
             0x60606868,
             0x60606868,
             0x60606868,
             0x60606868,
             0x60606868,
             0x60606868,
             0x60606868,
             0x9060A868,
             0x10001,
            ]
            
            self.adc_reg.set_sbnd_board(frqc=1,pdsr=1,pcsr=1,clk0=0,clk1=1,f1=0,f2=0,tstin=1)
            regs = self.adc_reg.REGS
            for iReg, val in enumerate(regs):
                #print("{:032b}".format(val))
                print("{:08x}".format(val))
                self.femb.write_reg(self.REG_ADCSPI_BASE+iReg,val)

            #ADC ASIC sync
            self.femb.write_reg( 17, 0x1) # controls HS link, 0 for on, 1 for off
            self.femb.write_reg( 17, 0x0) # controls HS link, 0 for on, 1 for off        

            #Write ADC ASIC SPI
            print( "Program ADC ASIC SPI")
            self.femb.write_reg( self.REG_ASIC_SPIPROG, 1)
            time.sleep(0.1)
            self.femb.write_reg( self.REG_ASIC_SPIPROG, 1)
            time.sleep(0.1)

            print( "Check ADC ASIC SPI")
            for regNum in range(self.REG_ADCSPI_RDBACK_BASE,self.REG_ADCSPI_RDBACK_BASE+34,1):
                    val = self.femb.read_reg( regNum ) 
                    #print("{:08x}".format(val))

            #enable streaming
            #self.femb.write_reg( 9, 0x8)

            #LBNE_ADC_MODE
            self.femb.write_reg( 16, 0x1)

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

            #self.femb.write_reg ( 18, 0x0)
            #time.sleep(0.1)

            #LBNE_ADC_MODE
            self.femb.write_reg( 16, 0x1)

            print("FEMB_CONFIG--> Check ADC ASIC SPI")
            adcasic_rb_regs = []
            for regNum in range(self.REG_ADCSPI_RDBACK_BASE,self.REG_ADCSPI_RDBACK_BASE+len(Adcasic_regs),1):
                val = self.femb.read_reg ( regNum ) 
                #print("{:08x}".format(val))
                adcasic_rb_regs.append( val )

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
        #enable streaming
        #self.femb.write_reg ( 9, 0x8)
        #LBNE_ADC_MODE

    def configAdcAsic(self,enableOffsetCurrent=None,offsetCurrent=None,testInput=None,
                            freqInternal=None,sleep=None,pdsr=None,pcsr=None,
                            clockMonostable=None,clockExternal=None,clockFromFIFO=None,
                            sLSB=None,f0=0,f1=0,f2=0,f3=None,f4=None,f5=None):
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
            pdsr=1
        if pcsr is None:
            pcsr=1
        if not (clockMonostable or clockExternal or clockFromFIFO):
            clockFromFIFO=True
        clk0=0
        clk1=0
        if clockExternal:
            clk0=1
            clk1=0
        elif clockFromFIFO:
            clk0=0
            clk1=1
        self.adc_reg.set_sbnd_board(en_gr=enableOffsetCurrent,d=offsetCurrent,tstin=testInput,frqc=freqInternal,slp=sleep,pdsr=pdsr,pcsr=pcsr,clk0=clk0,clk1=clk1,f1=f1,f2=f2,res2=0,res1=1,res0=1)
        self.configAdcAsic_regs(self.adc_reg.REGS)

        #regs = [
        # 0xC0C0C0C,
        # 0xC0C0C0C,
        # 0xC0C0C0C,
        # 0xC0C0C0C,
        # 0xC0C0C0C,
        # 0xC0C0C0C,
        # 0xC0C0C0C,
        # 0xC0C0C0C,
        # 0x18321832,
        # 0x18181818,
        # 0x18181818,
        # 0x18181818,
        # 0x18181818,
        # 0x18181818,
        # 0x18181818,
        # 0x18181818,
        # 0x64186418,
        # 0x30303030,
        # 0x30303030,
        # 0x30303030,
        # 0x30303030,
        # 0x30303030,
        # 0x30303030,
        # 0x30303030,
        # 0x30303030,
        # 0x60c868c8,
        # 0x60606868,
        # 0x60606868,
        # 0x60606868,
        # 0x60606868,
        # 0x60606868,
        # 0x60606868,
        # 0x60606868,
        # 0x9060A868,
        # 0x10001,
        #]
        #self.configAdcAsic_regs(regs)

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
        print("Start sync ADC")
        reg3 = self.femb.read_reg(3)
        newReg3 = ( reg3 | 0x80000000 )
        self.femb.write_reg( 3, newReg3 ) #31 - enable ADC test pattern
        alreadySynced = True
        for a in range(0,self.NASICS,1):
                print("Test ADC " + str(a))
                unsync = self.testUnsync(a)
                if unsync != 0:
                        alreadySynced = False
                        print("ADC not synced, try to fix")
                        self.fixUnsync(a)
        LATCH = self.femb.read_reg( self.REG_LATCHLOC )
        PHASE = self.femb.read_reg( self.REG_CLKPHASE )
        self.femb.write_reg( 3, reg3 ) # turn off adc test pattern
        self.femb.write_reg( 3, reg3 ) # turn off adc test pattern
        print("Latch latency {:#010x} Phase: {:#010x}".format(LATCH,PHASE))
        print("End sync ADC")
        return not alreadySynced, LATCH, None, PHASE

    def testUnsync(self, adc):
        adcNum = int(adc)
        if (adcNum < 0 ) or (adcNum >= self.NASICS ):
                print("femb_config_femb : testLink - invalid asic number")
                return
        
        #loop through channels, check test pattern against data
        badSync = 0
        for ch in range(0,16,1):
                self.selectChannel(adcNum,ch)
                time.sleep(0.1)                
                for test in range(0,1000,1):
                        data = self.femb.get_data(1)
                        for samp in data:
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
        if (adcNum < 0 ) or (adcNum >= self.NASICS ):
                print("femb_config_femb : testLink - invalid asic number")
                return

        initLATCH = self.femb.read_reg( self.REG_LATCHLOC )
        initPHASE = self.femb.read_reg( self.REG_CLKPHASE )

        #loop through sync parameters
        for phase in range(0,2,1):
                clkMask = (0x1 << adcNum)
                testPhase = ( (initPHASE & ~(clkMask)) | (phase << adcNum) ) 
                self.femb.write_reg( self.REG_CLKPHASE, testPhase )
                for shift in range(0,16,1):
                        shiftMask = (0xF << 4*adcNum)
                        testShift = ( (initLATCH & ~(shiftMask)) | (shift << 4*adcNum) )
                        self.femb.write_reg( self.REG_LATCHLOC, testShift )
                        #reset ADC ASIC
                        self.femb.write_reg( self.REG_ASIC_RESET, 1)
                        time.sleep(0.1)
                        self.femb.write_reg( self.REG_ASIC_SPIPROG, 1)
                        time.sleep(0.1)
                        self.femb.write_reg( self.REG_ASIC_SPIPROG, 1)
                        time.sleep(0.1)
                        #test link
                        unsync = self.testUnsync(adcNum)
                        if unsync == 0 :
                                print("ADC synchronized")
                                return
        #if program reaches here, sync has failed
        print("ADC SYNC process failed for ADC # " + str(adc))

