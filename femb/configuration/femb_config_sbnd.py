#!/usr/bin/env python33

import sys 
import string
import time
import struct
from femb_udp_cmdline import FEMB_UDP
from adc_asic_reg_mapping import ADC_ASIC_REG_MAPPING
from fe_asic_reg_mapping import FE_ASIC_REG_MAPPING

class FEMB_CONFIG:

    def resetBoard(self):
        #Reset system
        self.femb.write_reg_i2c ( self.REG_RESET, 1)

        #Reset registers
        self.femb.write_reg_i2c ( self.REG_RESET, 2)

        #Time stamp reset
        #femb.write_reg_i2c ( 0, 4)
        
        #Reset ADC ASICs
        self.femb.write_reg_i2c ( self.REG_ASIC_RESET, 1)

    def initBoard(self):
        print "FEMB_CONFIG--> Reset FEMB"
        #set up default registers
        
        #Reset ADC ASICs
        self.femb.write_reg_i2c( self.REG_ASIC_RESET, 1)

        #Set ADC test pattern register
        self.femb.write_reg_i2c ( 3, 0x01170000) #31 - enable ADC test pattern, 

        #Set ADC latch_loc
        self.femb.write_reg_i2c ( self.REG_LATCHLOC1_4, self.REG_LATCHLOC1_4_data )
        self.femb.write_reg_i2c ( self.REG_LATCHLOC5_8, self.REG_LATCHLOC5_8_data )
        #Set ADC clock phase
        self.femb.write_reg_i2c ( self.REG_CLKPHASE, self.REG_CLKPHASE_data)

        #internal test pulser control
        freq = 500
        dly = 80
        ampl = 0 % 32
        int_dac = 0 # or 0xA1
        dac_meas = int_dac  # or 60
        reg_5_value = ((freq<<16)&0xFFFF0000) + ((dly<<8)&0xFF00) + ( (dac_meas|ampl)& 0xFF )
        self.femb.write_reg_i2c ( 5, reg_5_value)
        self.femb.write_reg_i2c (16, 0x0)

        self.femb.write_reg_i2c ( 13, 0x0) #enable

        #Set test and readout mode register
        self.femb.write_reg_i2c ( 7, 0x0000) #11-8 = channel select, 3-0 = ASIC select
        self.femb.write_reg_i2c ( 17, 1) #11-8 = channel select, 3-0 = ASIC select

        #set default value to FEMB ADCs and FEs
        self.configAdcAsic(self.adc_reg.REGS)
        self.configFeAsic(self.fe_reg.REGS)

        #Set number events per header -- no use
        #self.femb.write_reg_i2c ( 8, 0x0)
        print "FEMB_CONFIG--> Reset FEMB is DONE"

    def configAdcAsic(self,Adcasic_regs):
        #ADC ASIC SPI registers
        print "FEMB_CONFIG--> Config ADC ASIC SPI"
        for k in range(10):
            i = 0
            for regNum in range(self.REG_ADCSPI_BASE,self.REG_ADCSPI_BASE+len(Adcasic_regs),1):
                    self.femb.write_reg_i2c ( regNum, Adcasic_regs[i])
                    i = i + 1

            #ADC ASIC sync
            #self.femb.write_reg_i2c ( 17, 0x1) # controls HS link, 0 for on, 1 for off
            #self.femb.write_reg_i2c ( 17, 0x0) # controls HS link, 0 for on, 1 for off        

            #Write ADC ASIC SPI
            print "FEMB_CONFIG--> Program ADC ASIC SPI"
            self.femb.write_reg_i2c ( self.REG_ASIC_SPIPROG, 1)
            time.sleep(0.1)
            self.femb.write_reg_i2c ( self.REG_ASIC_SPIPROG, 1)
            time.sleep(0.1)

            self.femb.write_reg_i2c ( 18, 0x0)
            time.sleep(0.1)

            print "FEMB_CONFIG--> Check ADC ASIC SPI"
            adcasic_rb_regs = []
            for regNum in range(self.REG_ADCSPI_RDBACK_BASE,self.REG_ADCSPI_RDBACK_BASE+len(Adcasic_regs),1):
                val = self.femb.read_reg_i2c ( regNum ) 
                adcasic_rb_regs.append( val )

            if (adcasic_rb_regs !=Adcasic_regs  ) :
                if ( k == 1 ):
                    sys.exit("femb_config : Wrong readback. ADC SPI failed")
                    return
            else: 
                print "FEMB_CONFIG--> ADC ASIC SPI is OK"
                break
        #enable streaming
        #self.femb.write_reg_i2c ( 9, 0x8)
        #LBNE_ADC_MODE


    def configFeAsic(self,feasic_regs):
        print "FEMB_CONFIG--> Config FE ASIC SPI"
        print len(feasic_regs)

        for k in range(10):
            i = 0
            for regNum in range(self.REG_FESPI_BASE,self.REG_FESPI_BASE+len(feasic_regs),1):
                self.femb.write_reg_i2c ( regNum, feasic_regs[i])
                i = i + 1
            #Write FE ASIC SPI
            print "FEMB_CONFIG--> Program FE ASIC SPI"
            self.femb.write_reg_i2c ( self.REG_ASIC_SPIPROG, 2)
            self.femb.write_reg_i2c ( self.REG_ASIC_SPIPROG, 2)

            print "FEMB_CONFIG--> Check FE ASIC SPI"
            feasic_rb_regs = []
            for regNum in range(self.REG_FESPI_RDBACK_BASE,self.REG_FESPI_RDBACK_BASE+len(feasic_regs),1):
                val = self.femb.read_reg_i2c ( regNum ) 
                feasic_rb_regs.append( val )

            if (feasic_rb_regs !=feasic_regs  ) :
                if ( k == 9 ):
                    sys.exit("femb_config_femb : Wrong readback. FE SPI failed")
                    return
            else: 
                print "FEMB_CONFIG--> FE ASIC SPI is OK"
                break

    def selectChannel(self,asic,chan, allchn ):
        asicVal = int(asic)
        if (asicVal < 0 ) or (asicVal > 7 ) :
                print "FEMB_CONFIG--> femb_config_femb : selectChan - invalid ASIC number"
                return
        chVal = int(chan)
        if (chVal < 0 ) or (chVal > 15 ) :
                print "FEMB_CONFIG--> femb_config_femb : selectChan - invalid channel number"
                return
        allchnVal = int(allchn)
        if (allchnVal != 0 ) and ( allchnVal != 1 ) :
                print "FEMB_CONFIG--> femb_config_femb : selectChan - invalid HS mode"
                return

        print "FEMB_CONFIG--> Selecting ASIC " + str(asicVal) + ", channel " + str(chVal)

        self.femb.write_reg_i2c ( self.REG_HS, allchnVal)
        self.femb.write_reg_i2c ( self.REG_HS, allchnVal)
        regVal = (chVal << 8 ) + asicVal
        self.femb.write_reg_i2c ( self.REG_SEL_CH, regVal)
        self.femb.write_reg_i2c ( self.REG_SEL_CH, regVal)

    def syncADC(self):
        #turn on ADC test mode
        print "FEMB_CONFIG--> Start sync ADC"
        reg3 = self.femb.read_reg_i2c (3)
        newReg3 = ( reg3 | 0x80000000 )

        self.femb.write_reg_i2c ( 3, newReg3 ) #31 - enable ADC test pattern
        for a in range(0,8,1):
                print "FEMB_CONFIG--> Test ADC " + str(a)
                unsync = self.testUnsync(a)
                if unsync != 0:
                        print "FEMB_CONFIG--> ADC not synced, try to fix"
                        self.fixUnsync(a)
        self.REG_LATCHLOC1_4_data = self.femb.read_reg_i2c ( self.REG_LATCHLOC1_4 ) 
        self.REG_LATCHLOC5_8_data = self.femb.read_reg_i2c ( self.REG_LATCHLOC5_8 )
        self.REG_CLKPHASE_data    = self.femb.read_reg_i2c ( self.REG_CLKPHASE )
        print "FEMB_CONFIG--> Latch latency " + str(hex(self.REG_LATCHLOC1_4_data)) \
                        + str(hex(self.REG_LATCHLOC5_8_data )) + \
                        "\tPhase " + str(hex(self.REG_CLKPHASE_data))
        self.femb.write_reg_i2c ( 3, (reg3&0x7fffffff) )
        self.femb.write_reg_i2c ( 3, (reg3&0x7fffffff) )
        print "FEMB_CONFIG--> End sync ADC"

    def testUnsync(self, adc):
        adcNum = int(adc)
        if (adcNum < 0 ) or (adcNum > 7 ):
                print "FEMB_CONFIG--> femb_config_femb : testLink - invalid asic number"
                return
        
        #loop through channels, check test pattern against data
        badSync = 0
        for ch in range(0,16,1):
                self.selectChannel(adcNum,ch, 1)
                time.sleep(0.1)                
                for test in range(0,100,1):
                        data = self.femb.get_data()
                        for samp in data[0:(16*1024+1023)]:
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
                print "FEMB_CONFIG--> femb_config_femb : testLink - invalid asic number"
                return

        initLATCH1_4 = self.femb.read_reg_i2c ( self.REG_LATCHLOC1_4 )
        initLATCH5_8 = self.femb.read_reg_i2c ( self.REG_LATCHLOC5_8 )
        initPHASE = self.femb.read_reg_i2c ( self.REG_CLKPHASE )

        #loop through sync parameters
        for phase in range(0,2,1):
                clkMask = (0x1 << adcNum)
                testPhase = ( (initPHASE & ~(clkMask)) | (phase << adcNum) ) 
                self.femb.write_reg_i2c ( self.REG_CLKPHASE, testPhase )
                for shift in range(0,16,1):
                        shiftMask = (0x3F << 8*adcNum)
                        if ( adcNum < 4 ):
                            testShift = ( (initLATCH1_4 & ~(shiftMask)) | (shift << 8*adcNum) )
                            self.femb.write_reg_i2c ( self.REG_LATCHLOC1_4, testShift )
                        else:
                            testShift = ( (initLATCH5_8 & ~(shiftMask)) | (shift << 8*adcNum) )
                            self.femb.write_reg_i2c ( self.REG_LATCHLOC5_8, testShift )
                        #reset ADC ASIC
                        self.femb.write_reg_i2c ( self.REG_ASIC_RESET, 1)
                        time.sleep(0.01)
                        self.femb.write_reg_i2c ( self.REG_ASIC_SPIPROG, 1)
                        time.sleep(0.01)
                        self.femb.write_reg_i2c ( self.REG_ASIC_SPIPROG, 1)
                        time.sleep(0.01)
                        #test link
                        unsync = self.testUnsync(adcNum)
                        if unsync == 0 :
                                print "FEMB_CONFIG--> ADC synchronized"
                                return
        #if program reaches here, sync has failed
        print "FEMB_CONFIG--> ADC SYNC process failed for ADC # " + str(adc)

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
                        print "FEMB_CONFIG--> get_rawdata_chipXchnX--> cycle%d to get right data"%i
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
                        print "FEMB_CONFIG--> get_rawdata_chipXchnX--> cycle%d to get right data"%i
                    break
        return data

    #__INIT__#
    def __init__(self):
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

        #initialize FEMB UDP object
        self.femb = FEMB_UDP()
        self.adc_reg = ADC_ASIC_REG_MAPPING()
        self.fe_reg = FE_ASIC_REG_MAPPING() 

