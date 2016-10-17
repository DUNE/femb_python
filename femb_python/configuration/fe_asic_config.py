import time

class FE_CONFIG:
    def reset(self):

        #Reset FE ASICs
        self.femb.write_reg( self.REG_ASIC_RESET, 2)
        time.sleep(0.5)

    def configureDefault(self):
        #set up default registers
        
        #internal test pulser control
        self.femb.write_reg( 5, 0x02000001)
        self.femb.write_reg( 13, 0x0) #enable

        #FE ASIC SPI registers
        print("Config FE ASIC SPI")
        for regNum in range(self.REG_FESPI_BASE,self.REG_FESPI_BASE+34,1):
                self.femb.write_reg( regNum, 0xC4C4C4C4)
        self.femb.write_reg( self.REG_FESPI_BASE+8, 0xC400C400 )
        self.femb.write_reg( self.REG_FESPI_BASE+16, 0x00C400C4 )
        self.femb.write_reg( self.REG_FESPI_BASE+25, 0xC400C400 )
        self.femb.write_reg( self.REG_FESPI_BASE+33, 0x00C400C4 )

        #Write FE ASIC SPI
        print("Program FE ASIC SPI")
        self.femb.write_reg( self.REG_ASIC_SPIPROG, 2)
        time.sleep(0.1)
        self.femb.write_reg( self.REG_ASIC_SPIPROG, 2)
        time.sleep(0.1)

        """
        print("Check FE ASIC SPI")
        for regNum in range(self.REG_FESPI_RDBACK_BASE,self.REG_FESPI_RDBACK_BASE+34,1):
                val = self.femb.read_reg( regNum)            
                print(hex(val))
        """

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
        word2 = (chReg << 8) + (chReg << 24)
        word3 = chReg + (chReg << 16)

        print("Config FE ASIC SPI")
        for regNum in range(self.REG_FESPI_BASE,self.REG_FESPI_BASE+34,1):
                self.femb.write_reg( regNum, word1)
        self.femb.write_reg( self.REG_FESPI_BASE+8, word2 )
        self.femb.write_reg( self.REG_FESPI_BASE+16, word3 )
        self.femb.write_reg( self.REG_FESPI_BASE+25, word2 )
        self.femb.write_reg( self.REG_FESPI_BASE+33, word3 )

        #Write FE ASIC SPI
        print("Program FE ASIC SPI")
        self.femb.write_reg( self.REG_ASIC_SPIPROG, 2)
        time.sleep(0.1)
        self.femb.write_reg( self.REG_ASIC_SPIPROG, 2)
        time.sleep(0.1)

        #print "Check FE ASIC SPI"
        #for regNum in range(self.REG_FESPI_RDBACK_BASE,self.REG_FESPI_RDBACK_BASE+34,1):
        #        val = self.femb.read_reg( regNum)
        #        print hex(val)

    def setInternalPulser(self,pulserEnable,pulseHeight):
        pulserEnable = int(pulserEnable)
        if (pulserEnable < 0 ) or (pulserEnable > 1):
                return
        pulserEnableVal = int(pulserEnable)
        if (pulseHeight < 0 ) or (pulseHeight > 32):
                return
        pulseHeightVal = int(pulseHeight)
        self.femb.write_reg_bits( 5 , 0, 0x1F, pulseHeightVal )
        self.femb.write_reg_bits( 13 , 1, 0x1, pulserEnableVal )

    #__INIT__#
    def __init__(self,config_file,femb_udp_obj):
        #set FEMB UDP object
        self.config_file = config_file
        self.femb = femb_udp_obj
        for key in self.config_file.listKeys("GENERAL"):
          setattr(self,key.upper(),self.config_file.get("GENERAL",key))
        for key in self.config_file.listKeys("REGISTER_LOCATIONS"):
          setattr(self,key.upper(),self.config_file.get("REGISTER_LOCATIONS",key))
