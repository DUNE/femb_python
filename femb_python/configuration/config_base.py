""" 
Base class for configuration files. These should be considered the 'public'
methods of the config classes, non-configuration code should only use this set
of functions.  
"""

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import
from builtins import int
from builtins import range
from builtins import hex
from builtins import str
from future import standard_library
standard_library.install_aliases()
from builtins import object
import time
import sys
import os
import json
from femb_python.test_measurements.quad_FE_Board.config_functions import FEMB_CONFIG_FUNCTIONS as quadFE
from femb_python.configuration.config_module_loader import getDefaultDirectory

class FEMBConfigError(Exception):
    """Base class exception for femb_python configuration errors"""
    pass

class ConfigADCError(FEMBConfigError):
    """Exception when you can't configure the ADC"""
    pass

class SyncADCError(FEMBConfigError):
    """Exception when you can't sync the ADC"""
    pass

class InitBoardError(FEMBConfigError):
    """Exception when you can't initialize a board"""
    pass

class ReadRegError(FEMBConfigError):
    """Exception when you can't read a register"""
    pass

class FEMB_CONFIG_BASE(object):
    """
    Base class for configuration files. These should be considered the 'public'
    methods of the config classes, non-configuration code should only use this set
    of functions.  
    """

    def __init__(self, config_file = None, exitOnError=True):
        """
        Initialize this class (no board communication here. Should setup self.femb_interface as a femb_udp instance.)
        if exitOnError is false, methods should raise error that subclass FEMBConfigError
        """
        if (config_file == None):
            from femb_python.configuration import CONFIG
            self.config = CONFIG
        else:
            self.config = config_file
            
        all_tests = {'quadFE': quadFE}
        try:
            board = all_tests[self.config["DEFAULT"]["NAME"]]
        except KeyError:
            print("FEMB_CONFIG_BASE --> self.config is {}".format(self.config))
            sys.exit("FEMB_CONFIG_BASE --> No board class for {}".format(self.config["DEFAULT"]["NAME"]))
        self.test = board()
        self.FE_Regs = self.test.asic_config.FE_Regs
        self.ASIC_functions = self.test.asic_config
        
        self.root_dir = getDefaultDirectory()
        file_name = os.path.join(self.root_dir,self.config["FILENAMES"]["DEFAULT_GUI_FILE_NAME"])
        if os.path.isfile(file_name):
            self.default_settings = dict()
            with open(file_name, 'r') as f:
                jsondata = json.load(f)
                for i in jsondata:
                    self.default_settings[i] = jsondata[i]
                    
        self.master_chip_list = [[0,self.default_settings["asic0id"]], [1,self.default_settings["asic1id"]], [2,self.default_settings["asic2id"]], [3,self.default_settings["asic3id"]]]
    
        self.femb_interface = self.test.femb_udp
        self.lower_functions = self.test.low_func
        self.sync = self.test.sync_functions
        self.exitOnError=exitOnError
        
    def resetBoard(self):
        """
        Resets board.  Some of them really do need 5 seconds before you can communicate
        """
        print ("FEMB_CONFIG_BASE--> Reset FEMB (5 Seconds)")
        self.femb_interface.write_reg ( self.config["REGISTERS"]["REG_RESET"], self.config["DEFINITIONS"]["RESET"])
        time.sleep(5)
        print ("FEMB_CONFIG_BASE--> Reset FEMB is DONE")

    def initBoard(self, **kwargs):
        """
        Initialize board/asics with default configuration as determined by their own classes, since it's so specific
        """        
        result = self.test.initBoard(**kwargs)
        
        if (result != None):
            print ("FEMB_CONFIG_BASE--> Init Board Passed!")
            return (result)
        else:
            print("FEMB_CONFIG_BASE --> initBoard failed - Response was {}".format(result))
    
    #Note, on the FE quad board, REG_ON_OFF also returns the status of the buttons being pushed, so it won't always return exactly what you wrote, hence doReadback=False
    def turnOffAsics(self):
        print ("FEMB_CONFIG_BASE--> Turning ASICs off (2 seconds)")
        self.femb_interface.write_reg(int(self.config["REGISTERS"]["REG_ON_OFF"]), int(self.config["DEFINITIONS"]["ASIC_OFF"], 2), doReadBack=False)
        #pause after turning off ASICs
        time.sleep(2)
        print ("FEMB_CONFIG_BASE--> ASICs off")
        
    def turnOnAsics(self):
        print ("FEMB_CONFIG_BASE--> Turning ASICs on (2 seconds)")
        self.femb_interface.write_reg(int(self.config["REGISTERS"]["REG_ON_OFF"]), int(self.config["DEFINITIONS"]["ASIC_ON"]), doReadBack=False)
        #pause after turning on ASICSs
        time.sleep(2)
        print ("FEMB_CONFIG_BASE--> ASICs on")

    def writeADC(self,Adcasic_regs):
        """
        Configure ADCs with given list of registers
        """
        pass
    
    def configAdcAsic(self,enableOffsetCurrent=None,offsetCurrent=None,testInput=None,
                            freqInternal=None,sleep=None,pdsr=None,pcsr=None,
                            clockMonostable=None,clockExternal=None,clockFromFIFO=None,
                            sLSB=None,f0=None,f1=None,f2=None,f3=None,f4=None,f5=None):
       #Need to set for new ADC
        pass

    def writeFE(self):
        """
        This will write the last configFeAsic settings to the actual chips, so all those new settings come into affect AFTER this method
        """
        try:
            response = self.ASIC_functions.writeFE()
        except AttributeError:
            sys.exit("FEMB_CONFIG_BASE --> {} does not have writeFE() method!".format(self.config["DEFAULT"]["NAME"]))
            
        for count, name in self.master_chip_list:
            if count not in response:
                print("FEMB_CONFIG_BASE --> Chip {}({}) failed FE SPI write!".format(count, name))

    def configFeAsic(self,**kwargs):
        """
        Prepares ASIC configuration registers for new settings but does NOT send them and make them active
        """
        try:
            self.ASIC_functions.configFeAsic(**kwargs)
        except AttributeError:
            print("FEMB_CONFIG_BASE --> {} does not have configFeAsic() method!".format(self.config["DEFAULT"]["NAME"]))

    #Returns boolean array of the chips that pass.  If a chips is not part of "working chips", its place will be empty in the array
    #chip_id[0] is the index of the chip, where it sits on the board (spot 0, 1, 2, 3 etc...)
    #chip_id[1] is its name (A2567, A2568, etc...)
    def syncADC(self, **kwargs):
