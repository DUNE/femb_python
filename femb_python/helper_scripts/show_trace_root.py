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
    if f.IsZombie():
        raise FileNotFoundError(filename)
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

def show_trace_root(infilename,sampleMax=None,fullADCRange=False):

    waveforms, metadata, voltages, calibSlopes, calibInters = loadWaveform(infilename)

    fig, axs = plt.subplots(4,4)
    fig2, axs2 = plt.subplots(4,4)
    fig.suptitle("Waveforms for socket: {}, FE: {} ADC: {}".format(metadata['iChip'],metadata['feSerial'],metadata['adcSerial']),fontsize="large")
    fig2.suptitle("FFT for socket: {}, FE: {} ADC: {}".format(metadata['iChip'],metadata['feSerial'],metadata['adcSerial']))
    axRights = []
    for iChan in waveforms:
      ax = axs[iChan // 4][iChan % 4]
      ax2 = axs2[iChan // 4][iChan % 4]
      waveform = waveforms[iChan]
      if fullADCRange:
        ax.set_ylim(0,4096)
      if sampleMax:
          ax.set_xlim(0,sampleMax)
      if not (voltages is None):
        if not (calibSlopes is None):
            ax.plot(numpy.array(voltages[iChan])/calibSlopes[iChan]-calibInters[iChan]/calibSlopes[iChan],"-g")
            axRight = ax.twinx()
            ylow,yhigh = ax.get_ylim()
            ylow = ylow*calibSlopes[iChan] + calibInters[iChan]
            yhigh = yhigh*calibSlopes[iChan] + calibInters[iChan]
            axRight.set_ylim(ylow*1000.,yhigh*1000.)
            if iChan % 4 == 3:
                axRight.set_ylabel("Voltage [mV]")
            axRights.append(axRight)
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

def main():
    from ..configuration.argument_parser import ArgumentParser
    parser = ArgumentParser(description="Displays a trace from a root file")
    parser.add_argument("infilename",help="file name to read the waveform from")
    parser.add_argument("--sampleMax",help="Show from 0 to <sampleMax> on the x-axis",type=int,default=None)
    parser.add_argument("--fullADCRange",help="Show full y-axis 0 to 4095.",action="store_true")
    
    args = parser.parse_args()

    try:
        show_trace_root(args.infilename,args.sampleMax,args.fullADCRange)
    except Exception as e:
        print("{}: {}".format(type(e).__name__,e))

