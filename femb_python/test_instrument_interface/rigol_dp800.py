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

    def __init__(self,filename,channelNumbers):
        """
        filename is a the path to a usbtmc object like /dev/usbtmc0.

        channelNumbers is a list of
        the channels to turn on e.g. ["CH1","CH2","CH3"]. All three channels
        are turned off no matter what POWERSUPPLYCHANNELS is set to.
        """

        self.filename = filename
        print("Using Rigol DP800 at {}".format(self.filename))
        if type(channelNumbers) != list:
            print("Error: RigolDP800 channelNumbers argument is not list: '{}', exiting.".format(channelNumbers))
            sys.exit(1)
        self.channels = channelNumbers
        print("Configured to turn on these power supply channels: {}".format(self.channels))

    def writeCommand(self,command):
        """
        Writes a command string to the power supply
        """
        #print("Writing command '{}'".format(command))
        with open(self.filename,'w') as wfile:
            wfile.write(command)

    def on(self):
        """
        Turns on all channels listed in configuration file
        """
        print("Turning on power!")
        time.sleep(0.05)
        for channel in self.channels:
            self.writeCommand("OUTPut {},ON".format(channel))
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
    parser.add_argument("--turnOn",help="Turn on all channels listed in configuration file",action='store_true')
    parser.add_argument("--turnOff",help="Turn off all channels",action='store_true')
    args = parser.parse_args()

    config = CONFIG()
    ps = RigolDP800(config)
    
    if args.turnOn and args.turnOff:
        print("Error: Can't turn on and turn off at the same time")
        sys.exit(1)
    elif args.turnOn:
      ps.on()
    elif args.turnOff:
      ps.off()
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
  
