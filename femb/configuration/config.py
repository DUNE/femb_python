import sys 
import string
import time
from  config_file_parser import CONFIG_FILE
from adc_asic_config import ADC_CONFIG
from fe_asic_config import FE_CONFIG
from board_config import BOARD_CONFIG
from femb_udp_cmdline import FEMB_UDP

class CONFIG:

    def resetBoard(self):
      self.board_config.reset()
      if self.fe_config:
        self.fe_config.reset()
      if self.adc_config:
        self.adc_config.reset()

    def initBoard(self):
      self.board_config.configureDefault()
      if self.fe_config:
        self.fe_config.configureDefault()
      if self.adc_config:
        self.adc_config.configureDefault()

    def configFeAsic(self,gain,shape,base):
      if self.fe_config:
        self.fe_config.configFeAsic(gain,shape,base)
      else:
        print("CONFIG.configFeAsic: no FE ASIC present in configuration")

    def setInternalPulser(self,pulserEnable,pulseHeight):
      pass

    def syncADC(self):
      if self.adc_config:
        self.adc_config.syncADC()
      else:
        print("CONFIG.syncADC: no ADC ASIC present in configuration")

    def testUnsync(self, adc):
      if self.adc_config:
        self.adc_config.testUnsync(adc)
      else:
        print("CONFIG.syncADC: no ADC ASIC present in configuration")

    def fixUnsync(self, adc):
      if self.adc_config:
        self.adc_config.fixUnsync(adc)
      else:
        print("CONFIG.syncADC: no ADC ASIC present in configuration")

    #__INIT__#
    def __init__(self,config_file_name):
        #initialize FEMB UDP object
        self.femb = FEMB_UDP()
        #read the config file
        self.filename = config_file_name
        self.config_file = CONFIG_FILE(self.filename)
        self.board = BOARD_CONFIG(self.config_file,self.femb)
        self.adc = None
        self.fe = None
        if self.config_file.hasADC():
          self.adc = ADC_CONFIG(self.config_file,self.femb)
        if self.config_file.hasFE():
          self.fe = FE_CONFIG(self.config_file,self.femb)

if __name__ == "__main__":
    print("########################################")
    print("35t.ini:")
    cfg = CONFIG("35t.ini")
    print("########################################")
    print("adctest.ini:")
    cfg = CONFIG("adctest.ini")
