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
	'iChip' : metadataTree.iChip,
	'adcSerial' : metadataTree.adcSerial,
	'feSerial' : metadataTree.feSerial,
        }
    
    #####
    voltageGood = bool(tree.GetBranch("voltage"))
    calibrationTree = f.Get("calibration")
    voltages = {}
    calibSlopes = {}
    calibInters = {}
    #####
    result = {}
    for iEntry in range(tree.GetEntries()):
        tree.GetEntry(iEntry)
        iChannel = tree.chan % 16
        adccodes = list(tree.wf)
        #if self.nBits < 12:
        #    adccodes = [i >> (12 - self.nBits) for i in adccodes]
        try:
          result[iChannel].extend(adccodes)
        except KeyError:
          result[iChannel] = adccodes
        if voltageGood:
          voltagesTmp = list(tree.voltage)
          try:
            voltages[iChannel].extend(voltagesTmp)
          except KeyError:
            voltages[iChannel] = voltagesTmp
        if calibrationTree:
          calibrationTree.GetEntry(iEntry)
          calibSlopes[iChannel] = calibrationTree.voltsPerADC
          calibInters[iChannel] = calibrationTree.voltsIntercept
    if not voltageGood:
        voltages = None
    if not calibrationTree:
        calibSlopes = None
        calibInters = None
    return result, metadata, voltages, calibSlopes, calibInters

def main():
    from ..configuration.argument_parser import ArgumentParser
    parser = ArgumentParser(description="Displays a trace from a root file")
    parser.add_argument("infilename",help="file name to read the waveform from")
    args = parser.parse_args()
    waveforms, metadata, voltages, calibSlopes, calibInters = loadWaveform(args.infilename)

    fig, axs = plt.subplots(4,4)
    fig2, axs2 = plt.subplots(4,4)
    fig.suptitle("Waveforms for socket: {}, FE: {} ADC: {}".format(metadata['iChip'],metadata['feSerial'],metadata['adcSerial']))
    fig2.suptitle("FFT for socket: {}, FE: {} ADC: {}".format(metadata['iChip'],metadata['feSerial'],metadata['adcSerial']))
    for iChan in waveforms:
      ax = axs[iChan // 4][iChan % 4]
      ax2 = axs2[iChan // 4][iChan % 4]
      waveform = waveforms[iChan]
      if not (voltages is None):
        if not (calibSlopes is None):
            ax.plot(numpy.array(voltages[iChan])/calibSlopes[iChan]-calibInters[iChan]/calibSlopes[iChan],"-g")
        else:
            ax.plot(voltages[iChan],"-g")
      ax.plot(waveform,"-b")
      ax.set_title("Channel: {}".format(iChan))

      N = len(waveform)
      freqs = numpy.arange(N) / (N / 2.0)
      fft = numpy.fft.fft(waveform)

      freqs = freqs[1:N//2]
      fft = fft[1:N//2]

      fft = abs(fft*fft.conj())

      ax2.plot(freqs,fft)
      ax2.set_title("Channel: {}".format(iChan))
      if (fft > 0.).all():
        ax2.set_yscale('log')

      if iChan // 4 == 3:
        ax.set_xlabel("Time Sample")
        ax2.set_xlabel("Frequency")
      if iChan % 4 == 0:
        ax.set_ylabel("ADC Code")
        ax2.set_ylabel("Power")
    plt.show()
