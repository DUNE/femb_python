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
from femb_python.configuration.FE_config import FE_CONFIG 
from femb_python.configuration.config_module_loader import getDefaultDirectory
import time
import matplotlib.pyplot as plt
import numpy as np
import os
import json

class ASIC_CONFIG_FUNCTIONS(object):
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
        self.FE_Regs = FE_CONFIG(chip_num = int(self.config["DEFAULT"]["NASICS"]), chn_num = int(self.config["DEFAULT"]["NASICCH"]))
        
        self.root_dir = getDefaultDirectory()
        file_name = os.path.join(self.root_dir,self.config["FILENAMES"]["DEFAULT_GUI_FILE_NAME"])
        if os.path.isfile(file_name):
            self.default_settings = dict()
            with open(file_name, 'r') as f:
                jsondata = json.load(f)
                for i in jsondata:
                    self.default_settings[i] = jsondata[i]
                    
        try:
            self.chip_ver = int(self.default_settings["chipver"])
        except (ValueError, AttributeError):
            self.chip_ver = 7
    
    def writeFE(self,**kwargs):
        #Grab ASIC settings from linked class
        Feasic_regs = self.feasic_regs
        #note which sockets fail
        config_list = [False,False,False,False]
        try:
            working_chips = kwargs['working_chips']
        except KeyError:
            working_chips = [0, 1, 2, 3]
        #Try 10 times (ocassionally it wont work the first time)
        for k in range(10):
            #Puts the settings in FPGA memory
            for i,regNum in enumerate(range(int(self.config["REGISTERS"]["REG_FESPI_BASE"]), int(self.config["REGISTERS"]["REG_FESPI_BASE"])+len(Feasic_regs), 1)):
                self.femb_udp.write_reg( regNum, Feasic_regs[i])
#                print (hex(Feasic_regs[i]))

            #Reset, then write twice to the ASICs
            reg = int(self.config["REGISTERS"]["REG_FEASIC_SPI"])
            reset = int(self.config["DEFINITIONS"]["FEASIC_SPI_RESET"])
            start = int(self.config["DEFINITIONS"]["FEASIC_SPI_START"])
            stop = int(self.config["DEFINITIONS"]["FEASIC_SPI_STOP"])
            self.femb_udp.write_reg ( reg, reset, doReadBack = False)
            self.femb_udp.write_reg ( reg, stop, doReadBack = False)
            time.sleep(.2)
            self.femb_udp.write_reg ( reg, start, doReadBack = False)
            self.femb_udp.write_reg ( reg, stop, doReadBack = False)
            time.sleep(.2)
            self.femb_udp.write_reg ( reg, start, doReadBack = False)
            self.femb_udp.write_reg ( reg, stop, doReadBack = False)
            time.sleep(.2)
            
            #The FPGA automatically compares the readback to check if it matches what was written.  That result is read back
            #A bit that's zero means the corresponding ASIC didn't write properly
            val = self.femb_udp.read_reg(reg) 
            wrong = False

            #check to see if everything went well, and return the status of the 4 chips in the array, so the sequence can notify/skip them
            if 0 in working_chips:
                if (((val & 0x10000) >> 16) != 1):
                    print ("FEMB_CONFIG_BASE--> Something went wrong when programming FE 1")
                    config_list[0] = False
                    wrong = True
                else:
                    config_list[0] = True
                    
            if 1 in working_chips:
                if (((val & 0x20000) >> 17) != 1):
                    print ("FEMB_CONFIG_BASE--> Something went wrong when programming FE 2")
                    config_list[1] = False
                    wrong = True
                else:
                    config_list[1] = True
                
            if 2 in working_chips:
                if (((val & 0x40000) >> 18) != 1):
                    print ("FEMB_CONFIG_BASE--> Something went wrong when programming FE 3")
                    config_list[2] = False
                    wrong = True
                else:
                    config_list[2] = True
                
            if 3 in working_chips:
                if (((val & 0x80000) >> 19) != 1):
                    print ("FEMB_CONFIG_BASE--> Something went wrong when programming FE 4")
                    config_list[3] = False
                    wrong = True
                else:
                    config_list[3] = True

            if (wrong == True and k == 9):
                try:
                    print ("FEMB_CONFIG_BASE--> SPI_Status is {}").format(hex(val))
                except AttributeError:
                    print ("FEMB_CONFIG_BASE--> SPI_Status is NOT ok for all chips")
                
            elif (wrong == False):
