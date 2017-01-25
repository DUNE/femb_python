from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from builtins import int
from future import standard_library
standard_library.install_aliases()

import subprocess
import pkg_resources

PKGNAME="femb_python"

class CPP_FILE_RUNNER(object):
  def __init__(self):
      pass

  def run(self,filename,arguments):
      file_exists = self.exists(filename)
      file_isdir = self.is_dir(filename)
      real_filename = self.filename(filename)
      if not file_exists:
          raise Exception("C++ executable filename doesn't exist: {} at {}".format(filename,real_filename))
      if file_isdir:
          raise Exception("C++ executable filename is a directory: {} at {}".format(filename,real_filename))
      subprocess.call([real_filename]+arguments)
      
  def filename(self,filename):
      """
      filename is the filename relative to the package base 
        directory, the directory with femb_udp.py in it
      """
      return pkg_resources.resource_filename(PKGNAME,filename)
  
  def exists(self,filename):
      """
      filename is the filename relative to the package base 
        directory, the directory with femb_udp.py in it
      """
      real_filename = self.filename(filename)
      return pkg_resources.resource_exists(PKGNAME,filename)

  def is_dir(self,filename):
      """
      filename is the filename relative to the package base 
        directory, the directory with femb_udp.py in it
      """
      return pkg_resources.resource_isdir(PKGNAME,filename)
