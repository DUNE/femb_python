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

class FEASIC_CH_CONFIG(object):
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

class FEMB_CONFIG(object):

    def resetBoard(self):
        print("Reset")

    def initBoard(self):
        self.initWib()
        for femb in range(0,4,1):
            self.initFemb(femb)
        
    def initWib(self):

        #WIB initialization

        #set UDP ports to WIB registers
        self.femb.UDP_PORT_WREG = 32000
        self.femb.UDP_PORT_RREG = 32001
        self.femb.UDP_PORT_RREGRESP = 32002

        #register 2, LED
        self.femb.write_reg_bits(2 , 0, 0xFF, 0 )

        #clock select (firmware version dependent)
        #self.femb.write_reg_bits(4 , 2, 0x3, 2 )

        #initialize clock
        self.initSI5338()

        #return register interface to FEMB
        self.selectFemb(self.fembNum)

    def initFemb(self,femb):
        fembVal = int(femb)
        if (fembVal < 0) or (fembVal > 3 ):
            return

        #check if FEMB register interface is working
        self.selectFemb(fembVal)
        print("Checking register interface")
        regVal = self.femb.read_reg(6)
        if (regVal == None) or (regVal == -1):
            print("Error - FEMB register interface is not working.")
            print(" Will not initialize FEMB.")       
            return

        #FEMB power enable on WIB
        self.powerOnFemb(fembVal)

        #Make sure register interface is for correct FEMB
        self.selectFemb(fembVal)

        #turn off pulser
        self.femb.write_reg_bits( 16, 0,0x1,0) #test pulse enable
        self.femb.write_reg_bits( 16, 1,0x1,0) #test pulse enable
        self.femb.write_reg_bits( 16, 8,0x1,0) #test pulse enable
        self.femb.write_reg_bits( 5, 0,0x1F,0x00) #test pulse amplitude
        self.femb.write_reg_bits( 5, 16,0xFFFF,0x100) #test pulse frequency
        self.femb.write_reg_bits( 5, 8,0xFF,0x00) #test pulse delay

        #phase control
        self.femb.write_reg_bits(6 , 0, 0xFF, 0xAF ) #clock select
        self.femb.write_reg_bits(15 , 0, 0xFF, 0xAF ) #clock select 2

        self.femb.write_reg_bits(4 , 0, 0xFFFFFFFF, 0x00000000 )
        self.femb.write_reg_bits(14 , 0, 0xFFFFFFFF, 0x00000000 )

        #enable streaming
        self.femb.write_reg_bits(9 , 0, 0x1, 1 ) #Enable streaming
        self.femb.write_reg_bits(9 , 3, 0x1, 1 ) #Enable ADC data

        #Set FE ASIC SPI configuration registers
        self.configFeAsic(0,0,0)

        #Set ADC SPI configuration registers
        """
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
        """

        #do the actual SPI programming
        #self.doFeAsicConfig()
        #self.doAdcAsicConfig()

    #FEMB power enable on WIB
    def powerOnFemb(self,femb):
        fembVal = int(femb)
        if (fembVal < 0) or (fembVal > 3 ):
            return

        #set UDP ports to WIB registers
        self.femb.UDP_PORT_WREG = 32000
        self.femb.UDP_PORT_RREG = 32001
        self.femb.UDP_PORT_RREGRESP = 32002

        regBase = int( fembVal * 4)

        #FEMB power enable
        self.femb.write_reg_bits(8 , regBase + 0, 0x1, 1 ) #3.6V
        self.femb.write_reg_bits(8 , regBase + 1, 0x1, 1 ) #2.8V
        self.femb.write_reg_bits(8 , regBase + 2, 0x1, 1 ) #2.5V
        self.femb.write_reg_bits(8 , regBase + 3, 0x1, 1 ) #1.5V
        self.femb.write_reg_bits(8 , 16 + fembVal, 0x1, 1 ) #BIAS enable

        #return register interface to FEMB
        self.selectFemb(self.fembNum)

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
        chReg = chReg + 0x80 #enabled
        #chReg = chReg + 0x0 #disabled

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
            if (val == None) or (val == -1):
                print("Error - FEMB register interface is not working.")
                continue
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
            if (val == None) or (val == -1):
                print("Error - FEMB register interface is not working.")
                continue
            print( str(hex(val)) )

    def doAdcAsicConfig(self):
        print("Check ADC ASIC SPI")
        for regNum in range(self.REG_ADCSPI_BASE,self.REG_ADCSPI_BASE+35,1):
            val = self.femb.read_reg( regNum)
            if (val == None) or (val == -1):
                print("Error - FEMB register interface is not working.")
                continue
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
            if (val == None) or (val == -1):
                print("Error - FEMB register interface is not working.")
                continue
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
       
        #disable all outputs
        #i2c_reg_wr(i2c_bus_base_addr, si5338_i2c_addr, 230, 0x10);
        self.write_reg_SI5338(230,0x10)

        #pause lol
	#i2c_reg_wr(i2c_bus_base_addr, si5338_i2c_addr, 241, 0xE5);
        self.write_reg_SI5338(241,0xE5)

        import femb_python.configuration.femb_config_wib_sbnd_si5338_data
        for word in range(0,349,1):
            wordNum = int(word)
            addr = int(femb_python.configuration.femb_config_wib_sbnd_si5338_data.data[3*wordNum+0])
            val = int(femb_python.configuration.femb_config_wib_sbnd_si5338_data.data[3*wordNum+1])
            mask = int(femb_python.configuration.femb_config_wib_sbnd_si5338_data.data[3*wordNum+2])

            if wordNum % 10 == 0:
                print( "Writing SI5338 register # " + str(wordNum) + " out of 349") 

            if mask == 0:
                continue

            writeVal = val
            if mask != 0xFF:
                curr_val = self.read_reg_SI5338(addr)
                clear_curr_val = curr_val & (~mask)
                clear_new_val = val & mask
                writeVal = clear_curr_val | clear_new_val
            self.write_reg_SI5338(addr,writeVal)
            #print(str(addr) + "\t" + str(writeVal)) 

        #validate input clock status
	#i2c_reg_rd(i2c_bus_base_addr, si5338_i2c_addr, 218);
        clkStatus = (self.read_reg_SI5338(218) & 0x04)
        count = 0
        while count < 100:
            clkStatus = (self.read_reg_SI5338(218) & 0x04)
            if clkStatus != 0x04:
                break
            count = count + 1
        if clkStatus == 0x04:
            print( "Did not finish clock initialization")
            return

        #configure pll
        pllWord = int(femb_python.configuration.femb_config_wib_sbnd_si5338_data.data[3*49+1])
        self.write_reg_SI5338(49,(0x7F & pllWord)) 
        
        #reset the chip
        self.write_reg_SI5338(246,0x02)

        time.sleep(0.1)

        #restart lol
        self.write_reg_SI5338(241,0x65)

        #validate pll
        pllStatus = self.read_reg_SI5338(218)
        count = 0
        while count < 100:
            pllStatus = self.read_reg_SI5338(218)
            if pllStatus == 0 :
                break
            count = count + 1
        if pllStatus != 0:
            print("Did not finish clock initialization")
            return

        #copy FCAL values to active registers 
        fcalVal = self.read_reg_SI5338(235)
        self.write_reg_SI5338(45,fcalVal)
 
        fcalVal = self.read_reg_SI5338(236)
        self.write_reg_SI5338(46,fcalVal)

        fcalVal = self.read_reg_SI5338(237)
        fcalVal = ( 0x14 | ( fcalVal & 0x3) )
        self.write_reg_SI5338(47,fcalVal)

        #set pll to use FCAL values
        #i2c_reg_wr(i2c_bus_base_addr, si5338_i2c_addr, 49, 0x80|SI5338Reg[49*3+1]);
        setPllWord = ( 0x80 | pllWord )
        self.write_reg_SI5338(49, setPllWord )

        #enable outputs
        self.write_reg_SI5338(230,0x00)
        print("Done initalizing Si5338 clock")

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
  
        self.REG_WIB_MODE = 8

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
