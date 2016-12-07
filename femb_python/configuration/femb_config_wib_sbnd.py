import sys 
import string
import time
from femb_python.femb_udp import FEMB_UDP

class FEASIC_CH_CONFIG:
    def __init__(self, num, regNum, regPos):
        numVal = int(num)
        regNumVal = int(regNum)
        regPosVal = int(regPos)
        
        self.chan_num = numVal
        self.STS = 0
        self.NC = 0
        self.SG = 0
        self.ST = 0
        self.SDC = 0
        self.SBF = 0
        self.regNum = regNumVal
        self.regPos = regPosVal
        self.regval = 0

    #sts=test input, snc = baseline, sg = gain, st = shaping time, sdc = coupling, sbf = buffer amplifier
    def set_fechn_reg(self, sts=0, snc=0, sg=0, st=0, sdc=0, sdf=0 ):
        testVal = int(sts)
        if (testVal < 0 ) or (testVal > 1):
                return
        baseVal = int(snc)
        if (baseVal < 0 ) or (baseVal > 1):
                return
        gainVal = int(sg)
        if (gainVal < 0 ) or (gainVal > 3):
                return
        shapeVal = int(st)
        if (shapeVal < 0 ) or (shapeVal > 3):
                return
        acdcVal = int(sdc)
        if (acdcVal < 0 ) or (acdcVal > 1):
                return
        bufVal = int(sbf)
        if (bufVal < 0 ) or (bufVal > 1):
                return

        gainArray = [0,2,1,3]
        shapeArray = [2,0,3,1] #I don't know why
        baseVal = 1 - baseVal #want 0 = 200mV, 1 = 900mV

        self.regval = ((testVal & 0x01)<<7) + ((baseVal & 0x01)<<6) + ((gainArray[gainVal] & 0x03)<<4) +\
                  ((shapeArray[shapeVal] & 0x03)<<2)  + ((acdcVal & 0x01)<<1) + ((bufVal & 0x01)<<0)

