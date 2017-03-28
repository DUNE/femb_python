from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals
from __future__ import absolute_import
from builtins import range
from future import standard_library
standard_library.install_aliases()
from ...femb_udp import FEMB_UDP
from ...test_instrument_interface import RigolDG4000
from ...write_root_tree import WRITE_ROOT_TREE
import time
import datetime
import glob
from uuid import uuid1 as uuid
import numpy
import matplotlib.pyplot as plt
import ROOT
from .collect_data import COLLECT_DATA 
from .static_tests import STATIC_TESTS
from .dynamic_tests import DYNAMIC_TESTS

def main():
    from ...configuration.argument_parser import ArgumentParser
    from ...configuration import CONFIG
    ROOT.gROOT.SetBatch(True)
    parser = ArgumentParser(description="Runs ADC tests")
    parser.addNPacketsArgs(False,100)
    args = parser.parse_args()
  
    config = CONFIG()

    collect_data = COLLECT_DATA(config,args.nPackets)
    static_tests = STATIC_TESTS(config)
    dynamic_tests = DYNAMIC_TESTS(config)
    startDateTime = datetime.datetime.now().replace(microsecond=0).isoformat()

    #for offset in range(-1,16):
    for offset in [-1,0]:
      if offset <=0:
        config.configAdcAsic(enableOffsetCurrent=0,offsetCurrent=0)
      else:
        config.configAdcAsic(enableOffsetCurrent=1,offsetCurrent=offset)
      for iChip in range(config.NASICS):
          fileprefix = "adcTestData_{}_chip{}_offset{}".format(startDateTime,iChip,offset)
          collect_data.getData(fileprefix,iChip,adcOffset=offset)
          static_fns = list(glob.glob(fileprefix+"_functype3_*.root"))
          assert(len(static_fns)==1)
          static_fn = static_fns[0]
          static_tests.analyzeLinearity(static_fn)
          dynamic_tests.analyze(fileprefix)
