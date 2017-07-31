from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import
from builtins import int
from builtins import str
from builtins import hex
from future import standard_library
standard_library.install_aliases()
import sys 
from ..femb_udp import FEMB_UDP

def main():
  if len(sys.argv) != 2 :
      print( 'Invalid # of arguments, usage python read_reg <reg #>')
      sys.exit(0)
  
  femb = FEMB_UDP()
  regVal = int( sys.argv[1] )
  if (regVal < 0) or (regVal > femb.MAX_REG_NUM):
      print( 'Invalid register number')
      sys.exit(0)
  val = femb.read_reg(regVal)
  if val is None:
    print("Error reading register")
  else:
    print("register {0:4} read: {1:#010x} = {1:#034b} = {1:10}".format(regVal,val,val))
