#!/usr/bin/env python33
import sys
import os
from femb_config import FEMB_CONFIG
femb_config = FEMB_CONFIG()

print "START CONFIG"
femb_config.initBoard()
print "END CONFIG"
