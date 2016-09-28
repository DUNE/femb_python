import sys 
import string
import time
from femb_udp_cmdline import FEMB_UDP

class FEMB_CONFIG:

    #__INIT__#
    def __init__(self):
        print "FEMB CONFIG ERROR: Configuration file has not been specified! Run setup.py to specify configuration file. Program will terminate!"
        sys.exit(0)
