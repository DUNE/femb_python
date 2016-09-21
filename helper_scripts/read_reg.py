#!/usr/bin/env python33

import sys 
import string
from femb_udp_cmdline import FEMB_UDP

if len(sys.argv) != 2 :
	print 'Invalid # of arguments, usage python read_reg <reg #>'
	sys.exit(0)

femb = FEMB_UDP()
regVal = int( sys.argv[1] )
if (regVal < 0) or (regVal > femb.MAX_REG_NUM):
	print 'Invalid register number'
        sys.exit(0)
val = femb.read_reg(regVal)
print str(regVal) + "\t" + str(hex(val))
