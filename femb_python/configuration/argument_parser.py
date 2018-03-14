from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from builtins import int
from future import standard_library
standard_library.install_aliases()
import argparse

class ArgumentParser(argparse.ArgumentParser):
    """
    Adds some uniformity to argument parsing in the femb_python package
    """
    def __init__(self,*args,**kargs):
        epilogStr = "This command is part of the femb_python package for protoDUNE/SBND cold electronics testing. https://github.com/DUNE/femb_python"
        try:
            kargs['epilog'] += "\n"+epilogStr
        except:
            kargs['epilog'] = epilogStr
        argparse.ArgumentParser.__init__(self,*args,**kargs)

    def addNPacketsArgs(self,required=False,default=None):
        """
        Adds an argument to get a config filename from the command line.
        """
        helpString = "Number of packets to process."
        if default:
          helpString += " default={}".format(default)
        if required:
          helpString += " (required)"
        self.add_argument('-n','--nPackets',required=required, default=default,type=int,
                            help=helpString
                            )

    def addDumpWaveformRootFileArgs(self,required=False,default=None):
        """
        Adds an argument to dump a waveform to a root file
        """
        helpString = "Dump a waveform to a root file."
        if default:
          helpString += " default={}".format(default)
        if required:
          helpString += " (required)"
        self.add_argument('-d','--dumpWaveformRootFile',required=required, default=default,
                            help=helpString
                            )

    def addLoadWaveformRootFileArgs(self,required=False,default=None):
        """
        Adds an argument to load a waveform to a root file
        """
        helpString = "Load a waveform to a root file."
        if default:
          helpString += " default={}".format(default)
        if required:
          helpString += " (required)"
        self.add_argument('-l','--loadWaveformRootFile',required=required, default=default,
                            help=helpString
                            )



def convert_int_literals(instring):
      if instring[:2] == "0x":
        try:
          result = int(instring,16) # it's a hex int
          return result
        except:
          pass
      if instring[:2] == "0o":
        try:
          result = int(instring,8) # it's an octal int
          return result
        except:
          pass
      if instring[:2] == "0b":
        try:
          result = int(instring,2) # it's a binary int
          return result
        except:
          pass
      try:
        result = int(instring) # it's a decimal int
        return result
      except:
        raise Exception("Could not convert '{}' to int".format(instring))
