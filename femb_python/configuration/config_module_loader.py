"""
Loads a configuration class from the configuration module given in an
environment variable
"""
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
import pkg_resources
import os
import importlib
import sys
import os.path, pkgutil
from . import configs as configs

#PKGNAME="femb_python"
#PKGCONFIGPREFIX = "configuration"
#VARNAME="FEMB_CONFIG"

class CONFIGURATION_MODULE_LOADER(object):
  """
  Loads the femb configuration file using the environmental variable
  """

  def __init__(self,varname="FEMB_CONFIG"):
      self.varname=varname

  def load(self):
      """
      Get the environment variable name, load the config module, and return its FEMB_CONFIG class
      """
      if not self.varname in os.environ:
          print("Error: Environment variable '{}' not found. Standard options are: \n{}".format(self.varname,self.get_standard_configurations()))
	  sys.exit(1)
      config_name = os.environ[self.varname]
      print("Using configuration environment var {}={}".format(self.varname,config_name))
      module = self.config_file_finder(config_name)
      try:
        return module.FEMB_CONFIG
      except AttributeError:
          print("Error: Config module '{}' doesn't contain the class FEMB_CONFIG".format(config_name))
	  sys.exit(1)
  
  def config_file_finder(self,requestedModuleName):
      """
      Load the given modulename from the configs directory
      """
      moduleStr = "."+requestedModuleName
      module = importlib.import_module(moduleStr,"femb_python.configuration.configs")
#      try:
#          module = importlib.import_module(moduleStr,"femb_python.configuration.configs")
#      except ImportError as e:
#          print("Error: Couldn't find config module '{}' that was listed in environment var {}. Standard options are: \n{}".format(requestedModuleName,self.varname,self.get_standard_configurations()))
#	  raise e
#	  sys.exit(1)
#      except KeyError as e:
#          print("Error: Couldn't find config module '{}' that was listed in environment var {}. Standard options are: \n{}".format(requestedModuleName,self.varname,self.get_standard_configurations()))
#          raise e
#	  sys.exit(1)
      return module
  
  def get_standard_configurations(self):
      pkgpath = os.path.dirname(configs.__file__)
      standard_file_list = [name for _, name, _ in pkgutil.iter_modules([pkgpath])]
      return standard_file_list
