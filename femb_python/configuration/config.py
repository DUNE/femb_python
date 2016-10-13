"""
Main Configuration module.
"""
import os.path
from .config_file_parser import CONFIG_FILE
from .adc_asic_config import ADC_CONFIG
from .fe_asic_config import FE_CONFIG
from .board_config import BOARD_CONFIG
from ..femb_udp import FEMB_UDP

class CONFIG:
    """
    Main configuration class. Rangles other classes that configure the ADC ASIC, FE ASIC, and FEMB itself.
    """

    def resetBoard(self):
      self.board.reset()
      if self.fe:
        self.fe.reset()
      if self.adc:
        self.adc.reset()

    def initBoard(self):
      self.resetBoard()
      self.board.configureDefault()
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
      return self.board.selectChannel(asic,chan)

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

    #__INIT__#
    def __init__(self,config_file_name):
        print("Using configuration file: {}".format(os.path.abspath(config_file_name)))
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
