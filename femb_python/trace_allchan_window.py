"""
This module contains a class that displays a live ADC readout and its FFT for all
16 channels of an ASIC:
                        _______________
1 | 2 | 3 | 4          |               |
---------------        |  ADC vs time  |
5 | 6 | 7 | 8          |_______________|
---------------        |               |
9 | 10| 11| 12         |      FFT      |
---------------        |_______________|
13| 14| 15| 16                       

Configurations handled elsewhere.

"""
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import absolute_import
from builtins import super
from future import standard_library
standard_library.install_aliases()

import sys
import time
import datetime
import numpy as np

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg as FigureCanvas
from matplotlib.backends.backend_tkagg import NavigationToolbar2TkAgg as NaviationToolbar
from matplotlib.figure import Figure
from matplotlib import animation

import tkinter as Tk

matplotlib.rc('xtick',labelsize=8)
matplotlib.rc('ytick',labelsize=8)

from femb_python.femb_udp import FEMB_UDP
from femb_python.write_root_tree import WRITE_ROOT_TREE

class TRACE_FFT_ALLCHAN_WINDOW_NEW(Tk.Frame):
  """
  This window displays a live ADC redout
  """
  
  def __init__(self, master=None, packedHighSpeed=False):
    self.maxtraces = 5
    self.selChan = 0

    Tk.Frame.__init__(self,master) # hack to make work in python2

    self.pack()
    self.figure = Figure(figsize=(15,7), dpi=100, facecolor='white')
       
    self.canvas = FigureCanvas(self.figure, master=self)
    self.canvas.show()
    self.canvas.get_tk_widget().pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)
    self.toolbar = NaviationToolbar(self.canvas,self)
    self.toolbar.update()
    self.canvas._tkcanvas.pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)

    self.pauseButton = Tk.Button(self,text="Pause",command=self.pause)
    self.pauseButton.pack(side=Tk.LEFT)

    self.playButton = Tk.Button(self,text="Play",command=self.play,state=Tk.DISABLED)
    self.playButton.pack(side=Tk.LEFT)

    self.prevButton = Tk.Button(self,text="Previous Trace",command=self.prevTrace,state=Tk.DISABLED)
    self.prevButton.pack(side=Tk.LEFT)

    self.nextButton = Tk.Button(self,text="Next Trace",command=self.nextTrace,state=Tk.DISABLED)
    self.nextButton.pack(side=Tk.LEFT)

    self.packedHighSpeed = packedHighSpeed
    self.femb = None
    self.iTrace = -1
    self.traces = []
    self.timestamps = []

    self.reset()

  def reset(self,iTrace=None):
    self.femb = FEMB_UDP()
    self.figure.clf()
    self.subgs = [None]*16
    self.ax = [None]*16
    self.plot = [None]*16

    # 4x4 grid, one cell per channel
    self.gs  = gridspec.GridSpec(4,4)
    self.gs.update(wspace=0.2,hspace=0.2)
    # 1 plots per channel
    for row in range(4):
      for col in range(4):        
        self.subgs[col+4*row] = gridspec.GridSpecFromSubplotSpec(1, 1, subplot_spec=self.gs[col+4*row],hspace=0.0)
        self.ax[col+4*row] = self.figure.add_subplot(self.subgs[col+4*row][0])
        self.ax[col+4*row].tick_params(axis='x', colors='black',labelsize='medium')
        self.ax[col+4*row].tick_params(axis='y', colors='black',labelsize='smaller')

    if iTrace is None:
        self.ani = animation.FuncAnimation(self.figure, self.plotData, interval=1000, blit=True)
    else:
        self.plotData(0,iTrace)
    self.canvas.draw()

  def pause(self):
    self.ani.event_source.stop()
    self.reset(self.iTrace)
    self.pauseButton['state'] = Tk.DISABLED
    self.playButton['state'] = Tk.NORMAL
    self.prevButton['state'] = Tk.NORMAL
    self.nextButton['state'] = Tk.DISABLED

  def play(self):
    self.ani.event_source.start()
    self.pauseButton['state'] = Tk.NORMAL
    self.playButton['state'] = Tk.DISABLED
    self.prevButton['state'] = Tk.DISABLED
    self.nextButton['state'] = Tk.DISABLED

  def prevTrace(self):
    self.iTrace -= 1
    self.reset(self.iTrace)
    if self.iTrace < 1:
        self.prevButton['state'] = Tk.DISABLED
    else:
        self.prevButton['state'] = Tk.NORMAL
    if self.iTrace >= len(self.traces) - 1:
        self.nextButton['state'] = Tk.DISABLED
    else:
        self.nextButton['state'] = Tk.NORMAL

  def nextTrace(self):
    self.iTrace += 1
    self.reset(self.iTrace)
    if self.iTrace < 1:
        self.prevButton['state'] = Tk.DISABLED
    else:
        self.prevButton['state'] = Tk.NORMAL
    if self.iTrace >= len(self.traces) - 1:
        self.nextButton['state'] = Tk.DISABLED
    else:
        self.nextButton['state'] = Tk.NORMAL

  def plotData(self,iFrame,iTrace=None):
    for a in self.ax:
        a.cla()
        a.locator_params(tight=True, nbins=3)

    # In case no data, return an empty plot
    self.plot[0] = self.ax[0].plot()

    for r in range(4):
        for c in range(4):
            t, adc, thistimestamp = self.getTraceAndFFT(iTrace=iTrace,chan=c+4*r)
            if not (t is None) and not (adc is None):
                self.plot[c+4*r] = self.ax[c+4*r].plot(t,adc)
                if c+4*r < 12: self.ax[c+4*r].set_xticklabels([])
    self.figure.text(0.5,0.02,'Time [us]',ha='center',color='black',fontsize='25.0',weight='bold')
    self.figure.text(0.08,0.5,'ADC',ha='center',rotation=90,color='black',fontsize='25.0',weight='bold') 

    if not (thistimestamp is None):
        self.figure.suptitle(thistimestamp.replace(microsecond=0).isoformat(" "))
    self.canvas.draw()
    return self.plot[0]

  def getTraceAndFFT(self,iTrace=None,chan=0):
    """
    Gets trace from FEMB and returns 4 1D arrays:
        times, ADC counts
    """
    data = None
    timestamp = None
    if iTrace is None:
        data = self.femb.get_data(100)
        timestamp = datetime.datetime.now()
        self.traces.append(data)
        self.timestamps.append(timestamp)
        if len(self.traces) > self.maxtraces:
            self.traces.pop(0)
            self.timestamps.pop(0)
        self.iTrace = len(self.traces) - 1
    else:
        data = self.traces[iTrace]
        timestamp = self.timestamps[iTrace]
    if data == None:
        return None, None, None, None, None
    if len(data ) == 0:
        return None, None, None, None, None

    chSamples = None
    if self.packedHighSpeed:
      chSamples = WRITE_ROOT_TREE.convertHighSpeedPacked(None, data)
    else:
      chSamples = WRITE_ROOT_TREE.convertHighSpeedSimple(None, data)

    xpoint = []
    ypoint = []
    num = 0
    for samp in chSamples[chan]:
      xpoint.append(num*0.5)
      ypoint.append(samp)
      num = num + 1
      
    xarr = np.array(xpoint)
    yarr = np.array(ypoint)
    
    return xarr, yarr, timestamp
    
def main():
    window = Tk.Tk()
    window.title("FEMB All Channel Trace Viewer")
    trace_fft = TRACE_FFT_ALLCHAN_WINDOW_NEW(window)
    window.mainloop()