#                    print ("FEMB_CONFIG_BASE--> FE ASIC SPI is OK")
                break
                
        working_chips = []
        for i,j in enumerate(config_list):
            if (j==True):
                working_chips.append(i)
                
        return working_chips
        
    def configFeAsic(self,gain,shape,base,leak,test_cap,test_dac,dac_value,buffer,monitor_ch=None,acdc="dc",monitor_param=None,s16=None, chip=None, chn=None):

        """
        Gain bits      LARASIC7          LARASIC8
        00                4.7               14
        10                7.8               25
        01                14                7.8
        11                25                4.7 
        """
        if (self.chip_ver == 7):
            if gain == "4.7mV": sg = 0
            elif gain == "7.8mV": sg = 2
            elif gain == "14mV": sg = 1      
            elif gain == "25mV": sg = 3
            else: 
                print("FEMB_CONFIG_BASE--> {} is an invalid gain setting".format(gain))
                return None
        elif (self.chip_ver == 8):
            if gain == "4.7mV": sg = 3
            elif gain == "7.8mV": sg = 1
            elif gain == "14mV": sg = 0       
            elif gain == "25mV": sg = 2
            else:
                print("FEMB_CONFIG_BASE--> {} is an invalid gain setting".format(gain))
                return None
                
        else:
            print("Chip version is {}?".format(self.chip_ver))
            if gain == "4.7mV": sg = 0
            elif gain == "7.8mV": sg = 2
            elif gain == "14mV": sg = 1      
            elif gain == "25mV": sg = 3
            else: 
                print("FEMB_CONFIG_BASE--> {} is an invalid gain setting".format(gain))
                return None
                
        if shape == "0.5us": st = 2
        elif shape == "1us": st = 0
        elif shape == "2us": st = 3        
        elif shape == "3us": st = 1
        else:
            print("FEMB_CONFIG_BASE--> {} is an invalid shaping time setting".format(shape))
            return None

        if leak == "100pA": slk,slkh = 0,1
        elif leak == "500pA": slk,slkh = 0,0
        elif leak == "1nA": slk,slkh = 1,1       
        elif leak == "5nA": slk,slkh = 1,0
        else:
            print("FEMB_CONFIG_BASE--> {} is an invalid leakage current setting".format(leak))
            return None
        
        if test_dac == "test_off": sdacsw1,sdacsw2 = 0,0
        elif test_dac == "test_int": sdacsw1,sdacsw2 = 0,1
        elif test_dac == "test_ext": sdacsw1,sdacsw2 = 1,0
        elif test_dac == "test_meas": sdacsw1,sdacsw2 = 1,1
        else:
            print("FEMB_CONFIG_BASE--> {} is an invalid test pulse/DAC setting".format(test_dac))
            return None
        
        if (test_cap == "on"):
            sts = 1
        elif (test_cap == "off"):
            sts = 0
        else:
            print("FEMB_CONFIG_BASE--> {} is an invalid test capacitor setting".format(test_cap))
            return None
            
        if (base == "200mV"):
            snc = 1
        elif (base == "900mV"):
            snc = 0
        else:
            print("FEMB_CONFIG_BASE--> {} is an invalid baseline setting".format(base))
            return None
            
        if (buffer == "on"):
            sbf = 1
        elif (buffer == "off"):
            sbf = 0
        else:
            print("FEMB_CONFIG_BASE--> {} is an invalid buffer setting".format(buffer))
            return None
            
        sdac = int(dac_value)
        if ((sdac < 0) or (sdac > 32)):
            print("FEMB_CONFIG_BASE--> {} is an invalid internal DAC setting".format(sdac))
            return None
          
        if ((monitor_ch == None) or (monitor_ch == "None") or (monitor_ch == "off")):
            smn = 0
        elif (acdc == "on"):
            smn = 1
        else:
            print("FEMB_CONFIG_BASE--> {} is an invalid channel monitor setting".format(monitor_ch))
            return None
            
        if ((smn == 1) and (sdacsw2 == 1)):
            print("FEMB_CONFIG_BASE--> You're trying to turn on the monitor and SDACSW2!  Read the manual on why you shouldn't!  Turning the monitor off")
            smn = 0
            
        if (acdc == "dc"):
            sdc = 0
        elif (acdc == "ac"):
            sdc = 1
        else:
            print("FEMB_CONFIG_BASE--> {} is an invalid ac/dc setting".format(acdc))
            return None
            
        if ((monitor_param == None) or (monitor_param == "None") or (monitor_param == "off")): stb = 0
        elif monitor_param == "temp": stb = 2
        elif monitor_param == "bandgap": stb = 3
        else:
            print("FEMB_CONFIG_BASE--> {} is an invalid parameter monitoring setting".format(monitor_param))
            return None
            
        if ((s16 == None) or (s16 == "None") or (s16 == "off")):
            s16 = 0
        elif (acdc == "on"):
            s16 = 1
        else:
            print("FEMB_CONFIG_BASE--> {} is an invalid Channel 16 filter setting".format(s16))
            return None
            
        if (chn != None):
            self.feasic_regs = self.set_fe_chn(chip, chn, sts=sts, snc=snc, sg=sg, st=st, smn=smn, sbf=sbf)
        else:
            self.feasic_regs = self.FE_Regs.set_fe_board(sts=sts, snc=snc, sg=sg, st=st, smn=0, sbf=sbf, 
                       slk = slk, stb = stb, s16=s16, slkh=slkh, sdc=sdc, sdacsw2=sdacsw2, sdacsw1=sdacsw1, sdac=sdac)