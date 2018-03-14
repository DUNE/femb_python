#!/usr/bin/env python33

"""
Configuration for quad EPCS Flash memory tester
"""
import sys 
import time

from femb_python.femb_udp import FEMB_UDP
from femb_python.configuration.config_base import FEMB_CONFIG_BASE

class FEMB_CONFIG(FEMB_CONFIG_BASE):

    #__INIT__#
    def __init__(self):
        #set up UDP interface
        self.femb = FEMB_UDP()

    def initBoard(self):
        print("\nInitializing board\n")

        #check if FEMB register interface is working
        #regVal = self.femb.read_reg(257)
        #print(regVal)
        #if regVal == None:
        #    print("Error!! FEMB register interface is not working.")
        #    print(" Will not initialize FEMB.")       
        #    return
