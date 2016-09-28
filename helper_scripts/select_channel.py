#!/usr/bin/python3.4
import sys
from femb_config import FEMB_CONFIG
femb_config = FEMB_CONFIG()

print "BEGIN CHANNEL SELECT"

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

print "END CHANNEL SELECT"
