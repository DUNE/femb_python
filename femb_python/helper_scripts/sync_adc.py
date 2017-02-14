from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from builtins import str
from builtins import hex
from future import standard_library
standard_library.install_aliases()
from ..configuration import CONFIG

def main():
    femb_config = CONFIG()
    femb_config.resetBoard()
    femb_config.initBoard()
    hadToSync, latch1, latch2, phase = femb_config.syncADC()
    femb_config.resetBoard()
    femb_config.initBoard()
    if hadToSync:
      print("Had to sync chips. Please change settings to:")
      print("Latch latency " + str(hex(latch1)) + str(hex(latch2)) + "\tPhase " + str(hex(phase)))
    else:
      print("All chips already sync'd")
