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
import sys
import os.path
import time
import glob
from uuid import uuid1 as uuid
import numpy
import matplotlib
if os.path.basename(sys.argv[0]) == "femb_adc_const_tests":
    print("Using matplotlib AGG backend")
    matplotlib.use("AGG")
import matplotlib.pyplot as plt
import ROOT

class DC_TESTS(object):
    """
    Tests of ADC on DC data
    """

    def __init__(self,config):
        """
        config is a femb_python.configuration.CONFIG object
        """
        self.config = config

    def analyze(self,infilenames,verbose=False):
        allStats = []
        for iChan in range(16):
            chanStats = {}
            for infilename in infilenames:
                data, serial, metadata = self.loadWaveform(iChan,infilename)
                nData = len(data)
                mean = numpy.mean(data)
                std = numpy.std(data)
                voltage = metadata["funcOffset"]
                vStr = "CodeFor{:.1f}V".format(voltage)
                chanStats["mean"+vStr] = mean
                chanStats["rms"+vStr] = std
                if verbose:
                    print("{} chan {} {:.1f} {:.2f}".format(vStr,iChan,mean,std))
            allStats.append(chanStats)
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
        if metadata['funcType'] != 1:
            raise Exception("Input file is not funcType==1 DC data")
        result = []
        for iEntry in range(tree.GetEntries()):
            tree.GetEntry(iEntry)
            if iChan == tree.chan:
                adccode = tree.wf
                adccode = list(adccode)
                result.extend(adccode)
        return result, metadata['adcSerial'], metadata

def main():
    from ...configuration.argument_parser import ArgumentParser
    from ...configuration import CONFIG
    ROOT.gROOT.SetBatch(True)
    parser = ArgumentParser(description="Analyze DC waveforms")
    parser.add_argument("infilenames",help="Input file names. The file created by femb_adc_collect_data that includes 'functype1'.",nargs="+")
    args = parser.parse_args()
  
    config = CONFIG()
  
    dc_tests = DC_TESTS(config)
    stats = dc_tests.analyze(args.infilenames, True)
