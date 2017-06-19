#!/usr/bin/env python33

"""
Configuration for P1 ADC single-chip board on hothdaq4
Mainly uses the Rigol signal generator for now
"""

from femb_python.configuration.configs import adcTest_P1single
from femb_python.test_instrument_interface.rigol_dg4000 import RigolDG4000
from femb_python.test_instrument_interface.rigol_dp800 import RigolDP800

class FEMB_CONFIG(adcTest_P1single.FEMB_CONFIG):

    def __init__(self,exitOnError=True):
        super().__init__(exitOnError=exitOnError)
        self.REG_CLKPHASE_data = 0xfffc0000
        print("Really using:")
        self.FUNCGENINTER = RigolDG4000("/dev/usbtmc0",1)
        self.POWERSUPPLYINTER = RigolDP800("/dev/usbtmc1",["CH2","CH1"]) # turn on CH2 first
