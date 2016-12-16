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
        bufVal = int(sdf)
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
        
        #WIB initialization

        #set UDP ports to WIB registers
        self.femb.UDP_PORT_WREG = 32000
        self.femb.UDP_PORT_RREG = 32001
        self.femb.UDP_PORT_RREGRESP = 32002

        #register 2, LED
        self.femb.write_reg_bits(2 , 0, 0xFF, 0 )

        #clock select (firmware version dependent)
        self.femb.write_reg_bits(4 , 2, 0x3, 2 )

        #FEMB0 power enable
        self.femb.write_reg_bits(8 , 0, 0x1, 1 ) #3.6V
        self.femb.write_reg_bits(8 , 1, 0x1, 1 ) #2.8V
        self.femb.write_reg_bits(8 , 2, 0x1, 1 ) #2.5V
        self.femb.write_reg_bits(8 , 3, 0x1, 1 ) #1.5V
        self.femb.write_reg_bits(8 , 16, 0x1, 1 ) #BIAS enable

        #FEMB0 initialization
        self.selectFemb(0)

        #phase control
        self.femb.write_reg_bits(6 , 0, 0xFF, 0xAF )

        self.femb.write_reg_bits(9 , 0, 0x1, 1 ) #Enable streaming
        self.femb.write_reg_bits(9 , 3, 0x1, 1 ) #Enable ADC data

        #Set FE ASIC SPI configuration registers
        self.configFeAsic(0,0,0)

        #Set ADC SPI configuration registers
        self.femb.write_reg_bits(512, 0, 0xFFFFFFFF, 0xc0c0c0c)
        self.femb.write_reg_bits(513, 0, 0xFFFFFFFF, 0xc0c0c0c)
        self.femb.write_reg_bits(514, 0, 0xFFFFFFFF, 0xc0c0c0c)
        self.femb.write_reg_bits(515, 0, 0xFFFFFFFF, 0xc0c0c0c)
        self.femb.write_reg_bits(516, 0, 0xFFFFFFFF, 0xc0c0c0c)
        self.femb.write_reg_bits(517, 0, 0xFFFFFFFF, 0xc0c0c0c)
        self.femb.write_reg_bits(518, 0, 0xFFFFFFFF, 0xc0c0c0c)
        self.femb.write_reg_bits(519, 0, 0xFFFFFFFF, 0xc0c0c0c)
        self.femb.write_reg_bits(520, 0, 0xFFFFFFFF, 0x19351935)
        self.femb.write_reg_bits(521, 0, 0xFFFFFFFF, 0x18181818)
        self.femb.write_reg_bits(522, 0, 0xFFFFFFFF, 0x18181818)
        self.femb.write_reg_bits(523, 0, 0xFFFFFFFF, 0x18181818)
        self.femb.write_reg_bits(524, 0, 0xFFFFFFFF, 0x18181818)
        self.femb.write_reg_bits(525, 0, 0xFFFFFFFF, 0x18181818)
        self.femb.write_reg_bits(526, 0, 0xFFFFFFFF, 0x18181818)
        self.femb.write_reg_bits(527, 0, 0xFFFFFFFF, 0x18181818)
        self.femb.write_reg_bits(528, 0, 0xFFFFFFFF, 0x6a186a18)
        self.femb.write_reg_bits(529, 0, 0xFFFFFFFF, 0x30323032)
        self.femb.write_reg_bits(530, 0, 0xFFFFFFFF, 0x30303030)
        self.femb.write_reg_bits(531, 0, 0xFFFFFFFF, 0x30303030)
        self.femb.write_reg_bits(532, 0, 0xFFFFFFFF, 0x30303030)
        self.femb.write_reg_bits(533, 0, 0xFFFFFFFF, 0x30303030)
        self.femb.write_reg_bits(534, 0, 0xFFFFFFFF, 0x30303030)
        self.femb.write_reg_bits(535, 0, 0xFFFFFFFF, 0x30303030)
        self.femb.write_reg_bits(536, 0, 0xFFFFFFFF, 0x30303030)
        self.femb.write_reg_bits(537, 0, 0xFFFFFFFF, 0x64d464d4)
        self.femb.write_reg_bits(538, 0, 0xFFFFFFFF, 0x60606060)
        self.femb.write_reg_bits(539, 0, 0xFFFFFFFF, 0x60606060)
        self.femb.write_reg_bits(540, 0, 0xFFFFFFFF, 0x60606060)
        self.femb.write_reg_bits(541, 0, 0xFFFFFFFF, 0x60606060)
        self.femb.write_reg_bits(542, 0, 0xFFFFFFFF, 0x60606060)
        self.femb.write_reg_bits(543, 0, 0xFFFFFFFF, 0x60606060)
        self.femb.write_reg_bits(544, 0, 0xFFFFFFFF, 0x60606060)
        self.femb.write_reg_bits(545, 0, 0xFFFFFFFF, 0xa860a860)
        self.femb.write_reg_bits(546, 0, 0xFFFFFFFF, 0x90009)

        self.doFeAsicConfig()
        self.doAdcAsicConfig()

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
        self.selectFemb(self.fembNum)
    
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

    def selectFemb(self, fembIn):
        fembVal = int( fembIn)
        if (fembVal < 0) or (fembVal > 3 ):
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

    def initSI5338(self):
        #set UDP ports to WIB
        self.femb.UDP_PORT_WREG = 32000
        self.femb.UDP_PORT_RREG = 32001
        self.femb.UDP_PORT_RREGRESP = 32002
       

        for reg in range(0,256,1):
            regVal = self.read_reg_SI5338(reg)
            print( "reg " + str(reg) + "\tval " + str(hex(int(regVal))) )

        self.selectFemb(0)

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

        self.fembNum = 0

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
