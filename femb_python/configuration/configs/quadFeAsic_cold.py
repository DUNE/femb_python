#!/usr/bin/env python33

"""
Just like quadFeAsic, just with self.COLD = True
"""

from femb_python.configuration.configs import quadFeAsic

class FEMB_CONFIG(quadFeAsic.FEMB_CONFIG):
    def __init__(self):
        super().__init__()
        self.COLD = True
