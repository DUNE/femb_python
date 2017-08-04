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

class DummyPowerSupply(object):
    """
    Dummy power supply interface
    """

    def __init__(self,filename,channelNumbers,pauseBetweenChannels=2.):
        """
        filename is a the path to a usbtmc object like /dev/usbtmc0.

        channelNumbers is a list of
        the channels to turn on e.g. ["CH1","CH2","CH3"]. All three channels
        are turned off no matter what POWERSUPPLYCHANNELS is set to.

        pauseBetweenChannels is the amount of time in seconds to pause
            between turning on or off each channel in the list
        """

        pass

    def writeCommand(self,command):
        """
        Writes a command string to the power supply
        """

        pass

    def on(self):
        """
        Turns on all channels listed in configuration file
        """
        pass

    def off(self):
        """
        Turns off all channels
        """
        pass

def main():

    pass
  
