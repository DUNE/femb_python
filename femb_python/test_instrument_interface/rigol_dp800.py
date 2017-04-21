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

VMIN=0.
VMAX=3.5

class RigolDP800(object):
    """
    Interface to Rigol DP800 Power Supply
    """

    def __init__(self,filename):
        """
        filename is the file descriptor for the usbtmc object like /dev/usbtmc0
        """

        self.filename = filename
        print("Using Rigol DP800 at {}".format(filename))

    def writeCommand(self,command):
        """
        Writes a command string to the power supply
        """
        #print("Writing command '{}'".format(command))
        with open(self.filename,'w') as wfile:
            wfile.write(command)

    def on(self):
        """
        Turns on all channels
        """
        print("Turning on power!")
        time.sleep(0.05)
        self.writeCommand("OUTPut CH1,ON")
        self.writeCommand("OUTPut CH2,ON")
        self.writeCommand("OUTPut CH3,ON")
        time.sleep(0.05)

    def off(self):
        """
        Turns off all channels
        """
        print("Turning off power!")
        time.sleep(0.05)
        self.writeCommand("OUTPut CH1,OFF")
        self.writeCommand("OUTPut CH2,OFF")
        self.writeCommand("OUTPut CH3,OFF")
        time.sleep(0.05)

def main():

    from ..configuration.argument_parser import ArgumentParser
    from ..configuration import CONFIG
    parser = ArgumentParser(description="Control Rigol DP800 power supply. If run without arguments, turns off all channels.")
    parser.add_argument("--turnOn",help="Turn on all channels",action='store_true')
    args = parser.parse_args()

    config = CONFIG()
    ps = RigolDP800(config.POWERSUPPLYPATH)
    
    if args.turnOn:
      ps.on()
    else:
      ps.off()

#  with open("/dev/usbtmc0",'w') as wfile:
#
#    #wfile.write("*IDN?")
#    #wfile.write(":SOURce1:FUNCtion DC")
#    #wfile.write(":SOURce1:FUNCtion SINusoid")
#    #wfile.write(":SOURce1:FREQuency 1500")
#    #wfile.write(":SOURce1:VOLTage:AMPLitude 0.1")
#    #wfile.write(":SOURce1:VOLTage:OFFSet 0.25")
#    #wfile.write(":OUTPut1:STATe OFF")
  
