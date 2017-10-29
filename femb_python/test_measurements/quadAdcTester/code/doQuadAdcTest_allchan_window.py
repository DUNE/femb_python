"""
This module contains a class that displays a live QUAD ADC readout, taken from single ADC readout.

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

from femb_python.configuration import CONFIG
from femb_python.femb_udp import FEMB_UDP

class TRACE_ALLCHAN_WINDOW(Tk.Frame):
  """
  This window displays a live ADC redout
  """
  
  def __init__(self, master=None):
    self.maxtraces = 5
    self.selChan = 0

    Tk.Frame.__init__(self,master) # hack to make work in python2

    self.pack()
    self.figure = Figure(figsize=(20,8), dpi=100, facecolor='white')
       
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

    self.femb = None
    self.iTrace = -1
    self.traces = []
    self.timestamps = []

    self.reset()

  def reset(self,iTrace=None):
    self.femb = FEMB_UDP()
    self.femb_config = CONFIG()
    self.figure.clf()
    self.subgs = [None]*16*4
    self.ax = [None]*16*4
    self.plot = [None]*16*4

    # 4x4x4 grid, one cell per channel
    self.gs  = gridspec.GridSpec(4,16)
    self.gs.update(wspace=0.2,hspace=0.2)
    # 1 plots per channel
    for row in range(4):
      for col in range(16):        
        self.subgs[col+16*row] = gridspec.GridSpecFromSubplotSpec(1, 1, subplot_spec=self.gs[col+16*row],hspace=0.0)
        self.ax[col+16*row] = self.figure.add_subplot(self.subgs[col+16*row][0])
        self.ax[col+16*row].tick_params(axis='x', colors='black',labelsize='medium')
        self.ax[col+16*row].tick_params(axis='y', colors='black',labelsize='smaller')

    if iTrace is None:
        self.ani = animation.FuncAnimation(self.figure, self.plotData, interval=100, blit=True)
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

    for a in range(4):
    #for a in [2]:
        #if a != 0:
        #    continue
        asicNum = a
        #asicNum = 2
        self.femb_config.setExtClockRegs(asicNum)
        self.femb_config.selectAsic(asicNum)
        #self.femb_config.doAdcAsicConfig(a)
        #self.femb_config.initAsic(a)
        chPlots, thistimestamp = self.getTraceAndFFT(iTrace=iTrace)    
        if chPlots == None:
            continue
        if thistimestamp == None:
            continue
        if len(chPlots) != 16:
            continue
        for chan in range(0,16,1) :
            t = chPlots[chan][0]
            adc = chPlots[chan][1]
            if not (t is None) and not (adc is None):
                self.plot[chan+16*a] = self.ax[chan+16*a].plot(t,adc)
                #if c+4*r < 12: self.ax[c+4*r].set_xticklabels([])
    self.figure.text(0.5,0.02,'Time [us]',ha='center',color='black',fontsize='25.0',weight='bold')
    self.figure.text(0.08,0.5,'ADC',ha='center',rotation=90,color='black',fontsize='25.0',weight='bold') 

    if not (thistimestamp is None):
        self.figure.suptitle(thistimestamp.replace(microsecond=0).isoformat(" "))
    self.canvas.draw()
    return self.plot[0]

  def getTraceAndFFT(self,iTrace=None):
    """
    Gets trace from FEMB and returns 4 1D arrays:
        times, ADC counts
    """
    data = None
    timestamp = None
    if iTrace is None:
        data = self.femb.get_data(5)
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
        return None, None
    if len(data ) == 0:
        return None, None

    chSamples = self.convertHighSpeedPacked(data)

    if len(chSamples) != 16:
      return None, None

    chPlots = []
    for chan in range(0,16,1):
      xpoint = []
      ypoint = []
      num = 0
      for samp in chSamples[chan]:
        xpoint.append(num*0.5)
        ypoint.append(samp)
        num = num + 1
      
      xarr = np.array(xpoint)
      yarr = np.array(ypoint)
      chPlots.append([xarr,yarr])
    
    return chPlots, timestamp
    
  #taken from write_root_tree
  def convertHighSpeedPacked(self,data):
    packetNum = 0
    wordArray = []
    result = [[] for chan in range(16)]
    for word in data:
      if str(hex(word)) == "0xface" :
        packetNum = 0
        wordArray = []
      if packetNum > 0 and packetNum < 13 :
        wordArray.append( word )
      if packetNum == 12 :
        result[0].append(((wordArray[5] & 0xFFF0 ) >> 4))
        result[1].append(((wordArray[4] & 0xFF00 ) >> 8) | ((wordArray[5] & 0x000F ) << 8))
        result[2].append(((wordArray[4] & 0x00FF ) << 4) | ((wordArray[3] & 0xF000 ) >> 12))
        result[3].append(((wordArray[3] & 0x0FFF ) >> 0))
        result[4].append(((wordArray[2] & 0xFFF0 ) >> 4))
        result[5].append(((wordArray[2] & 0x000F ) << 8) | ((wordArray[1] & 0xFF00 ) >> 8))
        result[6].append(((wordArray[1] & 0x00FF ) << 4) | ((wordArray[0] & 0xF000 ) >> 12))
        result[7].append(((wordArray[0] & 0x0FFF ) >> 0)				)
        result[8].append(((wordArray[11] & 0xFFF0 ) >> 4))
        result[9].append(((wordArray[11] & 0x000F ) << 8) | ((wordArray[10] & 0xFF00 ) >> 8))
        result[10].append(((wordArray[10] & 0x00FF ) << 4) | ((wordArray[9] & 0xF000 ) >> 12))
        result[11].append(((wordArray[9] & 0x0FFF )))
        result[12].append(((wordArray[8] & 0xFFF0 ) >> 4))
        result[13].append(((wordArray[8] & 0x000F ) << 8) | ((wordArray[7] & 0xFF00 ) >> 8))
        result[14].append(((wordArray[7] & 0x00FF ) << 4) | ((wordArray[6] & 0xF000 ) >> 12))
        result[15].append(((wordArray[6] & 0x0FFF ) ))
      packetNum = packetNum + 1
    return result

def main():
    window = Tk.Tk()
    window.title("QUAD ADC All Channel Trace Viewer")
    trace_fft = TRACE_ALLCHAN_WINDOW(window)
    window.mainloop()

if __name__ == '__main__':
    main()