class FEMB_CONFIG:
    def resetBoard(self):
        print("Reset")
    def initBoard(self):
        print("Init")

    def selectChannel(self,asic,chan):
        print("Select channel")
        asicVal = int(asic)
        if (asicVal < 0 ) or (asicVal > 7):
                return

        #set UDP ports to WIB
        self.femb.UDP_PORT_WREG = 32000
        self.femb.UDP_PORT_RREG = 32001
        self.femb.UDP_PORT_RREGRESP = 32002

        #select ASIC
        print("Selecting ASIC " + str(asicVal) )
        self.femb.write_reg_bits(self.REG_SEL_ASIC , self.REG_SEL_ASIC_LSB, 0xF, asicVal )

        #set UDP ports back to normal
        self.femb.UDP_PORT_WREG = 32016
        self.femb.UDP_PORT_RREG = 32017
        self.femb.UDP_PORT_RREGRESP = 32018

    
    def configFeAsic(self,gain,shape,base):
        gainVal = int(gain)
        if (gainVal < 0 ) or (gainVal > 3):
                return
        shapeVal = int(shape)
        if (shapeVal < 0 ) or (shapeVal > 3):
                return
        baseVal = int(base)
        if (baseVal < 0 ) or (baseVal > 1):
                return

        #get ASIC channel config register SPI values        
        chReg = 0x0
        gainArray = [0,2,1,3]
        shapeArray = [2,0,3,1] #I don't know why
        chReg = (gainArray[gainVal] << 4 ) + (shapeArray[shapeVal] << 2)

        if (baseVal == 0) :
                chReg = chReg + 0x40

        #enable test capacitor here
        #chReg = chReg + 0x80 #enabled
        chReg = chReg + 0x0 #disabled

        #need better organization of SPI, just store in words for now
        word1 = chReg + (chReg << 8) + (chReg << 16) + (chReg << 24)
        #word2 = (chReg << 8) + (chReg << 24)
        #word3 = chReg + (chReg << 16)
        word2 = 0x02010201
        word3 = 0x02010201

        #turn off HS data before register writes
        self.femb.write_reg_bits(9 , 0, 0x1, 0 )
        print("HS link turned off")
        time.sleep(2)

        print("Config FE ASIC SPI")
        for regNum in range(self.REG_FESPI_BASE,self.REG_FESPI_BASE+7+1,1):
                self.femb.write_reg( regNum, word1)
        self.femb.write_reg( self.REG_FESPI_BASE+8, word2 )
        for regNum in range(self.REG_FESPI_BASE+9,self.REG_FESPI_BASE+16+1,1):
                self.femb.write_reg( regNum, word1)
        self.femb.write_reg( self.REG_FESPI_BASE+17, word3 )
        for regNum in range(self.REG_FESPI_BASE+18,self.REG_FESPI_BASE+25+1,1):
                self.femb.write_reg( regNum, word1)
        self.femb.write_reg( self.REG_FESPI_BASE+26, word2 )
        for regNum in range(self.REG_FESPI_BASE+27,self.REG_FESPI_BASE+34+1,1):
                self.femb.write_reg( regNum, word1)
        self.femb.write_reg( self.REG_FESPI_BASE+35, word3 )

        self.doFeAsicConfig()

        #turn HS link back on
        print("HS link turned back on")
        time.sleep(2)
        self.femb.write_reg_bits(9 , 0, 0x1, 1 )

    def doFeAsicConfig(self):
        print("Check FE ASIC SPI")
        for regNum in range(self.REG_FESPI_BASE,self.REG_FESPI_BASE+35,1):
            val = self.femb.read_reg( regNum)
            print( str(hex(val)) )

        #Write FE ASIC SPI
        print("Program FE ASIC SPI")
        self.femb.write_reg( self.REG_ASIC_SPIPROG, 2)
        time.sleep(0.1)
        self.femb.write_reg( self.REG_ASIC_SPIPROG, 2)
        time.sleep(0.1)

        print("Check FE ASIC SPI Readback")
        for regNum in range(self.REG_FESPI_RDBACK_BASE,self.REG_FESPI_RDBACK_BASE+35,1):
            val = self.femb.read_reg( regNum)
            print( str(hex(val)) )

    def doAdcAsicConfig(self):
        print("Check ADC ASIC SPI")
        for regNum in range(self.REG_ADCSPI_BASE,self.REG_ADCSPI_BASE+35,1):
            val = self.femb.read_reg( regNum)
            print( str(hex(val)) )

        #Write ADC ASIC SPI
        print("Program ADC ASIC SPI")
        self.femb.write_reg( self.REG_ASIC_SPIPROG, 1)
        time.sleep(0.1)
        self.femb.write_reg( self.REG_ASIC_SPIPROG, 1)
        time.sleep(0.1)

        print("Check ADC ASIC SPI Readback")
        for regNum in range(self.REG_ADCSPI_RDBACK_BASE,self.REG_ADCSPI_RDBACK_BASE+35,1):
            val = self.femb.read_reg( regNum)
            print( str(hex(val)) )

    def setInternalPulser(self,pulserEnable,pulseHeight):
        print("Set Pulser")
    def syncADC(self):
        print("Sync")

    #__INIT__#
    def __init__(self):
        #declare board specific registers
        self.FEMB_VER = "WIB_SBND"
        self.REG_RESET = 0

        self.REG_ASIC_RESET = 1
        self.REG_ASIC_SPIPROG = 2

        self.REG_SEL_ASIC = 7
        self.REG_SEL_ASIC_LSB = 8

        self.REG_FESPI_BASE = 592
        self.REG_ADCSPI_BASE = 512
        self.REG_FESPI_RDBACK_BASE = 632
        self.REG_ADCSPI_RDBACK_BASE = 552

        #initialize FEMB UDP object
        self.femb = FEMB_UDP()
        self.femb.UDP_PORT_WREG = 32016
        self.femb.UDP_PORT_RREG = 32017
        self.femb.UDP_PORT_RREGRESP = 32018

        #initialiuze ASIC ch objects, specify SPI register number (firmware specific!!!)
        self.feasic_ch_list = []
        for ch in range(0,128,1):
          chVal = int(ch)
          if (chVal < 0 ) or (chVal > 127 ):
            continue

          #seriously messy mapping between ch # and register bits
          regGrp = int( ( chVal % 64 ) / 16 )
          regGrpLine =  7 - int( ( chVal % 16 ) / 2 )
          regGrpBase = [27,18,9,0]

          regNum = self.REG_FESPI_BASE + regGrpBase[ regGrp ] + regGrpLine
          regPos = (1 - chVal % 2 )*8 + int(chVal / 64 )*16

          feasic_ch = FEASIC_CH_CONFIG(ch, regNum, regPos)
          self.feasic_ch_list.append(feasic_ch)
