#!/usr/bin/env python33

"""
Just like adcTest_P1single, just with self.COLD = True
"""

from femb_python.configuration.configs import adcTest_P1single

class FEMB_CONFIG(adcTest_P1single.FEMB_CONFIG):
    def __init__(self,exitOnError=True):
        super().__init__(exitOnError=exitOnError)
        self.COLD = True
        self.REG_LATCHLOC1_4_data_1MHz = 0x4
        self.REG_LATCHLOC5_8_data_1MHz = 0x0
        self.REG_CLKPHASE_data_1MHz = 0xfffc0001