#        try:
        response = self.sync.syncADC(**kwargs)
#        except AttributeError:
#            sys.exit("FEMB_CONFIG_BASE --> {} does not have syncADC() method!".format(self.config["DEFAULT"]["NAME"]))
            
        if (response == False):
            print("FEMB_CONFIG_BASE --> syncADC() failed")
    
    def get_fw_version(self):
        try:
            resp = self.femb_interface.read_reg(int(self.config["REGISTERS"]["REG_FW_VER"]))
        except KeyError:
            sys.exit("FEMB_CONFIG_BASE --> {} does not have a register for firmware version!!".format(self.config["DEFAULT"]["NAME"]))

        if (resp != None):
            return resp
        else:
            print("FEMB_CONFIG_BASE --> No response for firmware version!!")
        
    #Get a whole chip's worth of data
    def get_data_chipX(self, chip, packets = 1, data_format = "counts", tagged = False, header = False):
        
        chip_data = [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]]
        for chn in range(int(self.config["DEFAULT"]["NASICCH"])):
            for i in range(packets):
                if (tagged == False):
                    chip_data[chn].extend(list(self.lower_functions.get_data_chipXchnX(chip, chn, packets = packets, data_format = data_format, header = header)))
                else:
                    chip_data[chn].extend(list(self.lower_functions.get_data_chipXchnX_tagged(chip, chn, packets = packets, data_format = data_format, header = header)))
        return chip_data
        
    def setInternalPulser(self, **kwargs):
        try:
            self.lower_functions.setInternalPulser(**kwargs)
        except AttributeError:
            print("FEMB_CONFIG_BASE --> {} does not have setInternalPulser() method!".format(self.config["DEFAULT"]["NAME"]))
        
    def setExternalPulser(self, **kwargs):
        try:
            self.lower_functions.setExternalPulser(**kwargs)
        except AttributeError:
            print("FEMB_CONFIG_BASE --> {} does not have setExternalPulser() method!".format(self.config["DEFAULT"]["NAME"]))