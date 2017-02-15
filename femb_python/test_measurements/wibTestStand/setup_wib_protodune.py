import sys
import string
from subprocess import call
from time import sleep
import os
import ntpath
import glob
import struct

def main():

    from femb_python.configuration.femb_config_wib_protodune import FEMB_CONFIG
    femb_config = FEMB_CONFIG()
    femb_config.initWibRCE()
    femb_config.initWibUDP()

if __name__ == '__main__':
    main()
