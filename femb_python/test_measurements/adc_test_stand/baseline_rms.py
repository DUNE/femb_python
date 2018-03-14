from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals
from __future__ import absolute_import
from builtins import range
from future import standard_library
standard_library.install_aliases()
import time
import glob
from uuid import uuid1 as uuid
import numpy
import matplotlib.pyplot as plt
import ROOT

class BASELINE_RMS(object):
    """
    Tests of ADC baseline and rms
    """

    def __init__(self):
        self.nBits = 12

    def analyze(self,infile,diagnosticPlots=False):
        allStats = []
        for iChan in range(16):
                data, adcSerial, metadata, = self.loadWaveform(iChan,infile)
                data = numpy.array(data)
                chanStats = {}
                chanStats["mean"] = float(numpy.mean(data))
                chanStats["rms"] = float(numpy.std(data))
                allStats.append(chanStats)
                if diagnosticPlots:
                    print("Channel {:2} mean: {:7.2f}, RMS: {:7.2f}".format(iChan,chanStats["mean"],chanStats["rms"]))
        return allStats

    def loadWaveform(self,iChan,infilename):
        f = ROOT.TFile(infilename)
        tree = f.Get("femb_wfdata")
        metadataTree = f.Get("metadata")
        metadataTree.GetEntry(0)
        metadata = {
            'funcType': metadataTree.funcType,
            'funcAmp': metadataTree.funcAmp,
            'funcOffset': metadataTree.funcOffset,
            'funcFreq': metadataTree.funcFreq,
            'adcSerial': metadataTree.adcSerial,
            'adcOffset': metadataTree.adcOffset,
            }
        result = []
        for iEntry in range(tree.GetEntries()):
            tree.GetEntry(iEntry)
            if iChan == tree.chan:
                adccode = tree.wf
                adccode = list(adccode)
                if self.nBits < 12:
                    adccode = [i >> (12 - self.nBits) for i in adccode]
                result.extend(adccode)
        return result, metadata['adcSerial'], metadata

def main():
    from ...configuration.argument_parser import ArgumentParser
    ROOT.gROOT.SetBatch(True)
    parser = ArgumentParser(description="Measures ADC Baseline and RMS")
    parser.add_argument("infilename",help="Input file name.")
    parser.add_argument("-q", "--quiet",help="Disables output plots and printing, just dumps stats to stdout.",action='store_true')
    args = parser.parse_args()
  
    static_tests = BASELINE_RMS()
    stats = static_tests.analyze(args.infilename,diagnosticPlots=not args.quiet)
    if args.quiet:
        print(stats)
