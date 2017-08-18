#!/usr/bin/env python33

"""
Modified configuration for cold electronic box 018 using protoDUNE FEMB firmware v308
"""

from femb_python.configuration.configs import wib_sbnd_v109_femb_protodune_v308

class FEMB_CONFIG(wib_sbnd_v109_femb_protodune_v308.FEMB_CONFIG):

    def __init__(self,exitOnError=True):
        super().__init__()

        self.CLKSELECT_val_RT = 0xD9
        self.CLKSELECT2_val_RT = 0x26
        self.CLKSELECT_val_CT = 0x83
        self.CLKSELECT2_val_CT = 0xFF
