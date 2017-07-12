"""
Interface to Keysight 33600A Function Generator
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

VMIN=-0.3000001
VMAX=2.0000001

class Keysight_33600A(object):
    """
    Interface to Keysight 33600A Function Generator
    """

    def __init__(self,filename,sourceNumber=None):
        """
        filename is the file descriptor for the usbtmc object like /dev/usbtmc0
        sourceNumber is either 1, 2, or None. if None, get from envvar FUNCGENSOURCENUM
        """

        self.filename = filename
        if sourceNumber != 1 and sourceNumber != 2:
          try:
            sourceNumber = int(os.environ["FUNCGENSOURCENUM"])
          except KeyError:
            print("Error in Rigol Function Generator Setup: Environment variable FUNCGENSOURCENUM not found. Should be either 1 or 2")
            sys.exit(1)
          except ValueError:
            print("Error in Rigol Function Generator Setup: Environment variable FUNCGENSOURCENUM='{}'. Should be either 1 or 2".format(os.environ["FUNCGENSOURCENUM"]))
            sys.exit(1)
          if sourceNumber != 1 and sourceNumber != 2:
            print("Error in Rigol Function Generator Setup: Environment variable FUNCGENSOURCENUM='{}'. Should be either 1 or 2".format(sourceNumber))
            sys.exit(1)
        print("Using Keysight 33600A at {} Channel {}".format(filename,sourceNumber))
        self.sourceNumber = sourceNumber
        self.sourceString = "source{}".format(sourceNumber)
        self.outputString = "output{}".format(sourceNumber)

    def writeCommand(self,command):
        """
        Writes a command string to the function generator
        """
        #print("Writing command '{}'".format(command))
        try:
            with open(self.filename,'w') as wfile:
                wfile.write(command)
                time.sleep(0.1)
        except BrokenPipeError as e:
            print("Error while writing to function generator USB-TMC, reraising...")
            raise e

    def stop(self):
        """
        Stops output
        """
        command = self.outputString+" OFF"
        #print(command)
        self.writeCommand(command)

    def startSin(self,freq,amp,offset):
        """
        Starts a sin wave with
        freq freqeuncy in Hz
        amp amplitude in V
        offset offset in V
        """
        if offset - amp < VMIN or offset + amp > VMAX:
            raise Exception("Voltage swings outside of {} to {} V, may damage things, amp={} offset={}".format(VMIN,VMAX,amp,offset))
        peakToPeak = amp*2
        command = self.sourceString+":apply:sin {},{},{}".format(freq,peakToPeak,offset)
        #print(command)
        self.writeCommand(command)

    def startDC(self,voltage):
        """
        Starts a DC signal
        voltage in V
        """
        if voltage < VMIN or voltage > VMAX:
            raise Exception("Voltage swings outside of {} to {} V, may damage things".format(VMIN,VMAX))
        freq = 1000
        amplitude = 0.01
        offset = voltage
        command = self.sourceString+":apply:dc {},{},{}".format(freq,amplitude,offset)
        #print(command)
        self.writeCommand(command)

    def startRamp(self,freq,minV,maxV):
        """
        Starts a ramp (triangular wave) with
        freq freqeuncy in Hz
        minV minimum voltage in V
        maxV maximum voltage in V
        """
        if minV < VMIN or minV > VMAX:
            raise Exception("Voltage swings outside of {} to {} V, may damage things, minV={}, maxV={}".format(VMIN,VMAX,minV,maxV))
        if maxV < VMIN or maxV > VMAX:
            raise Exception("Voltage swings outside of {} to {} V, may damage things, minV={}, maxV={}".format(VMIN,VMAX,minV,maxV))
        if minV >= maxV:
            raise Exception("Ramp minVoltage {} >= maxVoltage {}".format(minV,maxV))
        peakToPeak = (maxV-minV)
        offset = 0.5*(maxV+minV)
        command = self.sourceString+":apply:triangle {},{},{}".format(freq,peakToPeak,offset)
        #print(command)
        self.writeCommand(command)
        

def main():

    from ..configuration.argument_parser import ArgumentParser
    from ..configuration import CONFIG
    parser = ArgumentParser(description="Control Keysight 33600A Function Generator. If run without arguments, stops generator.")
    parser.add_argument("--dc",help="Start DC signal, argument is voltage [V]",type=float,default=-99999)
    parser.add_argument("--sin",help="Start sin signal",action='store_true')
    parser.add_argument("--ramp",help="Start ramp signal",action='store_true')
    parser.add_argument("--offset",help="Set voltage offset [V], default=0.75",type=float,default=0.75)
    parser.add_argument("--amplitude",help="Set voltage amplitude [V], default=0.25",type=float,default=0.25)
    parser.add_argument("--frequency",help="Set signal frequency [Hz], default=100000",type=float,default=100000)
    args = parser.parse_args()

    if(args.dc > -100 and args.sin):
        print("Error: You may not run DC and sin at the same time, exiting.")
        sys.exit(1)
    if(args.dc > -100 and args.ramp):
        print("Error: You may not run DC and ramp at the same time, exiting.")
        sys.exit(1)
    if(args.sin and args.ramp):
        print("Error: You may not run sin and ramp at the same time, exiting.")
        sys.exit(1)

    config = CONFIG()
    funcgen = Keysight_33600A(config.FUNCGENPATH,config.FUNCGENSOURCE)

    funcgen.stop()
    
    if args.ramp:
      funcgen.startRamp(args.frequency,args.offset-args.amplitude,args.offset+args.amplitude)
    elif args.sin:
      funcgen.startSin(args.frequency,args.amplitude,args.offset)
    elif args.dc > -100:
      funcgen.startDC(args.dc)

#  with open("/dev/usbtmc0",'w') as wfile:
#
#    #wfile.write("*IDN?")
#    #wfile.write(":SOURce1:FUNCtion DC")
#    #wfile.write(":SOURce1:FUNCtion SINusoid")
#    #wfile.write(":SOURce1:FREQuency 1500")
#    #wfile.write(":SOURce1:VOLTage:AMPLitude 0.1")
#    #wfile.write(":SOURce1:VOLTage:OFFSet 0.25")
#    #wfile.write(":OUTPut1:STATe OFF")
  
