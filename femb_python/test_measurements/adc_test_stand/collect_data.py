from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals
from __future__ import absolute_import
from builtins import range
from future import standard_library
standard_library.install_aliases()
from ...femb_udp import FEMB_UDP
from ...test_instrument_interface import RigolDG4000
from ...test_instrument_interface.keysight_33600A import Keysight_33600A
from ...write_root_tree import WRITE_ROOT_TREE
import time
import datetime
import ROOT

class COLLECT_DATA(object):
    """
    Collect data for ADC tests
    """

    def __init__(self,config,nPackets=None):
        """
        config is a femb_python.configuration.CONFIG object
        """
        self.config = config
        self.femb = FEMB_UDP()
        self.funcgen = self.config.FUNCGENINTER
        self.settlingTime = 0.1 # second
        self.maxTries = 1000
        self.nPackets = nPackets
        self.nBits = 12

    def getData(self,outPrefix,iChip,adcSerial=-1,adcOffset=-2,adcClock=-1,sampleRate=-1):
        """
        Creates data files starting with outPrefix for iChip for ramp and sin inputs
        """

        codeHists = []
        bitHists = []
        xLow =-0.3
        xHigh = 1.7
        offsetV = (xLow + xHigh)*0.5
        amplitudeV = (xHigh - xLow)*0.5
        ## Created functions to ease profiling
        self.getRamp(outPrefix,iChip,adcSerial,adcOffset,adcClock,sampleRate,xLow,xHigh,amplitudeV,offsetV)
        self.getDC(outPrefix,iChip,adcSerial,adcOffset,adcClock,sampleRate)
        amplitudeV *= 0.6
        self.getSin(outPrefix,iChip,adcSerial,adcOffset,adcClock,sampleRate,amplitudeV,offsetV)
        self.funcgen.stop()

    def getRamp(self,outPrefix,iChip,adcSerial,adcOffset,adcClock,sampleRate,xLow,xHigh,amplitudeV,offsetV):
        freq = 734
        self.funcgen.startRamp(freq,xLow,xHigh)
        time.sleep(self.settlingTime)
        self.dumpWaveformRootFile(iChip,outPrefix,3,freq,offsetV,amplitudeV,self.femb.MAX_NUM_PACKETS,adcSerial=adcSerial,adcOffset=adcOffset,adcClock=adcClock,sampleRate=sampleRate)

    def getDC(self,outPrefix,iChip,adcSerial,adcOffset,adcClock,sampleRate):
        for dc in [0.2,0.5,1.,1.6]:
          self.funcgen.startDC(dc)
          time.sleep(self.settlingTime)
          self.dumpWaveformRootFile(iChip,outPrefix,1,0.,dc,0.,10,adcSerial=adcSerial,adcOffset=adcOffset,adcClock=adcClock,sampleRate=sampleRate)

    def getSin(self,outPrefix,iChip,adcSerial,adcOffset,adcClock,sampleRate,amplitudeV,offsetV):
        freqList = [6.2365e4,4.83587e5,9.515125e5]
        for freq in freqList:
          if sampleRate > 0.:
            if freq >= 0.5*sampleRate: # if greater than nyquist don't do
                continue
          self.funcgen.startSin(freq,amplitudeV,offsetV)
          time.sleep(self.settlingTime)
          self.dumpWaveformRootFile(iChip,outPrefix,2,freq,offsetV,amplitudeV,100,adcSerial=adcSerial,adcOffset=adcOffset,adcClock=adcClock,sampleRate=sampleRate)

    def dumpWaveformRootFile(self,iChip,fileprefix,functype,freq,offsetV,amplitudeV,nPackets=None,adcSerial=-1,adcOffset=-2,adcClock=-1,sampleRate=-1):
        filename = "{}_functype{}_freq{:.3f}_offset{:.3f}_amplitude{:.3f}.root".format(fileprefix,functype,freq,offsetV,amplitudeV)
        if not nPackets:
          nPackets = self.nPackets
        if functype > 1:
            nPackets = 100
        wrt = WRITE_ROOT_TREE(self.config,iChip,filename,nPackets)
        wrt.funcType = functype
        wrt.funcFreq = freq
        wrt.funcOffset = offsetV
        wrt.funcAmp = amplitudeV
        wrt.adcSerial = adcSerial
        wrt.adcOffset = adcOffset
        wrt.adcClock = adcClock
        wrt.sampleRate = sampleRate
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
  
    timestamp = datetime.datetime.now().replace(microsecond=0).isoformat().replace(":","").replace("-","")
    for iChip in range(config.NASICS):
        fileprefix = "adcTestData_{}_chip{}".format(timestamp,iChip)
        collect_data.getData(fileprefix,iChip)
