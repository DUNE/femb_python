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
from ..configuration import CONFIG
from ..configuration.argument_parser import ArgumentParser

def main():
  parser = ArgumentParser(description="Select FEMB channel")
  parser.add_argument("asic",help="ASIC number (start from 0)")
  parser.add_argument("channel",help="Channel number (0-16)")
  parser.add_argument("-m","--highSpeedMode",help="High-speed mode",action="store_true")
  parser.add_argument("-s","--singleChannelMode",help="Single-channel mode (some boards do this if not in high speed mode; may cause a crash)",action="store_true")

  args = parser.parse_args()

  asicVal = args.asic
  channelVal = args.channel
  hsmode = 1
  if args.highSpeedMode:
      hsmode = 0

  femb_config = CONFIG()
  
  asicVal = int( sys.argv[1] )
  if (asicVal < 0) or (asicVal >= femb_config.NASICS):
      print('Error: Invalid ASIC number')
      sys.exit(0)
  
  channelVal = int( sys.argv[2] )
  if (channelVal < 0) or (channelVal > 15):
      print('Error:Invalid channel number')
      sys.exit(0)
  
  print("ASIC value is " + str(asicVal))
  print("Channel value is " + str( channelVal))
  print("High-speed mode: " + str(args.highSpeedMode))
  if args.singleChannelMode:
    print("Using single channel mode")
    femb_config.selectChannel(asicVal,channelVal,hsmode,singlechannelmode=1)
  else:
    femb_config.selectChannel(asicVal,channelVal,hsmode)
