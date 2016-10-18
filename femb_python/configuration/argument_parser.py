import argparse
from .config_file_finder import get_standard_configuration_dir, get_standard_configurations

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

    def addConfigFileArgs(self,required=False):
        """
        Adds an argument to get a config filename from the command line.
        """
        self.add_argument('-c','--config',required=required,
                            help="Configuration file name. Can be a path or one of the standard configurations, {}, in {}".format(get_standard_configurations(), get_standard_configuration_dir())
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
