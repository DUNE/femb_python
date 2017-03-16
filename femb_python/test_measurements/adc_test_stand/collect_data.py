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

class COLLECT_DATA(object):
    """
    Collect data for ADC tests
    """

    def __init__(self,config,nPackets):
        """
        config is a femb_python.configuration.CONFIG object
        """
        self.config = config
        self.femb = FEMB_UDP()
        self.funcgen = RigolDG4000(config.FUNCGENPATH,config.FUNCGENSOURCE)
        self.settlingTime = 0.1 # second
        self.maxTries = 1000
        self.fitMinV = 0.5
        self.fitMaxV = 2.5
        self.nPackets = nPackets
        self.nBits = 12

    def getData(self,outPrefix,iChip):
        """
        Creates data files starting with outPrefix for iChip for ramp and sin inputs
        """

        fig, ax = plt.subplots(figsize=(8,8))
        codeHists = []
        bitHists = []
        freqList = [6.2365e4,1.234e5,5.13587e5,9.515125e5]
        xLow = 0.3
        xHigh = 2.7
        freq = 734
        offsetV = (xLow + xHigh)*0.5
        amplitudeV = (xHigh - xLow)*0.5
        ## Ramp
        self.funcgen.startRamp(freq,xLow,xHigh)
        time.sleep(self.settlingTime)
        self.dumpWaveformRootFile(outPrefix,3,freq,offsetV,amplitudeV,self.femb.MAX_NUM_PACKETS)
        ## Sin
        amplitudeV -= amplitudeV*0.1
        for freq in freqList:
          self.funcgen.startSin(freq,amplitudeV,offsetV)
          time.sleep(self.settlingTime)
          self.dumpWaveformRootFile(outPrefix,2,freq,offsetV,amplitudeV,self.femb.MAX_NUM_PACKETS)
        self.funcgen.stop()

    def dumpWaveformRootFile(self,fileprefix,functype,freq,offsetV,amplitudeV,nPackets=None):
        filename = "{}_functype{}_freq{:.3f}_offset{:.3f}_amplitude{:.3f}.root".format(fileprefix,functype,freq,offsetV,amplitudeV)
        if not nPackets:
          nPackets = self.nPackets
        if functype > 1:
            nPackets = 100
        wrt = WRITE_ROOT_TREE(self.config,filename,nPackets)
        wrt.funcType = functype
        wrt.funcFreq = freq
        wrt.funcOffset = offsetV
        wrt.funcAmp = amplitudeV
        wrt.record_data_run()

def main():
    from ...configuration.argument_parser import ArgumentParser
    from ...configuration import CONFIG
    ROOT.gROOT.SetBatch(True)
    parser = ArgumentParser(description="Collects data for ADC tests")
    parser.addNPacketsArgs(False,100)
    #parser.add_argument("outfilename",help="Output root file name")
    args = parser.parse_args()
  
    config = CONFIG()

    collect_data = COLLECT_DATA(config,args.nPackets)
  
    startDateTime = datetime.datetime.now().replace(microsecond=0).isoformat()
    for iChip in range(config.NASICS):
        fileprefix = "adcTestData_{}_chip{}".format(startDateTime,iChip)
        collect_data.getData(fileprefix,iChip)
