#!/usr/bin/env python33

"""
Just like adcTest_P1single, just with self.COLD = True
"""

from femb_python.configuration.configs import adcTest_P1single

class FEMB_CONFIG(adcTest_P1single.FEMB_CONFIG):
    def __init__(self):
        super().__init__()
        self.COLD = True
