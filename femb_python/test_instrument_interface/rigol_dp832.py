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
import os
import sys
from .driverUSBTMC import DriverUSBTMC

class RigolDP832(object):
    """
    Interface to Rigol DP832 Power Supply
    """

    #Creates a DriverUSBTMC object, because that read/write method seems to be more reliable than the original one here
    def __init__(self):
        self.powerSupplyDevice = None
        dirList = os.listdir("/dev")
        for fName in dirList:
            if(fName.startswith("usbtmc")):
                device = DriverUSBTMC("/dev/" + fName)
                deviceID = device.getID()
                if(deviceID.startswith(b"RIGOL TECHNOLOGIES,DP832")):
                    print("RigolDP832 --> DC Power Supply found with identification %s" %(deviceID.decode()))
                    self.powerSupplyDevice = device

    def on(self, channels = [1,2,3]):
        if type(channels) is not list:
            if ((channels < 1) or (channels > 3)):
                print("RigolDP832 Error --> Channel needs to be 1, 2, or 3!  {} was given!".format(channels))
                return
            self.powerSupplyDevice.write(":OUTP CH{}, ON".format(channels))
            if (self.get_on_off(channels) != True):
                   print("RigolDP832 Error --> Tried to turn on Channel {} of the Rigol DP832, but it didn't turn on".format(channels))
            
        else:
            for i in channels:
                if ((i < 1) or (i > 3)):
                    print("RigolDP832 Error --> Channel needs to be 1, 2, or 3!  {} was given!".format(i))
                    return
                
            for i in channels:
               self.powerSupplyDevice.write(":OUTP CH{}, ON".format(i))
               if (self.get_on_off(i) != True):
                   print("RigolDP832 Error --> Tried to turn on Channel {} of the Rigol DP832, but it didn't turn on".format(i))

    def off(self, channels = [1,2,3]):
        if type(channels) is not list:
            if ((channels < 1) or (channels > 3)):
                print("RigolDP832 Error --> Channel needs to be 1, 2, or 3!  {} was given!".format(channels))
                return
            self.powerSupplyDevice.write(":OUTP CH{}, OFF".format(channels))
            if (self.get_on_off(channels) != True):
                   print("RigolDP832 Error --> Tried to turn off Channel {} of the Rigol DP832, but it didn't turn off".format(channels))
            
        else:
            for i in channels:
                if ((i < 1) or (i > 3)):
                    print("RigolDP832 Error --> Channel needs to be 1, 2, or 3!  {} was given!".format(i))
                    return
                
            for i in channels:
               self.powerSupplyDevice.write(":OUTP CH{}, OFF".format(i))
               if (self.get_on_off(i) != False):
                   print("RigolDP832 Error --> Tried to turn off Channel {} of the Rigol DP832, but it didn't turn off".format(i))
               
    def get_on_off(self, channel):
        self.powerSupplyDevice.write(":OUTP? CH{}".format(channel))
        resp = self.powerSupplyDevice.read().strip().decode()
        status = None
        if (resp == "ON"):
            status = True
        elif (resp == "OFF"):
            status = False
        return (status)
        
    #Set all useful parameters of a channel.  Will ignore setting parameters that were not explicitly passed as arguments.
    def set_channel(self, channel, voltage = None, current = None, v_limit = None, c_limit = None, vp = None, cp = None):
        if (voltage and current):
            print("RigolDP832 Error --> Can't set both voltage and current for Channel {}".format(channel))
            
        if (voltage):
            if ((voltage > 0) and (voltage < 30)):
                self.powerSupplyDevice.write(":SOUR{}:VOLT {}".format(channel,voltage))
                self.powerSupplyDevice.write(":SOUR{}:VOLT?".format(channel))
                response = float(self.powerSupplyDevice.read().strip().decode())
                if (response != voltage):
                    print("RigolDP832 Error --> Voltage was set to {}, but response is {}".format(voltage, response))
            else:
                print("RigolDP832 Error --> Voltage must be between 0 and 30 Volts, was {}".format(voltage))
            
        if (current):
            if ((current > 0) and (current < 3)):
                self.powerSupplyDevice.write(":SOUR{}:CURR {}".format(channel,current))
                self.powerSupplyDevice.write(":SOUR{}:CURR?".format(channel))
                response = float(self.powerSupplyDevice.read().strip().decode())
                if (response != current):
                    print("RigolDP832 Error --> Current was set to {}, but response is {}".format(current, response))
            else:
                print("RigolDP832 Error --> Current must be between 0 and 3 Amps, was {}".format(current))
                
        if (v_limit):
            if ((v_limit > 0.01) and (v_limit < 33)):
                self.powerSupplyDevice.write(":SOUR{}:VOLT:PROT {}".format(channel,v_limit))
                self.powerSupplyDevice.write(":SOUR{}:VOLT:PROT?".format(channel))
                response = float(self.powerSupplyDevice.read().strip().decode())
                if (response != v_limit):
                    print("RigolDP832 Error --> Voltage protection was set to {}, but response is {}".format(v_limit, response))
            else:
                print("RigolDP832 Error --> OverVoltage protection must be between 0.01 and 30 Volts, was {}".format(v_limit))
                
        if (c_limit):
            if ((c_limit > 0.001) and (c_limit < 3.3)):
                self.powerSupplyDevice.write(":SOUR{}:CURR:PROT {}".format(channel,c_limit))
                self.powerSupplyDevice.write(":SOUR{}:CURR:PROT?".format(channel))
                response = float(self.powerSupplyDevice.read().strip().decode())
                if (response != c_limit):
                    print("RigolDP832 Error --> Current protection was set to {}, but response is {}".format(c_limit, response))
            else:
                print("RigolDP832 Error --> OverCurrent protection must be between 0.001 and 3.3 Amps, was {}".format(c_limit))
                
        if (vp):
            if ((vp == "ON") or (vp == "OFF")):
                self.powerSupplyDevice.write(":SOUR{}:VOLT:PROT:STATE {}".format(channel,vp))
                self.powerSupplyDevice.write(":SOUR{}:VOLT:PROT:STATE?".format(channel))
                response = self.powerSupplyDevice.read().strip().decode()
                if (response != vp):
                    print("RigolDP832 Error --> OverVoltage was set to {}, but response is {}".format(vp, response))
            else:
                print("RigolDP832 Error --> OverVoltage protection must be 'ON' or 'OFF', was {}".format(vp))
                
        if (cp):
            if ((cp == "ON") or (cp == "OFF")):
                self.powerSupplyDevice.write(":SOUR{}:CURR:PROT:STATE {}".format(channel,cp))
                self.powerSupplyDevice.write(":SOUR{}:CURR:PROT:STATE?".format(channel))
                response = self.powerSupplyDevice.read().strip().decode()
                if (response != cp):
                    print("RigolDP832 Error --> OverCurrent was set to {}, but response is {}".format(cp, response))
            else:
                print("RigolDP832 Error --> OverCurrent protection must be 'ON' or 'OFF', was {}".format(cp))
                
    #Returns array of 3 numbers: Voltage, Current and Power
    def measure_params(self,channel):
        if ((channel < 1) or (channel > 3)):
            print("RigolDP832 Error --> Channel needs to be 1, 2, or 3!  {} was given!".format(channel))
            return
        
        self.powerSupplyDevice.write(":MEAS:ALL? CH{}".format(channel))
        response = (self.powerSupplyDevice.read().strip().decode().split(","))
        for i in range(len(response)):
            response[i] = float(response[i])
        return response