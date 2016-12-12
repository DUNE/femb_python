#!/usr/bin/python3.4
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import
from builtins import int
from builtins import str
from future import standard_library
standard_library.install_aliases()
import sys
from ..configuration import CONFIG, get_env_config_file

def main():
  config_file = get_env_config_file()
  femb_config = CONFIG(config_file)
  
  print("BEGIN CHANNEL SELECT")
  
  if len(sys.argv) != 3 :
      print( 'Invalid # of arguments, usage python select_channel <ASIC #> <channel #>')
      sys.exit(0)
  
  asicVal = int( sys.argv[1] )
  if (asicVal < 0) or (asicVal > 7):
      print( 'Invalid ASIC number')
      sys.exit(0)
  
  channelVal = int( sys.argv[2] )
  if (channelVal < 0) or (channelVal > 15):
      print( 'Invalid channel number')
      sys.exit(0)
  
  print( "ASIC value is " + str(asicVal) )
  print( "Channel value is " + str( channelVal)	)
  femb_config.selectChannel(asicVal,channelVal)
  
  print("END CHANNEL SELECT")
