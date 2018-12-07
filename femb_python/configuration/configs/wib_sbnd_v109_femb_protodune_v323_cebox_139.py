#!/usr/bin/env python33

"""
Modified configuration for cold electronic box 139 using protoDUNE FEMB firmware v323
"""

from femb_python.configuration.configs import wib_sbnd_v109_femb_protodune_v323

class FEMB_CONFIG(wib_sbnd_v109_femb_protodune_v323.FEMB_CONFIG):

    def __init__(self,exitOnError=True):
        super().__init__()

        self.CLKSELECT_val_RT = 0xF7
        self.CLKSELECT2_val_RT = 0xF7
        print("CLKSELECT at RT:",self.CLKSELECT_val_RT,self.CLKSELECT2_val_RT)
        self.CLKSELECT_val_CT = 0xFF
        self.CLKSELECT2_val_CT = 0xFF
        print("CLKSELECT at CT:",self.CLKSELECT_val_CT,self.CLKSELECT2_val_CT)
