#!/usr/bin/env python33

"""
SBND-prototype FEMB. Same chips as 35t:
FE 4*
ADC V
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
import struct
import copy
from femb_python.femb_udp import FEMB_UDP
from femb_python.configuration.config_base import FEMB_CONFIG_BASE
from femb_python.configuration.adc_asic_reg_mapping import ADC_ASIC_REG_MAPPING
from femb_python.configuration.fe_asic_reg_mapping import FE_ASIC_REG_MAPPING

class FEMB_CONFIG(FEMB_CONFIG_BASE):

    def __init__(self):
        super().__init__()
        #declare board specific registers
        self.FEMB_VER = "SBND(FE-ASIC with internal DAC)"
        self.REG_RESET = 0
        self.REG_ASIC_RESET = 1
        self.REG_ASIC_SPIPROG = 2
        self.REG_SEL_ASIC = 7 
        self.REG_SEL_CH = 7
        self.REG_FESPI_BASE = 0x250
        self.REG_ADCSPI_BASE = 0x200
        self.REG_FESPI_RDBACK_BASE = 0x278
        self.REG_ADCSPI_RDBACK_BASE =0x228 
        self.REG_HS = 17
        self.REG_LATCHLOC1_4 = 4
        self.REG_LATCHLOC1_4_data = 0x07060707
        self.REG_LATCHLOC5_8 = 14
        self.REG_LATCHLOC5_8_data = 0x06060606
        self.REG_CLKPHASE = 6
        self.REG_CLKPHASE_data = 0xe1
        self.REG_EN_CALI = 16
        self.ADC_TESTPATTERN = [0x12, 0x345, 0x678, 0xf1f, 0xad, 0xc01, 0x234, 0x567, 0x89d, 0xeca, 0xff0, 0x123, 0x456, 0x789, 0xabc, 0xdef]
        self.NASICS = 8

        #initialize FEMB UDP object
        self.femb = FEMB_UDP()
        self.adc_reg = ADC_ASIC_REG_MAPPING()
        self.fe_reg = FE_ASIC_REG_MAPPING() 

    def resetBoard(self):
        #Reset system
        self.femb.write_reg ( self.REG_RESET, 1)

        #Reset registers
        self.femb.write_reg ( self.REG_RESET, 2)

        #Time stamp reset
        #femb.write_reg ( 0, 4)
        
        #Reset ADC ASICs
        self.femb.write_reg ( self.REG_ASIC_RESET, 1)

    def initBoard(self):
        nRetries = 5
        for iRetry in range(nRetries):
            print("FEMB_CONFIG--> Reset FEMB")
            #set up default registers
            
            #Reset ADC ASICs
            self.femb.write_reg( self.REG_ASIC_RESET, 1)

            #Set ADC test pattern register
            self.femb.write_reg ( 3, 0x01170000) #31 - enable ADC test pattern, 

            #Set ADC latch_loc
            self.femb.write_reg ( self.REG_LATCHLOC1_4, self.REG_LATCHLOC1_4_data )
            self.femb.write_reg ( self.REG_LATCHLOC5_8, self.REG_LATCHLOC5_8_data )
            #Set ADC clock phase
            self.femb.write_reg ( self.REG_CLKPHASE, self.REG_CLKPHASE_data)

            #internal test pulser control
            freq = 500
            dly = 80
            ampl = 0 % 32
            int_dac = 0 # or 0xA1
            dac_meas = int_dac  # or 60
            reg_5_value = ((freq<<16)&0xFFFF0000) + ((dly<<8)&0xFF00) + ( (dac_meas|ampl)& 0xFF )
            self.femb.write_reg ( 5, reg_5_value)
            self.femb.write_reg (16, 0x0)

            self.femb.write_reg ( 13, 0x0) #enable

            #Set test and readout mode register
            self.femb.write_reg ( 7, 0x0000) #11-8 = channel select, 3-0 = ASIC select
            self.femb.write_reg ( 17, 1) #11-8 = channel select, 3-0 = ASIC select

            #for iReg in range(len(self.fe_reg.REGS)):
            #  self.fe_reg.REGS[iReg] = 0xFFFFFFFF
            #set default value to FEMB ADCs and FEs
            #self.configAdcAsic(pdsr=1,pcsr=1,clockFromFIFO=True,freqInternal=1,f2=1)
            self.configAdcAsic_regs(self.adc_reg.REGS)
            self.configFeAsic_regs(self.fe_reg.REGS)

            #Set number events per header -- no use
            #self.femb.write_reg ( 8, 0x0)

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
                    #print("{:08x}".format(Adcasic_regs[i]))
                    self.femb.write_reg ( regNum, Adcasic_regs[i])
                    time.sleep(0.05)
                    i = i + 1

            #print("  ADC ASIC write : ",Adcasic_regs)
            #ADC ASIC sync
            #self.femb.write_reg ( 17, 0x1) # controls HS link, 0 for on, 1 for off
            #self.femb.write_reg ( 17, 0x0) # controls HS link, 0 for on, 1 for off        

            #Write ADC ASIC SPI
            print("FEMB_CONFIG--> Program ADC ASIC SPI")
            self.femb.write_reg ( self.REG_ASIC_SPIPROG, 1)
            time.sleep(0.1)
            self.femb.write_reg ( self.REG_ASIC_SPIPROG, 1)
            time.sleep(0.1)

            self.femb.write_reg ( 18, 0x0)
            time.sleep(0.1)

            print("FEMB_CONFIG--> Check ADC ASIC SPI")
            adcasic_rb_regs = []
            for regNum in range(self.REG_ADCSPI_RDBACK_BASE,self.REG_ADCSPI_RDBACK_BASE+len(Adcasic_regs),1):
                val = self.femb.read_reg ( regNum ) 
                adcasic_rb_regs.append( val )

            #print("  ADC ASIC read back: ",adcasic_rb_regs)
            if (adcasic_rb_regs !=Adcasic_regs  ) :
                if ( k == 1 ):
                    sys.exit("femb_config : Wrong readback. ADC SPI failed")
                    return
                print("FEMB_CONFIG--> ADC ASIC Readback didn't match, retrying...")
            else: 
                print("FEMB_CONFIG--> ADC ASIC SPI is OK")
                break
        #enable streaming
        #self.femb.write_reg ( 9, 0x8)
        #LBNE_ADC_MODE

    def configFeAsic_regs(self,feasic_regs):
        print("FEMB_CONFIG--> Config FE ASIC SPI")
        assert(len(feasic_regs)==34)

        for k in range(10):
            i = 0
            for regNum in range(self.REG_FESPI_BASE,self.REG_FESPI_BASE+len(feasic_regs),1):
                self.femb.write_reg ( regNum, feasic_regs[i])
                i = i + 1
            #Write FE ASIC SPI
            print("FEMB_CONFIG--> Program FE ASIC SPI")
            self.femb.write_reg ( self.REG_ASIC_SPIPROG, 2)
            self.femb.write_reg ( self.REG_ASIC_SPIPROG, 2)

            print("FEMB_CONFIG--> Check FE ASIC SPI")
            feasic_rb_regs = []
            for regNum in range(self.REG_FESPI_RDBACK_BASE,self.REG_FESPI_RDBACK_BASE+len(feasic_regs),1):
                val = self.femb.read_reg ( regNum ) 
                feasic_rb_regs.append( val )

            if (feasic_rb_regs !=feasic_regs  ) :
                if ( k == 9 ):
                    sys.exit("femb_config_femb : Wrong readback. FE SPI failed")
                    return
                print("FEMB_CONFIG--> FE ASIC Readback didn't match, retrying...")
                if len(feasic_rb_regs) == len(feasic_regs):
                    print("{:15} {:15}".format("feasic_rb_regs","feasic_regs"))
                    for iReg in range(len(feasic_rb_regs)):
                        print("{:#010x}      {:#010x}".format(feasic_rb_regs[iReg],feasic_regs[iReg]))
                else:
                    print("lens don't match: {} != {}".format(len(feasic_rb_regs),len(feasic_regs)))
            else: 
                print("FEMB_CONFIG--> FE ASIC SPI is OK")
                #print("{:15} {:15}".format("feasic_rb_regs","feasic_regs"))
                #for iReg in range(len(feasic_rb_regs)):
                #    print("{:#010x}      {:#010x}".format(feasic_rb_regs[iReg],feasic_regs[iReg]))
                break

    def configFeAsic(self,gain,shape,base,slk=None,slkh=None,monitorBandgap=None,monitorTemp=None):
        """
        Configure FEs with given gain/shape/base values.
        Also, configure leakage current slk = 0 for 500 pA, 1 for 100 pA
            and slkh = 0 for 1x leakage current, 1 for 10x leakage current
        if monitorBandgap is True: monitor bandgap instead of signal
        if monitorTemp is True: monitor temperature instead of signal
        """
        gain = int("{:02b}".format(gain)[::-1],2) # need to reverse bits, use string/list tricks
        shape = int("{:02b}".format(shape)[::-1],2) # need to reverse bits, use string/list tricks
        if slk is None:
            slk=0
        if slkh is None:
            slkh=0
        if monitorBandgap and monitorTemp:
            raise Exception("You can't monitor bandgap and temperature at the same time. Set either monitorBandgap or monitorTemp False")
        stb=0
        if monitorBandgap:
            stb=0b11
        if monitorTemp:
            stb=0b10
        self.fe_reg.set_fe_sbnd_board(snc=base,sg=gain,st=shape,slk0=slk,stb=stb)
        self.configFeAsic_regs(self.fe_reg.REGS)

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
            print(offsetCurrent,bin(offsetCurrent))
            offsetCurrent = int("{:04b}".format(offsetCurrent)[::-1],2) # need to reverse bits, use string/list tricks
            print(offsetCurrent,bin(offsetCurrent))
        if testInput is None:
            testInput=0
        if freqInternal is None:
            freqInternal=0
        if sleep is None:
            sleep=0
        if pdsr is None:
            pdsr=0
        if pcsr is None:
            pcsr=0
        clk0=0
        clk1=0
        if clockExternal:
            clk0=1
            clk1=0
        elif clockFromFIFO:
            clk0=0
            clk1=1
        self.adc_reg.set_sbnd_board(en_gr=enableOffsetCurrent,d=offsetCurrent,tstin=testInput,frqc=freqInternal,slp=sleep,pdsr=pdsr,pcsr=pcsr,clk0=clk0,clk1=clk1,f1=f1,f2=f2)
        self.configAdcAsic_regs(self.adc_reg.REGS)

    def selectChannel(self,asic,chan, hsmode= 1 ):
        asicVal = int(asic)
        if (asicVal < 0 ) or (asicVal >= self.NASICS ) :
                print( "femb_config_femb : selectChan - invalid ASIC number, only 0 to {} allowed".format(self.NASICS-1))
                return
        chVal = int(chan)
        if (chVal < 0 ) or (chVal > 15 ) :
                print("femb_config_femb : selectChan - invalid channel number, only 0 to 15 allowed")
                return
        hsmodeVal = int(hsmode)
        if (hsmodeVal != 0 ) and ( hsmodeVal != 1 ) :
                print("FEMB_CONFIG--> femb_config_femb : selectChan - invalid HS mode")
                return

        print("FEMB_CONFIG--> Selecting ASIC " + str(asicVal) + ", channel " + str(chVal))

        self.femb.write_reg ( self.REG_HS, hsmodeVal)
        self.femb.write_reg ( self.REG_HS, hsmodeVal)
        regVal = (chVal << 8 ) + asicVal
        self.femb.write_reg ( self.REG_SEL_CH, regVal)
        self.femb.write_reg ( self.REG_SEL_CH, regVal)

    def setInternalPulser(self,pulserEnable,pulseHeight):
        if pulserEnable:
            print("Enabling internal FPGA DAC")

            # turn on test capacitor on all FE ASIC channels
            fe_reg = copy.deepcopy(self.fe_reg.REGS)

            self.fe_reg.set_fe_sbnd_board(sts=1)
            for i in range(len(fe_reg)):
                self.fe_reg.REGS[i] = fe_reg[i] | self.fe_reg.REGS[i]
                print(hex(self.fe_reg.REGS[i]))

            self.configFeAsic_regs(self.fe_reg.REGS)

            # internal FPGA DAC settings
            freq = 20 # number of samples between pulses
            dly = 80 # dly*5ns sets inteval between where FPGA starts pulse and ADC samples 
            ampl =  pulseHeight % 32 # mV injected
            int_dac = 0 # or 0xA1
            dac_meas = int_dac  # or 60
            reg_5_value = ((freq<<16)&0xFFFF0000) + ((dly<<8)&0xFF00) + ( (dac_meas|ampl)& 0xFF )
            self.femb.write_reg ( 5, reg_5_value)

            # set to pulser mode (0x01) and enable FPGA DAC (0x01xx)
            self.femb.write_reg(16, 0x0101)
            print(self.femb.read_reg(16))
        else:
            print("Disabling pulser (still testing may not work)")

            # disable test capacitor
            fe_reg = copy.deepcopy(self.fe_reg.REGS)

            self.fe_reg.set_fe_sbnd_board(sts=0)
            for i in range(len(fe_reg)):
                self.fe_reg.REGS[i] = fe_reg[i] | self.fe_reg.REGS[i]
                print(hex(self.fe_reg.REGS[i]))

            self.configFeAsic_regs(self.fe_reg.REGS)

            # disable pulser mode
            self.femb.write_reg(16, 0x0)
            print(self.femb.read_reg(16))

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

    def get_rawdata_chipXchnX(self, chip=0, chn=0):
        i = 0
        while ( 1 ):
            i = i + 1
            self.selectChannel(chip,chn,1)
            data = self.femb.get_rawdata()
            #make sure the data belong to chipXchnX
            data0 =struct.unpack_from(">1H",data[0:2])
            if( len(data) > 2 ):
                if ( (data0[0] >> 12 ) == chn ):
                    if ( i > 1):
                        print("FEMB_CONFIG--> get_rawdata_chipXchnX--> cycle%d to get right data"%i)
                    break
        return data

    def get_rawdata_packets_chipXchnX(self, chip=0, chn=0, val = 10 ):
        i = 0
        while ( 1 ):
            self.selectChannel(chip,chn,1)
            data = self.femb.get_rawdata_packets(val)
            #make sure the data belong to chnX
            if( len(data) > 2 ):
                data0 =struct.unpack_from(">1H",data[0:2])
                if ( (data0[0] >> 12 ) == chn ):
                    if ( i > 1):
                        print("FEMB_CONFIG--> get_rawdata_chipXchnX--> cycle%d to get right data"%i)
                    break
        return data

    def enablePulseMode(self,srcflag):
        #Configures board in test pulse mode
        #srcflag = 0 means external input is enabled
        #srcflag = 1 means internal FPGA DAC is enabled with default settings
        #srcflag = 99 means turn it off
        #ETW just playing around with the internal DAC settings not sure this works
        srcflag = int(srcflag)
        if (srcflag==1):
            print("Enabling internal FPGA DAC")

            # turn on test capacitor on all FE ASIC channels
            fe_reg = copy.deepcopy(self.fe_reg.REGS)

            self.fe_reg.set_fe_sbnd_board(sts=1)
            for i in range(len(fe_reg)):
                self.fe_reg.REGS[i] = fe_reg[i] | self.fe_reg.REGS[i]
                print(hex(self.fe_reg.REGS[i]))

            self.configFeAsic_regs(self.fe_reg.REGS)

            # internal FPGA DAC settings
            freq = 20 # number of samples between pulses
            dly = 80 # dly*5ns sets inteval between where FPGA starts pulse and ADC samples 
            ampl =  20 % 32 # mV injected
            int_dac = 0 # or 0xA1
            dac_meas = int_dac  # or 60
            reg_5_value = ((freq<<16)&0xFFFF0000) + ((dly<<8)&0xFF00) + ( (dac_meas|ampl)& 0xFF )
            self.femb.write_reg ( 5, reg_5_value)

            # set to pulser mode (0x01) and enable FPGA DAC (0x01xx)
            self.femb.write_reg(16, 0x0101)
            print(self.femb.read_reg(16))

        elif (srcflag==0):
            print("Enabling external pulse (still testing may not work)")

            # turn on test capacitor on all FE ASIC channels
            fe_reg = copy.deepcopy(self.fe_reg.REGS)

            self.fe_reg.set_fe_sbnd_board(sts=1)
            for i in range(len(fe_reg)):
                self.fe_reg.REGS[i] = fe_reg[i] | self.fe_reg.REGS[i]
                print(hex(self.fe_reg.REGS[i]))

            self.configFeAsic_regs(self.fe_reg.REGS)

            # set to pulser mode (0x01) and enable external input (0x00xx)
            self.femb.write_reg(16, 0x0001)
            print(self.femb.read_reg(16))

        elif (srcflag==99):
            print("Disabling pulser (still testing may not work)")

            # disable test capacitor
            fe_reg = copy.deepcopy(self.fe_reg.REGS)

            self.fe_reg.set_fe_sbnd_board(sts=0)
            for i in range(len(fe_reg)):
                self.fe_reg.REGS[i] = fe_reg[i] | self.fe_reg.REGS[i]
                print(hex(self.fe_reg.REGS[i]))

            self.configFeAsic_regs(self.fe_reg.REGS)

            # disable pulser mode
            self.femb.write_reg(16, 0x0)
            print(self.femb.read_reg(16))

        else:
            print("Source flag must be 0 (ext), 1 (dac), or 99 (disable)")

