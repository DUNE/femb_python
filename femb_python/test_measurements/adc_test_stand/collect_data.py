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

    def __init__(self,config):
        """
        config is a femb_python.configuration.CONFIG object
        """
        self.config = config
        self.femb = FEMB_UDP()
        self.funcgen = self.config.FUNCGENINTER
        self.settlingTime = 0.1 # second
        self.maxTries = 1000
        self.nBits = 12

    def getData(self,outPrefix,iChip,adcSerial=-1,adcOffset=-2,adcClock=-1,sampleRate=-1,longRamp=False,longRampOnly=False,outSuffix=""):
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
        if longRamp or longRampOnly:
            self.getRamp(outPrefix,iChip,adcSerial,adcOffset,adcClock,sampleRate,xLow,xHigh,amplitudeV,offsetV,longRamp=True,outSuffix=outSuffix)
        if longRampOnly:
            self.funcgen.stop()
            return
        self.getRamp(outPrefix,iChip,adcSerial,adcOffset,adcClock,sampleRate,xLow,xHigh,amplitudeV,offsetV,outSuffix=outSuffix)
        self.getDC(outPrefix,iChip,adcSerial,adcOffset,adcClock,sampleRate,outSuffix=outSuffix)
        amplitudeV *= 0.6
        self.getSin(outPrefix,iChip,adcSerial,adcOffset,adcClock,sampleRate,amplitudeV,offsetV,outSuffix=outSuffix)
        self.funcgen.stop()

    def getRamp(self,outPrefix,iChip,adcSerial,adcOffset,adcClock,sampleRate,xLow,xHigh,amplitudeV,offsetV,longRamp=False,outSuffix=""):
        freq = 734
        nPackets = 100
        if longRamp:
            freq = 4
            nPackets = 7000
        self.funcgen.startRamp(freq,xLow,xHigh)
        time.sleep(self.settlingTime)
        self.dumpWaveformRootFile(iChip,outPrefix,3,freq,offsetV,amplitudeV,nPackets,adcSerial=adcSerial,adcOffset=adcOffset,adcClock=adcClock,sampleRate=sampleRate,outSuffix=outSuffix)

    def getDC(self,outPrefix,iChip,adcSerial,adcOffset,adcClock,sampleRate,outSuffix=""):
        for dc in [0.2,0.5,1.,1.6]:
          self.funcgen.startDC(dc)
          time.sleep(self.settlingTime)
          self.dumpWaveformRootFile(iChip,outPrefix,1,0.,dc,0.,10,adcSerial=adcSerial,adcOffset=adcOffset,adcClock=adcClock,sampleRate=sampleRate,outSuffix=outSuffix)

    def getSin(self,outPrefix,iChip,adcSerial,adcOffset,adcClock,sampleRate,amplitudeV,offsetV,outSuffix=""):
        freqList = [6.2365e4,4.83587e5,9.515125e5]
        for freq in freqList:
          if sampleRate > 0.:
            if freq >= 0.5*sampleRate: # if greater than nyquist don't do
                continue
          self.funcgen.startSin(freq,amplitudeV,offsetV)
          time.sleep(self.settlingTime)
          self.dumpWaveformRootFile(iChip,outPrefix,2,freq,offsetV,amplitudeV,100,adcSerial=adcSerial,adcOffset=adcOffset,adcClock=adcClock,sampleRate=sampleRate,outSuffix=outSuffix)

    def dumpWaveformRootFile(self,iChip,fileprefix,functype,freq,offsetV,amplitudeV,nPackets=None,adcSerial=-1,adcOffset=-2,adcClock=-1,sampleRate=-1,outSuffix=""):
        print("outSuffix:",outSuffix)
        filename = "{}_functype{}_freq{:.3f}_offset{:.3f}_amplitude{:.3f}{}.root".format(fileprefix,functype,freq,offsetV,amplitudeV,outSuffix)
        if not nPackets:
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
    #parser.add_argument("outfilename",help="Output root file name")
    parser.add_argument("-l","--longRamp",help="Take 4 Hz, 7000 packets long-ramp data",action="store_true")
    args = parser.parse_args()
  
    config = CONFIG()

    collect_data = COLLECT_DATA(config)
  
    timestamp = datetime.datetime.now().replace(microsecond=0).isoformat().replace(":","").replace("-","")
    for iChip in range(config.NASICS):
        fileprefix = "adcTestData_{}_chip{}".format(timestamp,iChip)
        collect_data.getData(fileprefix,iChip,longRamp=args.longRamp)
