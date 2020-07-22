# -*- coding: utf-8 -*-
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
"""
Created on Wed Mar 13 14:52:21 2019

@author: eraguzin
"""
class I2C_comm(object):
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
            
    #chips = "all", returns power information for all chips
    #chips = 0, returns power information for chip 0
    #chips = [0,2,3], returns power information for chips 0, 2, and 3, in that order
    def PCB_power_monitor(self, chips):
        result = []
        if (isinstance(chips, list)):
            for i in chips:
                device = int(self.config["REGISTERS"]["REG_INA226_VDDA_{}".format(i)], 16)
                result.append(self.get_PCB_power_info(device))
                device = int(self.config["REGISTERS"]["REG_INA226_VDDP_{}".format(i)], 16)
                result.append(self.get_PCB_power_info(device))
        elif (chips == "all"):
            for chips in range(int(self.config["DEFAULT"]["NASIC_MIN"]), int(self.config["DEFAULT"]["NASIC_MAX"]) + 1, 1):
                device = int(self.config["REGISTERS"]["REG_INA226_VDDA_{}".format(i)], 16)
                result.append(self.get_PCB_power_info(device))
                device = int(self.config["REGISTERS"]["REG_INA226_VDDP_{}".format(i)], 16)
                result.append(self.get_PCB_power_info(device))
        elif (isinstance(chips, int)):
            device = int(self.config["REGISTERS"]["REG_INA226_VDDA_{}".format(chips)], 16)
            result.append(self.get_PCB_power_info(device))
            device = int(self.config["REGISTERS"]["REG_INA226_VDDP_{}".format(chips)], 16)
            result.append(self.get_PCB_power_info(device))
        else:
            print("config_functions --> input to PCB_power_monitor is not a number, list or 'all'!")
            
        return result
            
    def get_PCB_power_info(self, device):
        dev_address = device
        shunt_voltage = round(self.INA226_read(dev_address, 1, 2) * 2.5E-6, 6)
        bus_voltage = round(self.INA226_read(dev_address, 2, 2) * 0.00125, 3)
        current = round(shunt_voltage / float(self.config["DEFAULT"]["PCB_SHUNT_RESISTOR"]), 3)
        return [shunt_voltage, bus_voltage, current]
        
    def INA226_write(self, device_address, reg_address, high_byte, low_byte):
        #Because of how the FPGA does I2C, you need to swap the high and low bytes going in and coming back out
        check_value = (high_byte << 8) + low_byte
        low_byte_shift = low_byte << 8
        value = low_byte_shift + high_byte
        self.femb_udp.write_reg(int(self.config["REGISTERS"]["REG_I2C_VALUE"]), value)
        
        device_reg = (device_address << 16) + (reg_address << 8) + 2
        self.femb_udp.write_reg(int(self.config["REGISTERS"]["REG_I2C_CONFIG"]), device_reg)
        
        self.femb_udp.write_reg(int(self.config["REGISTERS"]["REG_I2C_ACTION"]), 1)
        self.femb_udp.write_reg(int(self.config["REGISTERS"]["REG_I2C_ACTION"]), 0)
        
        #The first 4 bits of the INA config register is reserved and can't be changed
        check = self.INA226_read(device_address, reg_address, 2) & 0x0FFF
        
        if (check != check_value):
            print("config_functions --> I2C Power chip was not correctly written to!  Wanted {}, recieved {}".format(hex(check_value), hex(check)))
        else:
            return True
            
    def INA226_read(self, device_address, reg_address, num_bytes):
        device_reg = (device_address << 16) + (reg_address << 8) + 0
        self.femb_udp.write_reg(int(self.config["REGISTERS"]["REG_I2C_CONFIG"]), device_reg)
        self.femb_udp.write_reg(int(self.config["REGISTERS"]["REG_I2C_ACTION"]), 1)
        self.femb_udp.write_reg(int(self.config["REGISTERS"]["REG_I2C_ACTION"]), 0)
        
        device_reg = (device_address << 16) + (reg_address << 8) + 2
        self.femb_udp.write_reg(int(self.config["REGISTERS"]["REG_I2C_CONFIG"]), device_reg)
        self.femb_udp.write_reg(int(self.config["REGISTERS"]["REG_I2C_ACTION"]), 2)
        self.femb_udp.write_reg(int(self.config["REGISTERS"]["REG_I2C_ACTION"]), 0)
        
        #Because of how the FPGA does I2C, you need to swap the high and low bytes going in and coming back out
        resp = self.femb_udp.read_reg(int(self.config["REGISTERS"]["REG_I2C_RESULT"]))
        resp_high = resp >> 8
        resp_low = resp & 0xFF
        resp = ((resp_low << 8) + resp_high)
        return resp