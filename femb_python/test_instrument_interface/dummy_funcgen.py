"""
Dummy function generator interface
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

class DummyFuncGen(object):
    """
    Interface to Keysight 33600A Function Generator
    """

    def __init__(self,filename,sourceNumber=None):
        """
        filename is the file descriptor for the usbtmc object like /dev/usbtmc0
        sourceNumber is either 1, 2, or None. if None, get from envvar FUNCGENSOURCENUM
        """

        pass

    def writeCommand(self,command):
        """
        Writes a command string to the function generator
        """
        pass

    def stop(self):
        """
        Stops output
        """
        pass

    def startSin(self,freq,amp,offset):
        """
        Starts a sin wave with
        freq freqeuncy in Hz
        amp amplitude in V
        offset offset in V
        """
        pass

    def startDC(self,voltage):
        """
        Starts a DC signal
        voltage in V
        """
        pass

    def startRamp(self,freq,minV,maxV):
        """
        Starts a ramp (triangular wave) with
        freq freqeuncy in Hz
        minV minimum voltage in V
        maxV maximum voltage in V
        """
        pass
        

def main():

        pass
