"""
Main Configuration module.
"""
import sys
import os.path
import time
from .config_file_parser import CONFIG_FILE
from .asic_reg_packing import ASIC_REG_PACKING
from .fe_asic_config import FE_CONFIG
from ..femb_udp import FEMB_UDP

class CONFIG:
    """
    Main configuration class. Rangles other classes that configure the ADC ASIC and FE ASIC.
    """

    def resetBoard(self):
      #Reset system
      self.femb.write_reg( self.REG_RESET, 1)
      time.sleep(5.)

      #Reset registers
      self.femb.write_reg( self.REG_RESET, 2)
      time.sleep(1.)

      if self.hasFE:
        #Reset FE ASICs
        self.femb.write_reg( self.REG_ASIC_RESET, 2)
        time.sleep(0.5)
      if self.hasADC:
        #Reset ADC ASICs
        self.femb.write_reg( self.REG_ASIC_RESET, 1)
        time.sleep(0.5)

    def initBoard(self):
      self.resetBoard()
      self.setRegisterInitialVals()
      if self.TOGGLE_HSLINK:
        self.femb.write_reg( self.REG_HSLINK, 0x1)
        self.femb.write_reg( self.REG_HSLINK, 0x0)
      if self.hasFE:
        self.fe.configureDefault()
      if self.hasADC:
        self.configAdcAsic()

    def configAdcAsic(self,regs=None):
        if not self.hasADC:
          print("CONFIG.configAdcAsic: no ADC ASIC present in configuration")
        if not regs: # then get from configuration file
            nbits_global = self.config_file.get("ADC_CONFIGURATION","NBITS_GLOBAL")
            nbits_channel = self.config_file.get("ADC_CONFIGURATION","NBITS_CHANNEL")
            global_bits = self.config_file.get("ADC_CONFIGURATION","GLOBAL_BITS")
            channel_bits = self.config_file.get("ADC_CONFIGURATION","CHANNEL_BITS")
            print(("Setting all ADC global config registers to {:#0"+str(nbits_global+2)+"b}").format(global_bits))
            print(("Setting all ADC channel config registers to {:#0"+str(nbits_channel+2)+"b}").format(channel_bits))
            arp = ASIC_REG_PACKING(nbits_global,nbits_channel)
            arp.set_board(global_bits,channel_bits)
            for iChip in range(self.NASICS):
                try:
                    global_bits = self.config_file.get("ADC_CONFIGURATION","ASIC{}_GLOBAL_BITS".format(iChip))
                except:
                    pass
                else:
                    print(("Setting ADC chip {} global config registers to {:#0"+str(nbits_global+2)+"b}").format(iChip,global_bits))
                    arp.set_chip_global(iChip,global_bits)
                try:
                    channel_bits = self.config_file.get("ADC_CONFIGURATION","ASIC{}_CHANNEL_BITS".format(iChip))
                except:
                    pass
                else:
                    print(("Setting ADC chip {} channel config registers to {:#0"+str(nbits_channel+2)+"b}").format(iChip,channel_bits))
                    for iChan in range(16):
                        arp.set_chn_reg(iChip,iChan,channel_bits)
                for iChan in range(16):
                    try:
                        channel_bits = self.config_file.get("ADC_CONFIGURATION","ASIC{}_CHANNEL{}_BITS".format(iChip,iChan))
                    except:
                        pass
                    else:
                        print(("Setting ADC chip {} channel {} config registers to {:#0"+str(nbits_channel+2)+"b}").format(iChip,iChan,channel_bits))
                        arp.set_chn_reg(iChip,iChan,channel_bits)
            regs = arp.getREGS()
        checkReadback = True
        try:
            checkReadback = not self.DONTCHECKREADBACK
        except:
            pass
        #ADC ASIC SPI registers
        print("CONFIG--> Config ADC ASIC SPI")
        for k in range(10):
            i = 0
            for regNum in range(self.REG_ADCSPI_BASE,self.REG_ADCSPI_BASE+len(regs),1):
                    self.femb.write_reg( regNum, regs[i])
                    i = i + 1

            #Write ADC ASIC SPI
            print("CONFIG--> Program ADC ASIC SPI")
            self.femb.write_reg( self.REG_ASIC_SPIPROG, 1)
            time.sleep(0.1)
            self.femb.write_reg( self.REG_ASIC_SPIPROG, 1)
            time.sleep(0.1)

            print("CONFIG--> Check ADC ASIC SPI")
            adcasic_rb_regs = []
            for regNum in range(self.REG_ADCSPI_RDBACK_BASE,self.REG_ADCSPI_RDBACK_BASE+len(regs),1):
                val = self.femb.read_reg( regNum ) 
                adcasic_rb_regs.append( val )
                print(hex(val))

            if checkReadback:
                if (adcasic_rb_regs !=regs  ) :
                    if ( k == 1 ):
                        sys.exit("CONFIG : Wrong readback. ADC SPI failed")
                        return
                else: 
                    print("CONFIG--> ADC ASIC SPI is OK")
                    break
            else:
                print("CONFIG--> Not checking if ADC readback is okay")
                break

    def configFeAsic(self,gain,shape,base):
      if not self.hasFE:
        print("CONFIG.configFeAsic: no FE ASIC present in configuration")
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

    def selectChannel(self,asic,chan):
        asicVal = int(asic)
        if (asicVal < 0 ) or (asicVal > self.NASICS - 1) :
                print("config_femb : selectChan - invalid ASIC number, must be between 0 and {0}".format(self.NASICS - 1))
                return
        chVal = int(chan)
        if (chVal < 0 ) or (chVal > 15) :
                print("config_femb : selectChan - invalid channel number, must be between 0 and 15")
                return
        #print "Selecting ASIC " + str(asicVal) + ", channel " + str(chVal)
        regVal = (chVal << 8 ) + asicVal
        self.femb.write_reg( self.REG_SEL_CH, regVal)

    def setInternalPulser(self,pulserEnable,pulseHeight):
      if not self.hasFE:
        print("CONFIG.setInternalPulser: no FE ASIC present in configuration")
        return
      pulserEnable = int(pulserEnable)
      if (pulserEnable < 0 ) or (pulserEnable > 1):
              return
      pulserEnableVal = int(pulserEnable)
      if (pulseHeight < 0 ) or (pulseHeight > 32):
              return
      pulseHeightVal = int(pulseHeight)
      self.femb.write_reg_bits( 5 , 0, 0x1F, pulseHeightVal )
      self.femb.write_reg_bits( 13 , 1, 0x1, pulserEnableVal )

    def syncADC(self):
      if not self.hasADC:
        print("CONFIG.syncADC: no ADC ASIC present in configuration")
      #turn on ADC test mode
      print("Start sync ADC")
      reg3 = self.femb.read_reg(3)
      newReg3 = ( reg3 | 0x80000000 )
      self.femb.write_reg( 3, newReg3 ) #31 - enable ADC test pattern
      for a in range(0,8,1):
              print("Test ADC " + str(a))
              unsync = self.testUnsync(a)
              if unsync != 0:
                      print("ADC not synced, try to fix")
                      self.fixUnsync(a)
      LATCH = self.femb.read_reg( self.REG_LATCHLOC )
      PHASE = self.femb.read_reg( self.REG_CLKPHASE )
      print("Latch latency " + str(hex(LATCH)) + "\tPhase " + str(hex(PHASE)))
      print("End sync ADC")


    def testUnsync(self, adc):
      if not self.hasADC:
        print("CONFIG.testUnsync: no ADC ASIC present in configuration")

    def fixUnsync(self, adc):
      if not self.hasADC:
        print("CONFIG.fixUnsync: no ADC ASIC present in configuration")

    def setRegisterInitialVals(self):
        for key in self.config_file.listKeys("REGISTER_INITIAL_VALUES"):
          regName = key.upper()
          regLoc = None
          try:
            regLoc = getattr(self,regName)
          except:
            raise Exception("Register Location for '{}' not found in '{}'".format(regLoc,self.filename))
          regVal = self.config_file.get("REGISTER_INITIAL_VALUES",key)
          print("Setting {}, reg {} to {:#010x}".format(regName,regLoc,regVal))
          self.femb.write_reg(regLoc,regVal)

    #__INIT__#
    def __init__(self,config_file_name):
        print("Using configuration file: {}".format(os.path.abspath(config_file_name)))
        #initialize FEMB UDP object
        self.femb = FEMB_UDP()
        #read the config file
        self.filename = config_file_name
        self.config_file = CONFIG_FILE(self.filename)
        self.hasADC = False
        self.hasFE = False
        if self.config_file.hasADC():
          self.hasADC = True
        if self.config_file.hasFE():
          self.hasFE = True
        for key in self.config_file.listKeys("GENERAL"):
          setattr(self,key.upper(),self.config_file.get("GENERAL",key))
        for key in self.config_file.listKeys("REGISTER_LOCATIONS"):
          setattr(self,key.upper(),self.config_file.get("REGISTER_LOCATIONS",key))
        try:
          setattr(self,"TOGGLE_HSLINK",self.config_file.get("GENERAL","TOGGLE_HSLINK",isBool=True))
        except:
          setattr(self,"TOGGLE_HSLINK",False)
        try:
          setattr(self,"DONTCHECKREADBACK",self.config_file.get("GENERAL","DONTCHECKREADBACK",isBool=True))
        except:
          setattr(self,"DONTCHECKREADBACK",False)
        

if __name__ == "__main__":
    print("########################################")
    print("35t.ini:")
    cfg = CONFIG("35t.ini")
    print("########################################")
    print("adctest.ini:")
    cfg = CONFIG("adctest.ini")
