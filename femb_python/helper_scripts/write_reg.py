from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import
from builtins import int
from future import standard_library
standard_library.install_aliases()
import sys 
from ..femb_udp import FEMB_UDP

def main():
  if len(sys.argv) != 3 :
      print( 'Invalid # of arguments, usage python write_reg <reg #> <data>')
      sys.exit(0)
  
  femb = FEMB_UDP()
  regVal = int(sys.argv[1])
  if (regVal < 0) or (regVal > femb.MAX_REG_NUM):
      print( 'Invalid register number')
      sys.exit(0)
  
  dataVal = sys.argv[2]
  try:
    dataVal = int(dataVal)
  except:
    dataVal = int(dataVal,16)
  if (dataVal < 0) or (dataVal > 0xFFFFFFFF):
      print( 'Invalid register value')
      sys.exit(0)
  
  femb.write_reg(regVal,dataVal)
