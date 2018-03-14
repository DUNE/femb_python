from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import
from builtins import range
from future import standard_library
standard_library.install_aliases()
import ROOT
import numpy

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg as FigureCanvas
from matplotlib.backends.backend_tkagg import NavigationToolbar2TkAgg as NaviationToolbar
from matplotlib.figure import Figure
from matplotlib import animation

import tkinter as Tk

class TRACE_ROOT_WINDOW(Tk.Frame):
  """
  This window displays the trace from a root file
  """

  def __init__(self,infilename,sampleMax=None,fullADCRange=False,master=None):
    Tk.Frame.__init__(self,master) # hack to make work in python2

    self.pack()

    self.figure = Figure(figsize=(8,8), dpi=100)
    self.axs = []
    for iPlot in range(16):
        self.axs.append(self.figure.add_subplot(4,4,iPlot+1))
    
    self.canvas = FigureCanvas(self.figure, master=self)
    self.canvas.show()
    self.canvas.get_tk_widget().pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)
    self.toolbar = NaviationToolbar(self.canvas,self)
    self.toolbar.update()
    self.canvas._tkcanvas.pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)

    self.draw_trace(infilename,sampleMax=sampleMax,fullADCRange=fullADCRange)

  def loadWaveform(self,filename):
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
  	'adcSerial' : str(metadataTree.adcSerial),
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
          iChannel = int(tree.chan) % 16
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
            calibSlopes[iChannel] = float(calibrationTree.voltsPerADC)
            calibInters[iChannel] = float(calibrationTree.voltsIntercept)
      if not voltageGood:
          voltages = None
      if not calibrationTree:
          calibSlopes = None
          calibInters = None
      self.waveforms = result
      self.metadata = metadata
      del metadataTree
      del calibrationTree
      del tree
      f.Close()
      del f
      return result, metadata, voltages, calibSlopes, calibInters
  
  def draw_trace(self,infilename,sampleMax=None,fullADCRange=False):
  
      waveforms, metadata, voltages, calibSlopes, calibInters = self.loadWaveform(infilename)

#      self.figure.suptitle("Waveforms for socket: {}, FE: {} ADC: {}".format(metadata['iChip'],metadata['feSerial'],metadata['adcSerial']),fontsize="large")
      iChip = metadata['iChip']
      feSerial = metadata['feSerial']
      adcSerial = metadata['adcSerial']
      suptitleStr = "Waveforms for socket: {}, FE: {} ADC: {}".format(iChip,feSerial,adcSerial)
      self.figure.suptitle(suptitleStr,fontsize="large")
  
      axRights = []
      for iChan in waveforms:
        ax = self.axs[iChan]
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
  
        if iChan // 4 == 3:
          ax.set_xlabel("Time Sample")
        if iChan % 4 == 0:
          ax.set_ylabel("ADC Code")

class FFT_ROOT_WINDOW(Tk.Frame):
  """
  This window displays the FFT of given data
  """

  def __init__(self,waveforms,metadata,master=None):
    Tk.Frame.__init__(self,master) # hack to make work in python2

    self.pack()

    self.figure = Figure(figsize=(8,8), dpi=100)
    self.axs = []
    for iPlot in range(16):
        self.axs.append(self.figure.add_subplot(4,4,iPlot+1))
    
    self.canvas = FigureCanvas(self.figure, master=self)
    self.canvas.show()
    self.canvas.get_tk_widget().pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)
    self.toolbar = NaviationToolbar(self.canvas,self)
    self.toolbar.update()
    self.canvas._tkcanvas.pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)

    self.draw_fft(waveforms,metadata)
  
  def draw_fft(self,waveforms,metadata):
  
      self.figure.suptitle("FFT for socket: {}, FE: {} ADC: {}".format(metadata['iChip'],metadata['feSerial'],metadata['adcSerial']),fontsize="large")
  
      for iChan in waveforms:
        ax = self.axs[iChan]
        waveform = waveforms[iChan]

        N = len(waveform)
        freqs = numpy.arange(N) / (N / 2.0)
        fft = numpy.fft.fft(waveform)

        freqs = freqs[1:N//2]
        fft = fft[1:N//2]

        fft = abs(fft*fft.conj())

        ax.plot(freqs,fft)
        ax.set_title("Channel: {}".format(iChan))
        if (fft > 0.).all():
          ax.set_yscale('log')

        if iChan // 4 == 3:
          ax.set_xlabel("Frequency")
        if iChan % 4 == 0:
          ax.set_ylabel("Power")

def main():
    from ..configuration.argument_parser import ArgumentParser
    parser = ArgumentParser(description="Displays a trace from a root file")
    parser.add_argument("infilename",help="file name to read the waveform from")
    parser.add_argument("--sampleMax",help="Show from 0 to <sampleMax> on the x-axis",type=int,default=None)
    parser.add_argument("--fullADCRange",help="Show full y-axis 0 to 4095.",action="store_true")
    parser.add_argument("--dontShowFFT",help="Don't show FFT",action="store_true")
    
    args = parser.parse_args()

    #try:
    if True:
        window = Tk.Tk()
        window.title("FEMB ROOT File Trace Viewer")
        trace = TRACE_ROOT_WINDOW(args.infilename,sampleMax=args.sampleMax,fullADCRange=args.fullADCRange,master=window)
        fft_window = None
        fft = None
        if not args.dontShowFFT:
            fft_window = Tk.Toplevel(window)
            fft_window.title("FEMB ROOT FFT Viewer")
            fft = FFT_ROOT_WINDOW(trace.waveforms,trace.metadata,master=fft_window)
        window.mainloop()
    #except Exception as e:
    #    print("{}: {}".format(type(e).__name__,e))

