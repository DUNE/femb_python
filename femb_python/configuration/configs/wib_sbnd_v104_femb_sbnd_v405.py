#!/usr/bin/env python33

"""
Configuration for SBND FEMB + SBND WIB Setup - for LArIAT VST running
WIB firmware v104
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
import pickle
from femb_python.femb_udp import FEMB_UDP
from femb_python.configuration.config_base import FEMB_CONFIG_BASE
from femb_python.configuration.cppfilerunner import CPP_FILE_RUNNER

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
        self.wibNum = 0
        self.useExtAdcClock = True
        self.isRoomTemp = False
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
        self.useLArIATmap = True

        #initialize FEMB UDP object
        self.femb = FEMB_UDP()
        self.femb.UDP_IP = "131.225.150.203"
        self.femb.UDP_PORT_WREG = 32000 #WIB PORTS
        self.femb.UDP_PORT_RREG = 32001
        self.femb.UDP_PORT_RREGRESP = 32002
        self.femb.doReadBack = False #WIB register interface is unreliable

        #ASIC config variables
        self.feasicLeakage = 0 #0 = 500pA, 1 = 100pA
        self.feasicLeakagex10 = 0 #0 = pA, 1 = pA*10
        self.feasicAcdc = 0 #AC = 0, DC = 1
        self.feasicBaseline = 1 #0 = 200mV, 1 = 900mV        
        self.feasicEnableTestInput = 0 #0 = disabled, 1 = enabled
        self.feasicGain = 2 #4.7,7.8,14,25
        self.feasicShape = 1 #0.5,1,2,3
        self.feasicBuf = 0 #0 = OFF, 1 = ON

        #Read in LArIAT mapping if desired

        if self.useLArIATmap:
            self.cppfr = CPP_FILE_RUNNER()            
            with open(self.cppfr.filename('configuration/configs/LArIAT_pin_mapping.map'), "rb") as fp:
                self.lariatMap = pickle.load(fp)
                
            #APA Mapping
            va = self.lariatMap
            va_femb = []
            for vb in va:
                if int(vb[9]) in (0,1,2,3,4) :
                    va_femb.append(vb)
            apa_femb_loc = []
            for chn in range(128):
                for vb in va_femb:
                    if int(vb[8]) == chn:
                        if (vb[1].find("Co")) >= 0 :#collection wire
                            chninfo = [ "X" + vb[0], vb[8], int(vb[6]), int(vb[7]), int(vb[9]), int(vb[10])]
                        elif (vb[1].find("In")) >= 0 : #induction wire
                            chninfo = [ "U" + vb[0], vb[8], int(vb[6]), int(vb[7]), int(vb[9]), int(vb[10])]
                        apa_femb_loc.append(chninfo)
            for chn in range(128):
                fl_w = True
                fl_i = 0
                for tmp in apa_femb_loc:
                    if int(tmp[1]) == chn:
                        fl_w = False
                        break
                if (fl_w):
                    chninfo = [ "V" + format(fl_i, "03d"), format(chn, "03d"), chn//16 , format(chn%15, "02d"), apa_femb_loc[0][4], apa_femb_loc[0][5]]
                    apa_femb_loc.append(chninfo)
                    fl_i = fl_i + 1

            self.All_sort = []
            self.X_sort = []
            self.V_sort = []
            self.U_sort = []
            for i in range(128):
                for chn in apa_femb_loc:
                    if int(chn[1][0:3]) == i :
                        self.All_sort.append(chn)
    
                    for chn in apa_femb_loc:
                        if chn[0][0] == "X" and int(chn[0][1:3]) == i :
                            self.X_sort.append(chn)
                    for chn in apa_femb_loc:
                        if chn[0][0] == "V" and int(chn[0][1:3]) == i :
                            self.V_sort.append(chn)
                    for chn in apa_femb_loc:
                        if chn[0][0] == "U" and int(chn[0][1:3]) == i :
                            self.U_sort.append(chn)

            self.WireDict = {}
            for line in self.All_sort:
                key = "wib{:d}_femb{:d}_chip{:d}_chan{:02d}".format(line[5],line[4],line[2],line[3])
                self.WireDict[key] = line[0]
                
    def printParameters(self):
        print("FEMB #             \t",self.fembNum)
        print("Room temperature   \t",self.isRoomTemp)
        print("Do resync          \t",self.doReSync)
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
        for femb in range(1,4,1):
            self.selectFemb(femb)
            self.initFemb()
        
    def initWib(self):
        #WIB initialization

        self.wib_switch()
        
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
        fembVal = self.fembNum - 4*(self.wibNum)
            
        if (fembVal < 0) or (fembVal >= self.NFEMBS ):
            return

        print("Initialize FEMB",fembVal)

        #FEMB power enable on WIB
        self.powerOnFemb(fembVal)
        time.sleep(4)

        #Make sure register interface is for correct FEMB
        self.selectFemb(fembVal)

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

        #ADC Setup
        self.set_cots_shift()
        
        #Set ASIC SPI configuration registers
        self.configFeAsic()

        #check ASIC SPI
        self.checkFembSpi()
        print("SPI STATUS","\t",self.spiStatus)

        # write to WIB
        self.wib_reg_enable()

        self.femb.write_reg(20,3)
        self.femb.write_reg(20,3)
        time.sleep(0.001)
        self.femb.write_reg(20,0)
        self.femb.write_reg(20,0)
        time.sleep(0.001)

        # start streaming data from ASIC 0 in initialization
        self.femb.write_reg(7, 0x80000000)
        self.femb.write_reg(7, 0x80000000)
        femb_asic = 0 & 0x0F
        wib_asic = (((fembVal << 16)&0x000F0000) + ((femb_asic << 8) &0xFF00))
        self.femb.write_reg(7, wib_asic | 0x80000000)
        self.femb.write_reg(7, wib_asic | 0x80000000)
        self.femb.write_reg(7, wib_asic)
        self.femb.write_reg(7, wib_asic)

        # return to FEMB control
        self.selectFemb(fembVal)

        #Enable Streaming
        self.femb.write_reg(9,9)
        self.femb.write_reg(9,9)
        time.sleep(0.1)

        #Print some happy messages for shifters
        print("Finished initializing ASICs for WIB{:d} FEMB{:d}".format(self.wibNum,fembVal)) 

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
                        if self.fe_REGS[i] != readvals[i] :
                            print(hex(self.fe_REGS[i]),"\t",hex(readvals[i]))
                            print("SPI readback failed.")
                            self.spiStatus = 1
                if self.spiStatus == 1:            
                    return
        self.femb.write_reg(9, 9)
        self.femb.write_reg(9, 9)
        time.sleep(0.1)
        

    def checkSync(self):
        print("Check ASIC SYNC")
        regVal = self.femb.read_reg(6)
        if regVal == None:
            print("doAsicConfigcheckFembSpi: Could not check SYNC status, bad")
            return
        syncVal = ((regVal >> 16) & 0xFFFF)
        self.syncStatus = syncVal

    #Setup talking to WIB
    def wib_switch(self):
        #Set IP addresses based in wib number:
        For SBND-LArIAT
        iplist = ["131.225.150.203","131.225.150.206"]
        #For BNL testing
        #iplist = ["192.168.121.50"]
        self.femb.UDP_IP = iplist[self.wibNum]
    
    def wib_reg_enable(self):
        
        self.femb.UDP_PORT_WREG = 32000
        self.femb.UDP_PORT_RREG = 32001
        self.femb.UDP_PORT_RREGRESP = 32002
        self.femb.REG_SLEEP = 0.001

        #wib7val = self.femb.read_reg(7)
        #time.sleep(0.001)
        #wib7val = self.femb.read_reg(7)        
        #wib7val = wib7val & 0x00000000
        #self.femb.write_reg(7, wib7val)

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

        #print("asicVal",asicVal)
        fembVal = self.fembNum
        #print("fembVal",fembVal)
        
        #set UDP ports to WIB
        self.wib_reg_enable()

        self.femb.write_reg(7, 0x80000000)
        self.femb.write_reg(7, 0x80000000)
        femb_asic = asicVal & 0x0F
        wib_asic = (((fembVal << 16)&0x000F0000) + ((femb_asic << 8) &0xFF00))
        self.femb.write_reg(7, wib_asic | 0x80000000)
        self.femb.write_reg(7, wib_asic | 0x80000000)
        self.femb.write_reg(7, wib_asic)
        self.femb.write_reg(7, wib_asic)
        
        #select ASIC
        #print("Selecting ASIC " + str(asicVal) )
        #self.femb.write_reg_bits(self.REG_SEL_ASIC , self.REG_SEL_ASIC_LSB, 0xF, asicVal )

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
        
        for chip in range(self.NASICS):
            for chn in range(self.NASICCH):
                if self.useLArIATmap:
                    key = "wib{:d}_femb{:d}_chip{:d}_chan{:02d}".format(self.wibNum,self.fembNum,chip+1,chn) #Note map has chips 1-8, not 0-7
                    if self.WireDict[key][0] == "X":
                        snc = 0 #set baseline for collection
                    elif self.WireDict[key][0] == "U":
                        snc = 1 #set baseline for induction

                chn_reg = ((sts&0x01)<<7) + ((snc&0x01)<<6) + ((sg&0x03)<<4) + ((st&0x03)<<2)  + ((smn&0x01)<<1) + ((sdf&0x01)<<0)
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
        
    def doAsicConfig(self):
        print("Program ASIC SPI")

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

        #Enable streaming
        self.femb.write_reg(9, 9)
        self.femb.write_reg(9, 9)
        time.sleep(0.1)

    def selectFemb(self, fembIn):
        fembVal = int( fembIn)
        if (fembVal < 0) or (fembVal > self.NFEMBS ):
            print("Invalid FEMB # requested")
            return
        self.fembNum = fembVal
        #print("selecting FEMB",fembVal)

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

        #self.femb.write_reg(0, femb_asic)
        self.femb.write_reg(self.REG_HS,1)
        

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
        if wibVerReg != 0x104 :
            print("Invalid WIB firmware version detected " + str(wibVerReg) + ", this configuration requires version 0x104")
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

        
        
        
