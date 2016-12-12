from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import
from builtins import int
from future import standard_library
standard_library.install_aliases()
from builtins import object
import time

class BOARD_CONFIG(object):
    def reset(self):
        #Reset system
        self.femb.write_reg( self.REG_RESET, 1)
        time.sleep(5.)

        #Reset registers
        self.femb.write_reg( self.REG_RESET, 2)
        time.sleep(1.)

        #Time stamp reset
        #femb.write_reg( 0, 4)
        #time.sleep(0.5)

    def configureDefault(self):
        #set up default registers
        
        #Set test and readout mode register
        self.femb.write_reg( 7, 0x0000) #11-8 = channel select, 3-0 = ASIC select

        #Set number events per header
        self.femb.write_reg( 8, 0x0)

    def selectChannel(self,asic,chan):
        asicVal = int(asic)
        if (asicVal < 0 ) or (asicVal > self.NASICS - 1) :
                print("femb_config_femb : selectChan - invalid ASIC number, must be between 0 and {0}".format(self.NASICS - 1))
                return
        chVal = int(chan)
        if (chVal < 0 ) or (chVal > 15) :
                print("femb_config_femb : selectChan - invalid channel number, must be between 0 and 15")
                return

        #print "Selecting ASIC " + str(asicVal) + ", channel " + str(chVal)

        regVal = (chVal << 8 ) + asicVal
        self.femb.write_reg( self.REG_SEL_CH, regVal)

    #__INIT__#
    def __init__(self,config_file,femb_udp_obj):
        #set FEMB UDP object
        self.config_file = config_file
        self.femb = femb_udp_obj
        for key in self.config_file.listKeys("BOARD"):
          value = self.config_file.boardParam(key)
          key = key.upper()
          setattr(self,key,value)
          print(key,getattr(self,key))
        print("board object attrs: ",dir(self))
