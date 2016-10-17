"""
Main Configuration module.
"""
import os.path
import time
from .config_file_parser import CONFIG_FILE
from .adc_asic_config import ADC_CONFIG
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

      if self.fe:
        #Reset FE ASICs
        self.femb.write_reg( self.REG_ASIC_RESET, 2)
        time.sleep(0.5)
      if self.adc:
        #Reset ADC ASICs
        self.femb.write_reg( self.REG_ASIC_RESET, 1)
        time.sleep(0.5)

    def initBoard(self):
      self.resetBoard()
      self.setRegisterInitialVals()
      if self.TOGGLE_HSLINK:
        self.femb.write_reg( self.REG_HSLINK, 0x1)
        self.femb.write_reg( self.REG_HSLINK, 0x0)
      if self.fe:
        self.fe.configureDefault()
      if self.adc:
        self.adc.configureDefault()

    def configFeAsic(self,gain,shape,base):
      if self.fe:
        self.fe.configFeAsic(gain,shape,base)
      else:
        print("CONFIG.configFeAsic: no FE ASIC present in configuration")

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
      if self.fe:
        self.fe.setInternalPulser()
      else:
        print("CONFIG.setInternalPulser: no FE ASIC present in configuration")

    def syncADC(self):
      if self.adc:
        self.adc.syncADC()
      else:
        print("CONFIG.syncADC: no ADC ASIC present in configuration")

    def testUnsync(self, adc):
      if self.adc:
        self.adc.testUnsync(adc)
      else:
        print("CONFIG.syncADC: no ADC ASIC present in configuration")

    def fixUnsync(self, adc):
      if self.adc:
        self.adc.fixUnsync(adc)
      else:
        print("CONFIG.syncADC: no ADC ASIC present in configuration")

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
        self.adc = None
        self.fe = None
        #if self.config_file.hasADC():
        if True:
          self.adc = ADC_CONFIG(self.config_file,self.femb)
        if False:
          self.fe = FE_CONFIG(self.config_file,self.femb)
        for key in self.config_file.listKeys("GENERAL"):
          setattr(self,key.upper(),self.config_file.get("GENERAL",key))
        for key in self.config_file.listKeys("REGISTER_LOCATIONS"):
          setattr(self,key.upper(),self.config_file.get("REGISTER_LOCATIONS",key))
        try:
          setattr(self,"TOGGLE_HSLINK",self.config_file.get("GENERAL","TOGGLE_HSLINK",isBool=True))
        except:
          setattr(self,"TOGGLE_HSLINK",False)
          
        

if __name__ == "__main__":
    print("########################################")
    print("35t.ini:")
    cfg = CONFIG("35t.ini")
    print("########################################")
    print("adctest.ini:")
    cfg = CONFIG("adctest.ini")
