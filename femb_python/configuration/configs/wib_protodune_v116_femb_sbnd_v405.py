#!/usr/bin/env python33

"""
Configuration for SBND FEMB + protoDUNE WIB Setup
WIB firmware v116
FEMB firmware v405
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
        self.REG_SOFT_ADC_RESET = 1

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
        self.REG_HS = 17

        self.INT_TP_EN = 18
        self.EXT_TP_EN = 18

        self.REG_SPI_BASE = 0x200
        self.REG_SPI_RDBACK_BASE = 0x250
        
        self.REG_TEST_PAT = 3
        self.REG_TEST_PAT_DATA = 0x01230000

        #COTS shifts
        self.fe1_sft = 0x00000000
        self.fe2_sft = 0x00000000
        self.fe3_sft = 0x00000000
        self.fe4_sft = 0x00000000
        self.fe5_sft = 0x00000000
        self.fe6_sft = 0x00000000
        self.fe7_sft = 0x00000000
        self.fe8_sft = 0x00000000

        #COTS phases
        self.fe1_pha = 0x00000000
        self.fe2_pha = 0x00000000
        self.fe3_pha = 0x00000000
        self.fe4_pha = 0x00000000
        self.fe5_pha = 0x00000000
        self.fe6_pha = 0x00000000
        self.fe7_pha = 0x00000000
        self.fe8_pha = 0x00000000

                
        #internal variables
        self.fembNum = 0
        self.useExtAdcClock = True
        self.isRoomTemp = False
        self.maxSyncAttempts = 100
        self.doReSync = True
        self.spiStatus = 0x0
        self.syncStatus = 0x0
        self.CLKSELECT_val_RT = 0xFF
        self.CLKSELECT2_val_RT = 0xFF
        self.CLKSELECT_val_CT = 0xEF
        self.CLKSELECT2_val_CT = 0xEF
        self.REG_LATCHLOC_3_TO_0_val = 0x04040404
        self.REG_LATCHLOC_7_TO_4_val = 0x04040404
        self.fe_regs = [0x00000000]*(16+2)*8*8
        self.fe_REGS = [0x00000000]*(8+1)*4

        #initialize FEMB UDP object
        self.femb = FEMB_UDP()
        self.femb.UDP_PORT_WREG = 32000 #WIB PORTS
        self.femb.UDP_PORT_RREG = 32001
        self.femb.UDP_PORT_RREGRESP = 32002
        self.femb.doReadBack = True #WIB register interface is unreliable

        #ASIC config variables
        self.feasicLeakage = 0 #0 = 500pA, 1 = 100pA
        self.feasicLeakagex10 = 0 #0 = pA, 1 = pA*10
        self.feasicAcdc = 0 #AC = 0, DC = 1
        
        self.feasicEnableTestInput = 0 #0 = disabled, 1 = enabled
        self.feasicBaseline = 0 #0 = 200mV, 1 = 900mV
        self.feasicGain = 2 #4.7,7.8,14,25
        self.feasicShape = 1 #0.5,1,2,3
        self.feasicBuf = 0 #0 = OFF, 1 = ON

    def printParameters(self):
        print("FEMB #             \t",self.fembNum)
        print("External ADC Clocks\t",self.useExtAdcClock)
        print("Room temperature   \t",self.isRoomTemp)
        print("MAX SYNC ATTEMPTS  \t",self.maxSyncAttempts)
        print("Do resync          \t",self.doReSync)
        print("CLKSELECT RT       \t",str(hex(self.CLKSELECT_val_RT)))
        print("CLKSELECT2 RT      \t",str(hex(self.CLKSELECT2_val_RT)))
        print("CLKSELECT CT       \t",str(hex(self.CLKSELECT_val_CT)))
        print("CLKSELECT2 CT      \t",str(hex(self.CLKSELECT2_val_CT)))
        print("LATCHLOC_3_TO_0    \t",str(hex(self.REG_LATCHLOC_3_TO_0_val)))
        print("LATCHLOC_7_TO_4    \t",str(hex(self.REG_LATCHLOC_7_TO_4_val)))
        print("FE-ASIC leakage    \t",self.feasicLeakage)
        print("FE-ASIC leakage x10\t",self.feasicLeakagex10)
        print("FE-ASIC AD/DC      \t",self.feasicAcdc)
        print("FE-ASIC test input \t",self.feasicEnableTestInput)
        print("FE-ASIC baseline   \t",self.feasicBaseline)
        print("FE-ASIC gain       \t",self.feasicGain)
        print("FE-ASIC shape      \t",self.feasicShape)
        print("FE-ASIC buffer     \t",self.feasicBuf)

        print("FE-ASIC config")
        for regNum in range(self.REG_SPI_BASE,self.REG_SPI_BASE+72,1):
            regVal = self.femb.read_reg( regNum)
            if regVal == None:
                continue
            print( str(regNum) + "\t" + str(hex(regVal)) )

    def resetBoard(self):
        print("Reset")

    def initBoard(self):
        self.initWib()
        for femb in range(1,2,1):
            self.selectFemb(femb)
            self.initFemb()
        
    def initWib(self):
        #WIB initialization

        #set UDP ports to WIB registers
        self.wib_reg_enable()

        #register 2, LED
        #self.femb.write_reg_bits(2 , 0, 0xFF, 0 )

        #set jumbo size
        self.femb.write_reg(0x1F,0xEFB)

        #set external clock
        self.femb.write_reg(0x4, 8)
        self.femb.write_reg(16,0x7F00)
        self.femb.write_reg(15,0)

        #sync timestamp /WIB
        self.femb.write_reg(1,0)
        self.femb.write_reg(1,0)
        self.femb.write_reg(1,2)
        self.femb.write_reg(1,2)                
        self.femb.write_reg(1,0)
        self.femb.write_reg(1,0)

        #Reset error /WIB
        self.femb.write_reg(18, 0x8000)
        self.femb.write_reg(18, 0x8000)

        #return register interface to FEMB
        self.selectFemb(self.fembNum)

    def initFemb(self):
        if (self.fembNum < 0) or (self.fembNum >= self.NFEMBS ):
            return

        #FEMB power enable on WIB
        self.powerOnFemb(self.fembNum)
        time.sleep(4)

        #Make sure register interface is for correct FEMB
        self.selectFemb(self.fembNum)

        #check if FEMB register interface is working
        print("Checking register interface")
        regVal = self.femb.read_reg(6)
        if (regVal == None) or (regVal == -1):
            print("Error - FEMB register interface is not working.")
            print(" Will not initialize FEMB.")       
            return

        checkFirmware = self.checkFirmwareVersion()
        if checkFirmware == False:
            print("Error - invalid firmware, will not attempt to initialize board")
            return

        #turn off pulser
        self.femb.write_reg_bits( self.REG_FPGA_TP_EN, 0,0x1,0) #test pulse enable
        self.femb.write_reg_bits( self.REG_ASIC_TP_EN, 1,0x1,0) #test pulse enable
        self.femb.write_reg_bits( self.REG_DAC_SELECT, 8,0x1,0) #test pulse enable
        self.femb.write_reg_bits( self.REG_TP, 0,0x1F,0x00) #test pulse amplitude
        self.femb.write_reg_bits( self.REG_TP, 16,0xFFFF,0x100) #test pulse frequency
        self.femb.write_reg_bits( self.REG_TP, 8,0xFF,0x00) #test pulse delay

        #Timestamp reset
        self.femb.write_reg(0, 4)
        self.femb.write_reg(0, 4)

        #Reset SPI
        self.femb.write_reg(self.REG_ASIC_RESET,1)
        self.femb.write_reg(self.REG_ASIC_RESET,1)
        self.femb.write_reg(self.REG_ASIC_RESET,2)
        self.femb.write_reg(self.REG_ASIC_RESET,2)

        self.femb.write_reg(self.REG_TEST_PAT, self.REG_TEST_PAT_DATA)

        #Turn off readback checking for ASIC config
        self.femb.doReadBack = False
        self.set_cots_shift()
        
        #Set ASIC SPI configuration registers
        self.configFeAsic()

        #check ASIC SPI
        self.checkFembSpi()
        print("SPI STATUS","\t",self.spiStatus)

        #check ADC SYNC
        self.checkSync()
        print("SYNC STATUS","\t",self.syncStatus)

    #Test FEMB SPI working
    def checkFembSpi(self):
        print("Check ASIC SPI")
         
        self.spiStatus = 0

        for k in range(2):
            #Disable streaming
            self.femb.write_reg(9, 0x0)
            time.sleep(0.01)

            i = 0
            for regNum in range(self.REG_SPI_BASE,self.REG_SPI_BASE+len(self.fe_REGS),1):
                self.femb.write_reg( regNum, self.fe_REGS[i])
                i += 1
            time.sleep(0.01)
            self.femb.write_reg( self.REG_ASIC_SPIPROG, 1)

            if (k==1):
                for j in range(3):
                    self.spiStatus = 0
                    time.sleep(0.01)
                    readvals = []
                    for regNum in range(self.REG_SPI_RDBACK_BASE,self.REG_SPI_RDBACK_BASE+len(self.fe_REGS),1):
                        rdbckVal = self.femb.read_reg( regNum)
                        if rdbckVal == None :
                            print("Error - FEMB register interface is not working.")
                            return
                        else:
                            readvals.append(rdbckVal)
                        time.sleep(0.001)

                    for i in range(len(self.fe_REGS)):
                        print(hex(self.fe_REGS[i]),"\t",hex(readvals[i]))
                        if self.fe_REGS[i] != readvals[i] :
                            print("SPI readback failed.")
                            self.spiStatus = 1
                if self.spiStatus == 1:            
                    return

    def checkSync(self):
        print("Check ASIC SYNC")
        regVal = self.femb.read_reg(6)
        if regVal == None:
            print("doAsicConfigcheckFembSpi: Could not check SYNC status, bad")
            return
        syncVal = ((regVal >> 16) & 0xFFFF)
        self.syncStatus = syncVal

    #Setup talking to WIB
    def wib_reg_enable(self):
        self.femb.UDP_PORT_WREG = 32000
        self.femb.UDP_PORT_RREG = 32001
        self.femb.UDP_PORT_RREGRESP = 32002
        self.femb.REG_SLEEP = 0.001
        wib7val = self.femb.read_reg(7)
        time.sleep(0.001)
        wib7val = self.femb.read_reg(7)        
        wib7val = wib7val & 0x00000000
        self.femb.write_reg(7, wib7val)

    #COTS Shift and Phase Settings
    def set_cots_shift(self):
        print("Setting COTS Shifts")
        self.femb.write_reg(21,self.fe1_sft)
        self.femb.write_reg(29,self.fe1_pha)
        self.femb.write_reg(22,self.fe2_sft)
        self.femb.write_reg(30,self.fe2_pha)
        self.femb.write_reg(23,self.fe3_sft)
        self.femb.write_reg(31,self.fe3_pha)
        self.femb.write_reg(24,self.fe4_sft)
        self.femb.write_reg(32,self.fe4_pha)
        self.femb.write_reg(25,self.fe5_sft)
        self.femb.write_reg(33,self.fe5_pha)
        self.femb.write_reg(26,self.fe6_sft)
        self.femb.write_reg(34,self.fe6_pha)
        self.femb.write_reg(27,self.fe7_sft)
        self.femb.write_reg(35,self.fe7_pha)
        self.femb.write_reg(28,self.fe8_sft)
        self.femb.write_reg(36,self.fe8_pha)

        self.femb.write_reg(8,0)
        self.femb.write_reg(8,0)
        time.sleep(0.02)
        self.femb.write_reg(8,0x10)
        self.femb.write_reg(8,0x10)

        
    #FEMB power enable on WIB
    def powerOnFemb(self,femb):
        fembVal = int(femb)
        if (fembVal < 0) or (fembVal > 3 ):
            return

        #set UDP ports to WIB registers
        self.wib_reg_enable()
        
        # read back existing power setting
        oldVal = self.femb.read_reg(8)
        
        #FEMB power enable
        if(fembVal == 0):
            regVal = 0x1000F
        if(fembVal == 1):
            regVal = 0x200F0
        if(fembVal == 2):
            regVal = 0x40F00
        if(fembVal == 3):
            regVal = 0x8F000

        pwrVal = 0x100000 | regVal | oldVal

        self.femb.write_reg(8, 0)
        time.sleep(3)
        self.femb.write_reg(8, pwrVal)
        time.sleep(5)
        
        regVal = self.femb.read_reg(8)
        if regVal == None:
            return
        print("FEMB Power on: ", hex(regVal))

        #set UDP ports back to normal
        self.selectFemb(self.fembNum)

    def powerOffFemb(self,femb):
        fembVal = int(femb)
        if (fembVal < 0) or (fembVal > 3 ):
            return

        #set UDP ports to WIB registers
        self.wib_reg_enable()

        # read back existing power setting
        oldVal = self.femb.read_reg(8)

        #FEMB power disable
        if(fembVal == 0):
            regVal = 0x1000F
        if(fembVal == 1):
            regVal = 0x200F0
        if(fembVal == 2):
            regVal = 0x40F00
        if(fembVal == 3):
            regVal = 0x8F000
        
        pwrVal = 0x100000 | (regVal ^ oldVal)

        self.femb.write_reg(8, pwrVal)
        
        regVal = self.femb.read_reg(8)
        if regVal == None:
            return
        print("FEMB Power off: ", hex(regVal))        
        
        #set UDP ports back to normal
        self.selectFemb(self.fembNum)
        
    def selectChannel(self,asic,chan):
        #print("Select channel")
        asicVal = int(asic)
        if (asicVal < 0 ) or (asicVal > self.NASICS):
            return

        #set UDP ports to WIB
        self.wib_reg_enable()

        #select ASIC
        #print("Selecting ASIC " + str(asicVal) )
        self.femb.write_reg_bits(self.REG_SEL_ASIC , self.REG_SEL_ASIC_LSB, 0xF, asicVal )

        #Note: WIB data format streams all 16 channels, don't need to select specific channel

        #set UDP ports back to normal
        self.selectFemb(self.fembNum)
    
    def configFeAsic(self):
        print("CONFIG ASICs")

        # #global config varibles
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

        #gain
        gainArray = [0,2,1,3] #00=4.7, 10=7.8, 01=14, 11=25
        gainValCorrect = gainArray[gainVal]
        
        #shape
        shapeArray = [2,0,3,1] #00=1.0, 10=0.5, 01=3.0, 11=2.0
        shapeValCorrect = shapeArray[shapeVal]

        #COTS Register Settings
        sts = testVal
        snc = baseVal
        sg = gainValCorrect
        st = shapeValCorrect
        smn = 0 #Output monitor enabled: not currently an option in femb_python so keep at 0 for now
        sdf = bufVal
        chn_reg = ((sts&0x01)<<7) + ((snc&0x01)<<6) + ((sg&0x03)<<4) + ((st&0x03)<<2)  + ((smn&0x01)<<1) + ((sdf&0x01)<<0)

        #COTS Global Register Settings
        slk0 = feasicLeakageVal
        stb1 = 0 #Monitors not currently used in femb_python
        stb = 0 #Monitors not currently used in femb_python
        s16 = 0 #High filter in channel 16 disabled
        slk1 = feasicLeakagex10Val
        sdc = acdcVal
        swdac = 0 #For pulser, set elsewhere
        dac = 0 #For pulser, set elsewhere
        global_reg = ((slk0&0x01)<<0) + ((stb1&0x01)<<1) + ((stb&0x01)<<2)+ ((s16&0x01)<<3) + ((slk1&0x01)<<4) + ((sdc&0x01)<<5) +((00&0x03)<<6)
        dac_reg = (((dac&0x01)//0x01)<<7)+(((dac&0x02)//0x02)<<6)+\
                  (((dac&0x04)//0x04)<<5)+(((dac&0x08)//0x08)<<4)+\
                  (((dac&0x10)//0x10)<<3)+(((dac&0x20)//0x20)<<2)+\
                  (((swdac&0x03))<<0)
        
        for chip in range(8):
            for chn in range(16):
                chn_reg_bool = []
                for j in range(8):
                    chn_reg_bool.append ( bool( (chn_reg>>j)%2 ))
                start_pos = (8*16+16)*chip + (16-chn)*8
                self.fe_regs[start_pos-8 : start_pos] = chn_reg_bool

            global_reg_bool = []
            for j in range(8):
                global_reg_bool.append ( bool( (global_reg>>j)%2 ) )
            for j in range(8):
                global_reg_bool.append ( bool( (dac_reg>>j)%2 ) )

            start_pos = (8*16+16)*chip + 16*8
            self.fe_regs[start_pos : start_pos+16] = global_reg_bool

        #Convert bits to 36 32-bit register words
        for chip in [0,2,4,6]:
            chip_bits_len = 8*(16+2)
            chip_fe_regs0 = self.fe_regs[   chip*chip_bits_len: (chip+1)* chip_bits_len]
            chip_fe_regs1 = self.fe_regs[   (chip+1)*chip_bits_len: (chip+2)* chip_bits_len]
            chip_regs = []
            for onebit in chip_fe_regs0:
                chip_regs.append(onebit)
            for onebit in chip_fe_regs1:
                chip_regs.append(onebit)
            len32 = len(chip_regs)//32
            if (len32 != 9):
                print("ERROR FE register mapping")
            else:
                for i in range(len32):
                    if ( i*32 <= len(chip_regs) ):
                        bits32 = chip_regs[i*32: (i+1)*32]
                        self.fe_REGS[int(chip/2*len32 + i) ] = (sum(v<<j for j, v in enumerate(bits32)))


        #turn off HS data before register writes
        self.femb.write_reg_bits(9 , 0, 0x1, 0 )
        print("HS link turned off")
        time.sleep(2)

        #run the SPI programming
        self.doAsicConfig()

        #turn HS link back on
        print("HS link turned back on")
        time.sleep(2)
        self.femb.write_reg_bits(9 , 0, 0x1, 1 )
        


    def findADCPhase(self, trial=0):

        print("Find ADC phases that sync all ADCs")

        #Write ADC ASIC SPI
        if True :
            print("ADC reconfig")
            self.femb.write_reg( self.REG_RESET,0x4) #reset timestamp
            time.sleep(0.01)
            self.femb.write_reg( self.REG_ASIC_RESET, 1) #reset ASIC SPI
            time.sleep(0.01)
            self.femb.write_reg( self.REG_ASIC_SPIPROG, 1) #configure ASICs
            time.sleep(0.01)
            self.femb.write_reg( self.REG_ASIC_SPIPROG, 1) #configure ASICs
            time.sleep(0.01)
            
        syncSuccess = False
        oldSyncVal = 0xFFFF

        # start with the default values for the configuration
        def_clksel_rt = self.CLKSELECT_val_RT
        def_clksel2_rt = self.CLKSELECT2_val_RT
            
        def_clksel_ct = self.CLKSELECT_val_CT
        def_clksel2_ct = self.CLKSELECT2_val_CT

        #first step will always go +1
        lastStep = 1

        didJump = False
        
        while (syncSuccess == False) :

            # give up after 50 trials
            if trial == 50:
                print("Could not find good clock phase, SYNC STATUS:",hex(syncVal))
                return
            
            #phase control
            if self.isRoomTemp == True:
                print("ADC clock phase:",self.CLKSELECT_val_RT,self.CLKSELECT2_val_RT)
                self.femb.write_reg_bits(self.CLK_SELECT , 0, 0xFF, self.CLKSELECT_val_RT ) #clock select
                self.femb.write_reg_bits(self.CLK_SELECT2 , 0, 0xFF, self.CLKSELECT2_val_RT ) #clock select 2
            else:
                print("Using cryogenic parameters, ADC clock phase:",self.CLKSELECT_val_CT,self.CLKSELECT2_val_CT)
                self.femb.write_reg_bits(self.CLK_SELECT , 0, 0xFF, self.CLKSELECT_val_CT ) #clock select
                self.femb.write_reg_bits(self.CLK_SELECT2 , 0, 0xFF,  self.CLKSELECT2_val_CT ) #clock select 2
               
            # check sync
            regVal = self.femb.read_reg(6)
            if regVal == None:
                print("doAsicConfig: Could not check SYNC status, bad")
                return
            
            syncVal = ((regVal >> 16) & 0xFFFF)
            self.syncStatus = syncVal
            print("SYNC ATTEMPT\t",trial,"\tSYNC VAL " , hex(syncVal) )

            #try again if sync not achieved
            if syncVal != 0x0 :

                if syncVal <= oldSyncVal:

                    # keep going this direction
                    if lastStep == 1:
                        
                        if self.isRoomTemp == True:
                            if self.CLKSELECT_val_RT < 0xFF :
                                self.CLKSELECT_val_RT = self.CLKSELECT_val_RT + 1
                        
                            if self.CLKSELECT2_val_RT < 0xFF :
                                self.CLKSELECT2_val_RT = self.CLKSELECT2_val_RT + 1

                        else:        
                            if self.CLKSELECT_val_CT < 0xFF :
                                self.CLKSELECT_val_CT = self.CLKSELECT_val_CT + 1
                       
                            if self.CLKSELECT2_val_CT < 0xFF :
                                self.CLKSELECT2_val_CT = self.CLKSELECT2_val_CT + 1

                        lastStep = 1
                        
                    else:

                        if self.isRoomTemp == True:
                            if self.CLKSELECT_val_RT < 0xFF :
                                self.CLKSELECT_val_RT = self.CLKSELECT_val_RT - 1
                        
                            if self.CLKSELECT2_val_RT < 0xFF :
                                self.CLKSELECT2_val_RT = self.CLKSELECT2_val_RT - 1

                        else:        
                            if self.CLKSELECT_val_CT < 0xFF :
                                self.CLKSELECT_val_CT = self.CLKSELECT_val_CT - 1
                       
                            if self.CLKSELECT2_val_CT < 0xFF :
                                self.CLKSELECT2_val_CT = self.CLKSELECT2_val_CT - 1

                        lastStep = -1

                    oldSyncVal = syncVal
                        
                else:

                    # already jumped once
                    if didJump == True:
                        print("Could not find good clock phase, SYNC STATUS:",hex(syncVal))
                        return
                    
                    # jump back to start and switch directions
                    if self.isRoomTemp == True:
                        if self.CLKSELECT_val_RT < 0xFF :
                            self.CLKSELECT_val_RT = def_clksel_rt - 1
                        
                        if self.CLKSELECT2_val_RT < 0xFF :
                            self.CLKSELECT2_val_RT = def_clksel2_rt - 1

                    else:        
                        if self.CLKSELECT_val_CT < 0xFF :
                            self.CLKSELECT_val_CT = def_clksel_ct - 1
                            
                        if self.CLKSELECT2_val_CT < 0xFF :
                            self.CLKSELECT2_val_CT = def_clksel2_ct - 1

                    lastStep = -1
                    didJump = True
                    oldSyncVal = 0xFFFF

                syncSuccess = False
                
            else :
                syncSuccess = True

                if self.isRoomTemp == True:
                    print("Found good RT clock phase:",hex(self.CLKSELECT_val_RT),hex(self.CLKSELECT2_val_RT))
                else:
                    print("Found good CT clock phase:",hex(self.CLKSELECT_val_CT),hex(self.CLKSELECT2_val_CT))

            trial = trial + 1
                
        
    def doAsicConfig(self, syncAttempt=0):
        if syncAttempt == 0:
            print("Program ASIC SPI")

        #Write ADC ASIC SPI
        #if syncAttempt == 0:
        if True :
            print("ADC reconfig")
            self.femb.write_reg( self.REG_RESET,0x4) #reset timestamp
            time.sleep(0.01)
            self.femb.write_reg( self.REG_ASIC_RESET, 1) #reset ASIC SPI
            time.sleep(0.01)
            self.femb.write_reg( self.REG_ASIC_SPIPROG, 1) #configure ASICs
            time.sleep(0.01)
            self.femb.write_reg( self.REG_ASIC_SPIPROG, 1) #configure ASICs
            time.sleep(0.01)

        #check the sync
        if self.doReSync == False:
            return

        regVal = self.femb.read_reg(6)
        if regVal == None:
            print("doAsicConfig: Could not check SYNC status, bad")
            return
        syncVal = ((regVal >> 16) & 0xFFFF)
        self.syncStatus = syncVal
        #print("SYNC ATTEMPT\t",syncAttempt,"\tSYNC VAL " , hex(syncVal) )

        #try again if sync not achieved, note recursion
        if syncVal != 0x0 :
            if syncAttempt >= self.maxSyncAttempts :
                print("doAsicConfig: Could not sync ADC ASIC, sync val\t",hex(syncVal))
                return
            else:
                self.doAsicConfig(syncAttempt+1)

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
        self.wib_reg_enable()
        wib7val = self.femb.read_reg(7)        
        wib7val = wib7val | 0x80000000
        self.femb.write_reg(7, wib7val)
        
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
        time.sleep(0.1)

    def setFpgaPulser(self,enable,dac):
        enableVal = int(enable)
        if (enableVal < 0 ) or (enableVal > 1 ) :
            print( "femb_config_femb : setFpgaPulser - invalid enable value")
            return
        dacVal = int(dac)
        if ( dacVal < 0 ) or ( dacVal > 0x3F ) :
            print( "femb_config_femb : setFpgaPulser - invalid dac value")
            return

        self.femb.write_reg_bits( self.REG_FPGA_TP_EN, 0,0x3,enableVal) #test pulse enable
        self.femb.write_reg_bits( self.REG_FPGA_TP_EN, 8,0x1,enableVal) #test pulse enable
        self.femb.write_reg_bits( self.REG_TP , 0, 0x3F, dacVal ) #TP Amplitude
        self.femb.write_reg_bits( self.REG_TP , 8, 0xFF, 219 ) #DLY
        self.femb.write_reg_bits( self.REG_TP , 16, 0xFFFF, 497 ) #FREQ

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

    def setInternalPulser(self,enable,dac):
        enableVal = int(enable)
        if (enableVal < 0 ) or (enableVal > 1 ) :
            print( "femb_config_femb : setInternalPulser - invalid enable value")
            return
        dacVal = int(dac)
        if ( dacVal < 0 ) or ( dacVal > 0x3F ) :
            print( "femb_config_femb : setInternalPulser - invalid dac value")
            return

        self.femb.write_reg_bits( self.REG_DAC_SELECT, 8,0x1,0) #test pulse enable
        self.femb.write_reg_bits( self.REG_TP , 0, 0x3F, 0 ) #TP Amplitude
        self.femb.write_reg_bits( self.REG_TP , 8, 0xFF, 219 ) #DLY
        self.femb.write_reg_bits( self.REG_TP , 16, 0xFFFF, 497 ) #FREQ

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

        if enableVal == 1:
            self.femb.write_reg_bits( self.REG_ASIC_TP_EN , 0, 0x3, 0x2 ) #NOTE, also disabling FPGA pulser here
        else:
            self.femb.write_reg_bits( self.REG_ASIC_TP_EN , 0, 0x3, 0x0 )

    def checkFirmwareVersion(self):
        #set UDP ports to WIB
        self.wib_reg_enable()

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
        if wibVerReg != 0x116 :
            print("Invalid WIB firmware version detected " + str(wibVerReg) + ", this configuration requires version 0x116")
            return False
        if fembVerReg != 0x405 :
            print("Invalid FEMB firmware version detected " + str(fembVerReg) + ", this configuration requires version 0x405")
            return False
        
        print( "WIB Firmware Version : " + str(hex(wibVerReg)) )
        print( "FEMB Firmware Version : " + str(hex(fembVerReg)) )

        #good firmware id
        return True

    def readCurrent(self):

        self.femb.UDP_PORT_WREG = 32000 #WIB PORTS
        self.femb.UDP_PORT_RREG = 32001
        self.femb.UDP_PORT_RREGRESP = 32002

        for j in range(0,100):
            self.femb.write_reg(5,0)
            self.femb.write_reg(5,0x10000)
            self.femb.write_reg(5,0)
            time.sleep(0.01)

        results = []
        for pwrSel in range(1,25):
            self.femb.write_reg(5,pwrSel)
            time.sleep(0.1)
            regVal = self.femb.read_reg(6)
            if regVal == None:
                 results.append(0)
                 continue
                 #return None
            val = regVal & 0xFFFFFFFF
            results.append(val)

        self.selectFemb(0)
        return results
    
"""
    def ext_clk_config_femb(self):
        #EXTERNAL CLOCK VARIABLES
        ####################external clokc timing
        clk_period = 5 #ns
        self.clk_dis = 0 #0 --> enable, 1 disable
        self.d14_rst_oft  = 0   // clk_period   
        self.d14_rst_wdt  = (45  // clk_period )    
        self.d14_rst_inv  = 1  
        self.d14_read_oft = 480 // clk_period    
        self.d14_read_wdt = 20  // clk_period    
        self.d14_read_inv = 1 
        self.d14_idxm_oft = 230 // clk_period    
        self.d14_idxm_wdt = 270 // clk_period    
        self.d14_idxm_inv = 0 
        self.d14_idxl_oft = 480 // clk_period    
        self.d14_idxl_wdt = 20  // clk_period    
        self.d14_idxl_inv = 0 
        self.d14_idl0_oft = 50  // clk_period    
        self.d14_idl0_wdt = (190 // clk_period ) -1   
        self.d14_idl1_oft = 480 // clk_period
        self.d14_idl1_wdt = 20  // clk_period    
        self.d14_idl_inv  = 0      

        self.d58_rst_oft  = 0   // clk_period 
        self.d58_rst_wdt  = (45  // clk_period ) 
        self.d58_rst_inv  = 1  
        self.d58_read_oft = 480 // clk_period 
        self.d58_read_wdt = 20  // clk_period 
        self.d58_read_inv = 1 
        self.d58_idxm_oft = 230 // clk_period 
        self.d58_idxm_wdt = 270 // clk_period 
        self.d58_idxm_inv = 0 
        self.d58_idxl_oft = 480 // clk_period 
        self.d58_idxl_wdt = 20  // clk_period 
        self.d58_idxl_inv = 0 
        self.d58_idl0_oft = 50  // clk_period 
        self.d58_idl0_wdt = (190 // clk_period ) -1
        self.d58_idl1_oft = 480 // clk_period
        self.d58_idl1_wdt = 20  // clk_period 
        self.d58_idl_inv  = 0       
        ####################external clock phase for V323 firmware
        self.d14_read_step = 11
        self.d14_read_ud   = 0
        self.d14_idxm_step = 9
        self.d14_idxm_ud   = 0
        self.d14_idxl_step = 7
        self.d14_idxl_ud   = 0
        self.d14_idl0_step = 12
        self.d14_idl0_ud   = 0
        self.d14_idl1_step = 10
        self.d14_idl1_ud   = 0
        self.d14_phase_en  = 1

        self.d58_read_step = 0
        self.d58_read_ud   = 0
        self.d58_idxm_step = 5
        self.d58_idxm_ud   = 0
        self.d58_idxl_step = 4
        self.d58_idxl_ud   = 1
        self.d58_idl0_step = 3
        self.d58_idl0_ud   = 0
        self.d58_idl1_step = 4
        self.d58_idl1_ud   = 0
        self.d58_phase_en  = 1

        #END EXTERNAL CLOCK VARIABLES

        #config timing
        d14_inv = (self.d14_rst_inv<<0) + (self.d14_read_inv<<1)+ (self.d14_idxm_inv<<2)+ (self.d14_idxl_inv<<3)+ (self.d14_idl_inv<<4)
        d58_inv = (self.d58_rst_inv<<0) + (self.d58_read_inv<<1)+ (self.d58_idxm_inv<<2)+ (self.d58_idxl_inv<<3)+ (self.d58_idl_inv<<4)
        d_inv = d58_inv + ( d14_inv<<5)

        addr_data = self.clk_dis + (d_inv << 16)
        #self.ext_clk_reg_wr_femb( femb_addr, 21, addr_data)
        self.femb.write_reg( 21, addr_data)

        addr_data = self.d58_rst_oft + (self.d14_rst_oft << 16)
        #self.ext_clk_reg_wr_femb( femb_addr, 22, addr_data)
        self.femb.write_reg( 22, addr_data)

        addr_data = self.d58_rst_wdt + (self.d14_rst_wdt << 16)
        #self.ext_clk_reg_wr_femb( femb_addr, 23, addr_data)
        self.femb.write_reg( 23, addr_data)

        addr_data = self.d58_read_oft + (self.d14_read_oft << 16)
        #self.ext_clk_reg_wr_femb( femb_addr, 24, addr_data)
        self.femb.write_reg( 24, addr_data)

        addr_data = self.d58_read_wdt + (self.d14_read_wdt << 16)
        #self.ext_clk_reg_wr_femb( femb_addr, 25, addr_data)
        self.femb.write_reg( 25, addr_data)

        addr_data = self.d58_idxm_oft + (self.d14_idxm_oft << 16)
        #self.ext_clk_reg_wr_femb( femb_addr, 26, addr_data)
        self.femb.write_reg( 26, addr_data)

        addr_data = self.d58_idxm_wdt + (self.d14_idxm_wdt << 16)
        #self.ext_clk_reg_wr_femb( femb_addr, 27, addr_data)
        self.femb.write_reg( 27, addr_data)

        addr_data = self.d58_idxl_oft + (self.d14_idxl_oft << 16)
        #self.ext_clk_reg_wr_femb( femb_addr, 28, addr_data)
        self.femb.write_reg( 28, addr_data)

        addr_data = self.d58_idxl_wdt + (self.d14_idxl_wdt << 16)
        #self.ext_clk_reg_wr_femb( femb_addr, 29, addr_data)
        self.femb.write_reg( 29, addr_data)

        addr_data = self.d58_idl0_oft + (self.d14_idl0_oft << 16)
        #self.ext_clk_reg_wr_femb( femb_addr, 30, addr_data)
        self.femb.write_reg( 30, addr_data)

        addr_data = self.d58_idl0_wdt + (self.d14_idl0_wdt << 16)
        #self.ext_clk_reg_wr_femb( femb_addr, 31, addr_data)
        self.femb.write_reg( 31, addr_data)

        addr_data = self.d58_idl1_oft + (self.d14_idl1_oft << 16)
        #self.ext_clk_reg_wr_femb( femb_addr, 32, addr_data)
        self.femb.write_reg( 32, addr_data)

        addr_data = self.d58_idl1_wdt + (self.d14_idl1_wdt << 16)
        #self.ext_clk_reg_wr_femb( femb_addr, 33, addr_data)
        self.femb.write_reg( 33, addr_data)

        #config phase 
        for i in range(4):
            addr_data = self.d14_read_step + (self.d14_idxm_step <<16)
            #self.ext_clk_reg_wr_femb( femb_addr, 35, addr_data)
            self.femb.write_reg( 35, addr_data)

            addr_data = self.d14_idxl_step + (self.d14_idl0_step <<16)
            #self.ext_clk_reg_wr_femb( femb_addr, 36, addr_data)
            self.femb.write_reg( 36, addr_data)
             
            self.d14_phase_en = self.d14_phase_en ^ 1
            d14_ud = self.d14_read_ud + (self.d14_idxm_ud<<1) + (self.d14_idxl_ud<<2)+ (self.d14_idl0_ud<<3)+ (self.d14_idl1_ud<<4) + (self.d14_phase_en <<15)
            addr_data = self.d14_idl1_step + (d14_ud<<16)
            #self.ext_clk_reg_wr_femb( femb_addr, 37, addr_data)
            self.femb.write_reg( 37, addr_data)

            addr_data = self.d58_read_step + (self.d58_idxm_step <<16)
            #self.ext_clk_reg_wr_femb( femb_addr, 38, addr_data)
            self.femb.write_reg( 38, addr_data)

            addr_data = self.d58_idxl_step + (self.d58_idl0_step <<16)
            #self.ext_clk_reg_wr_femb( femb_addr, 39, addr_data)
            self.femb.write_reg( 39, addr_data)
            
            self.d58_phase_en = self.d58_phase_en ^ 1
            d58_ud = self.d58_read_ud + (self.d58_idxm_ud<<1) + (self.d58_idxl_ud<<2)+ (self.d58_idl0_ud<<3)+ (self.d58_idl1_ud<<4) + (self.d58_phase_en <<15)
            addr_data = self.d58_idl1_step + (d58_ud <<16)
            #self.ext_clk_reg_wr_femb( femb_addr, 40, addr_data)
            self.femb.write_reg( 40, addr_data)
"""
