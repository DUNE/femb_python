from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import
from builtins import range
from future import standard_library
standard_library.install_aliases()
import matplotlib.pyplot as plt
import ROOT
import numpy
import matplotlib.pyplot as plt

def loadWaveform(filename):
    """
    result[freq][amp][iChip][iChan][iSample]
    """
    f = ROOT.TFile(filename)
    tree =  f.Get("femb_wfdata")
    metadataTree = f.Get("metadata")
    metadatas = []
    amplitudes = set()
    frequencies = set()
    metadataTree.GetEntry(0)
    metadata = {
        'funcType': metadataTree.funcType,
        'funcAmp': metadataTree.funcAmp,
        'funcOffset': metadataTree.funcOffset,
        'funcFreq': metadataTree.funcFreq,
        }
    
    result = {}
    for iEntry in range(tree.GetEntries()):
        tree.GetEntry(iEntry)
        iChip = tree.chan//16
        iChannel = tree.chan % 16
        adccodes = list(tree.wf)
        #if self.nBits < 12:
        #    adccodes = [i >> (12 - self.nBits) for i in adccodes]
        try:
          result[iChip][iChannel].extend(adccodes)
        except KeyError:
          if iChip in result:
            result[iChip][iChannel] = adccodes
          else:
            result[iChip] = {iChannel:adccodes}
    return result, metadata

def main():
    from ..configuration.argument_parser import ArgumentParser
    parser = ArgumentParser(description="Displays a trace from a root file")
    parser.addLoadWaveformRootFileArgs(required=True)
    args = parser.parse_args()
    waveforms, metadata = loadWaveform(args.loadWaveformRootFile)

    for iChip in waveforms:
      fig, axs = plt.subplots(4,4)
      print(axs)
      for iChan in waveforms[iChip]:
        ax = axs[iChan // 4][iChan % 4]
        waveform = waveforms[iChip][iChan]
        ax.plot(waveform)
        ax.set_title("Chip: {} Channel: {}".format(iChip,iChan))
        ax.set_xlabel("Time Sample")
        ax.set_ylabel("ADC Code")
      plt.show()
