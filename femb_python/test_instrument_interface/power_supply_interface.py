"""
Interface to Rigol DP800 Power Supply
"""
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import

from builtins import int
from builtins import open
from future import standard_library
standard_library.install_aliases()
import time
from .rigol_dp832 import RigolDP832

class Power_Supply(object):
    """
    Interface to Rigol DP832 Power Supply
    """

    #Creates a DriverUSBTMC object, because that read/write method seems to be more reliable than the original one here
    def __init__(self, config):
        self.interface = None
        self.config = config
        valid_supplies = list(self.config._sections["POWER_SUPPLIES"].keys())
        for i in valid_supplies:
            name = self.config["POWER_SUPPLIES"][i]
            if (name == "RIGOL DP832"):
                self.interface = RigolDP832()
                
            if (self.interface.powerSupplyDevice != None):
                self.name = name
                print("power_supply_interface --> Found {}!".format(name))
                break
            else:
                self.interface = None
                    
        if (self.interface == None):
            print("power_supply_interface --> No valid power supply found!")

    def on(self, **kwargs):
        if (self.interface == None):
            print("power_supply_interface --> No valid power supply found!")
        else:
            wait = False
            channels = kwargs["channels"]
            if type(channels) is int:
                status = self.get_on_off(channels)
                if (status == True):
                    print("power_supply_interface --> Channel {} is already on!".format(channels))
                else:
                    resp = self.interface.on(**kwargs)
                    if (resp == True):
                        wait = True
                
            elif type(channels) is list:
                status = []
                for i in channels:
                    status.append(self.get_on_off(channel = i))
                   
                if False in status:
                    resp = self.interface.on(**kwargs)
                    if (resp == True):
                        wait = True
                else:
                    print("power_supply_interface --> All channels are already on!")
                       
            else:
                print("power_supply_interface --> Channel input should be a list or int, it's a {}".format(type(channels)))
                       
            if (wait == True):
                time.sleep(5)

    def off(self, **kwargs):
        if (self.interface == None):
            print("power_supply_interface --> No valid power supply found!")
        else:
            return (self.interface.off(**kwargs))
               
    def get_on_off(self, **kwargs):
        if (self.interface == None):
            print("power_supply_interface --> No valid power supply found!")
        else:
            return (self.interface.get_on_off(**kwargs))
        
    #Set all useful parameters of a channel.  Will ignore setting parameters that were not explicitly passed as arguments.
    def set_channel(self, **kwargs):
        if (self.interface == None):
            print("power_supply_interface --> No valid power supply found!")
        else:
            return (self.interface.set_channel(**kwargs))
                
    #Returns array of 3 numbers: Voltage, Current and Power
    def measure_params(self,**kwargs):
        if (self.interface == None):
            print("power_supply_interface --> No valid power supply found!")
        else:
            return (self.interface.measure_params(**kwargs))
            
    def beep(self,**kwargs):
        if (self.interface == None):
            print("power_supply_interface --> No valid power supply found!")
        else:
            return (self.interface.beep(**kwargs))