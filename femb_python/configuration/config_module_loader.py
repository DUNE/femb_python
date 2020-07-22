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
import json
import getpass
import os.path, pkgutil
from . import configs as configs
import configparser

#PKGNAME="femb_python"
#PKGCONFIGPREFIX = "configuration"
#VARNAME="FEMB_CONFIG"

def getDefaultDirectory():
    try:
        femb_config = os.environ["FEMB_CONFIG"]  # required
    except KeyError:
        print( "ERROR RUNPOLICY - Please set the environment variable FEMB_config" )
        return None

    # Check out the data disk situation and find the most available disk
    freedisks = list()
    datadisks=["/tmp"]
    hostname = os.uname()[1]
    if (hostname.startswith("hoth") or hostname.startswith("hunk")):
        datadisks = ["/dsk/1", "/dsk/2"]
    for dd in datadisks:
        stat = os.statvfs(dd)
        MB = stat.f_bavail * stat.f_frsize >> 20
        freedisks.append((MB, dd))
    freedisks.sort()
    lo_disk = freedisks[0][1]

    user = getpass.getuser()
    if ("user" == "oper"):
        datadisk = "{}/data".format(lo_disk)
    else:
        datadisk = "{}/tmp".format(lo_disk)
        
    step2 = os.path.join(datadisk,user,femb_config)
    step1 = os.path.join(datadisk,user)
    
    for i in [step1,step2]:
        if not os.path.exists(i):
            os.makedirs(i)
    
    return step2

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
          module = self.config_file_finder_ini(config_name)
          try:
              print("Found INI file for {}".format(module['DEFAULT']['NAME']))
              return module
          except:
              print("Error: Config module '{}' doesn't contain the class FEMB_CONFIG, no INI file either".format(config_name))
              sys.exit(1)
          
  def config_file_finder_ini(self,requestedModuleName):
      config = configparser.ConfigParser()
      #This returns the directory of the file we're currently in (config_module_loader.py), NOT the working directory that launched this from command line
      current_dir = os.path.dirname(os.path.abspath(__file__))
      config.read('{}/configs/{}.ini'.format(current_dir,requestedModuleName))
      return config
  
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
#         raise e
#         sys.exit(1)
#      except KeyError as e:
#          print("Error: Couldn't find config module '{}' that was listed in environment var {}. Standard options are: \n{}".format(requestedModuleName,self.varname,self.get_standard_configurations()))
#          raise e
#         sys.exit(1)
      return module
  
  def get_standard_configurations(self):
      pkgpath = os.path.dirname(configs.__file__)
      standard_file_list = [name for _, name, _ in pkgutil.iter_modules([pkgpath])]
      return standard_file_list