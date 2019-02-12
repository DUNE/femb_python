""" 
Board-specific function
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
from femb_python.generic_femb_udp import FEMB_UDP
from femb_python.test_measurements.quad_FE_Board.low_level_pre_udp import LOW_LEVEL
from femb_python.test_measurements.quad_FE_Board.sync_functions import SYNC_FUNCTIONS
from femb_python.test_measurements.quad_FE_Board.ASIC_config import ASIC_CONFIG_FUNCTIONS
from femb_python.configuration.config_module_loader import getDefaultDirectory
import time
import matplotlib.pyplot as plt
import numpy as np
import os
import json

class FEMB_CONFIG_FUNCTIONS(object):
    """
    Base class for configuration files. These should be considered the 'public'
    methods of the config classes, non-configuration code should only use this set
    of functions.  
    """

    def __init__(self, config_file = None):
        """
        Initialize this class (no board communication here. Should setup self.femb_udp as a femb_udp instance, get FE Registers, etc...)
        """
        if (config_file == None):
            from femb_python.configuration import CONFIG
            self.config = CONFIG
        else:
            self.config = config_file
            
        self.femb_udp = FEMB_UDP(self.config)     
        self.low_func = LOW_LEVEL(self.config)
        self.sync_functions = SYNC_FUNCTIONS(self.config)
        self.asic_config = ASIC_CONFIG_FUNCTIONS(self.config)
        
        self.root_dir = getDefaultDirectory()
        file_name = os.path.join(self.root_dir,self.config["FILENAMES"]["DEFAULT_GUI_FILE_NAME"])
        if os.path.isfile(file_name):
            self.default_settings = dict()
            with open(file_name, 'r') as f:
                jsondata = json.load(f)
                for i in jsondata:
                    self.default_settings[i] = jsondata[i]
                    
        self.board_ver = self.default_settings["boardid"]

    def initBoard(self, **kwargs):
        """
        Initialize board/asics with default configuration
        """

        self.femb_udp.write_reg(int(self.config["REGISTERS"]["REG_MUX_MODE"]), int(self.config["INITIAL_SETTINGS"]["DEFAULT_MUX"]))
        self.femb_udp.write_reg(int(self.config["REGISTERS"]["REG_SS"]), int(self.config["INITIAL_SETTINGS"]["DEFAULT_SS"]))
        self.femb_udp.write_reg(int(self.config["REGISTERS"]["REG_TIMEOUT"]), int(self.config["INITIAL_SETTINGS"]["DEFAULT_TIMEOUT"], 16))
        self.femb_udp.write_reg(int(self.config["REGISTERS"]["REG_SAMPLESPEED"]), int(self.config["INITIAL_SETTINGS"]["DEFAULT_SAMPLE_SPEED"]))
        
        default_frame_size = 16 * (int(self.config["INITIAL_SETTINGS"]["DEFAULT_FRAME_SIZE"], 16)//16)
        #Readback gives other values, it'll always be wrong
        self.femb_udp.write_reg(int(self.config["REGISTERS"]["REG_FRAME_SIZE"]), default_frame_size, doReadBack = False)
        
        self.low_func.setExternalPulser(val=int(self.config["INITIAL_SETTINGS"]["DEFAULT_EXTERNAL_DAC_VAL"], 16), 
                               period=int(self.config["INITIAL_SETTINGS"]["DEFAULT_EXTERNAL_DAC_TP_PERIOD"]), shift=int(self.config["INITIAL_SETTINGS"]["DEFAULT_EXTERNAL_DAC_TP_SHIFT"]), enable=False)
                       
        self.asic_config.configFeAsic(test_cap="on", base="200mV", gain="14mV", shape="2us", monitor_ch=None, buffer="off", 
                       leak = "500pA", monitor_param = None, s16=None, acdc="dc", test_dac="test_off", dac_value=0)
        
        self.low_func.selectChipChannel(chip = 2, chn = 7)
        self.low_func.selectChipChannel(chip = 1, chn = 6)
        
        if 'default_sync' in kwargs:
            print("found it")
            default_sync = kwargs["default_sync"]
        else:
            print("Did not find it")
            default_sync = True
    
        if (default_sync == True):
            print("config_functions --> Putting in default sync settings")
            latch_settings_name = "{}_LATCH_SETTINGS".format(self.board_ver)
            phase_settings_name = "{}_PHASE_SETTINGS".format(self.board_ver)
            
            latch = []
            phase = []
            
            #This section loops through the categories to get the settings we want, since you can't make arrays in INI files
            try:
                latch_settings = list(self.config._sections["{}".format(latch_settings_name)].keys())
                phase_settings = list(self.config._sections["{}".format(phase_settings_name)].keys())
                
                for i in range(len(latch_settings)):
                    latch.append(int(self.config["{}".format(latch_settings_name)][latch_settings[i]], 16))
                for i in range(len(phase_settings)):
                    phase.append(int(self.config["{}".format(phase_settings_name)][phase_settings[i]], 16))
                
            except KeyError:
                print("config_functions --> No settings found for {} and {}!  Using defaults".format(latch_settings_name, phase_settings_name))
                latch_settings = list(self.config._sections["LATCH_SETTINGS_DEFAULT"].keys())
                phase_settings = list(self.config._sections["PHASE_SETTINGS_DEFAULT"].keys())
                
                for i in range(len(latch_settings)):
                    latch.append(int(self.config["LATCH_SETTINGS_DEFAULT"][latch_settings[i]], 16))
                for i in range(len(phase_settings)):
                    phase.append(int(self.config["PHASE_SETTINGS_DEFAULT"][phase_settings[i]], 16))
                
            for i,reg in enumerate(range(int(self.config["REGISTERS"]["REG_LATCH_MIN"]), int(self.config["REGISTERS"]["REG_LATCH_MAX"]) + 1, 1)):
                self.femb_udp.write_reg(reg, latch[i])
            for i,reg in enumerate(range(int(self.config["REGISTERS"]["REG_PHASE_MIN"]), int(self.config["REGISTERS"]["REG_PHASE_MAX"]) + 1, 1)):
                self.femb_udp.write_reg(reg, phase[i])
            self.femb_udp.write_reg(int(self.config["REGISTERS"]["REG_TEST_ADC"]), int(self.config["INITIAL_SETTINGS"]["DEFAULT_MONITOR_ADC_SETTINGS"], 16))
            
        else:
            print("config_functions --> Skipping default sync settings")
        
        self.SPI_array = self.asic_config.writeFE()
        return self.SPI_array