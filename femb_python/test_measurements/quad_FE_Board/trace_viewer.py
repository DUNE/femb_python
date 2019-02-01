# -*- coding: utf-8 -*-
"""
Created on Fri Feb  1 12:24:57 2019

@author: eraguzin

This module contains a class that displays a live ADC readout and its FFT for all
16 channels of an ASIC:
               
1 | 2 | 3 | 4  
---------------
5 | 6 | 7 | 8  
---------------
9 | 10| 11| 12
---------------
13| 14| 15| 16

Configurations handled elsewhere.

"""
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()

import datetime
import numpy as np


import matplotlib
matplotlib.use("TkAgg")
import matplotlib.gridspec as gridspec

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg as FigureCanvas
from matplotlib.backends.backend_tkagg import NavigationToolbar2TkAgg as NavigationToolbar
from femb_python.test_measurements.quad_FE_Board.low_level_pre_udp import LOW_LEVEL
from matplotlib.figure import Figure
from matplotlib import animation

import tkinter as Tk

matplotlib.rc('xtick',labelsize=8)
matplotlib.rc('ytick',labelsize=8)

class TRACE_VIEWER(Tk.Frame):
  """
  This window displays a live ADC readout
  """
  
  def __init__(self, master=None):  
    #Gets the low level module to do UDP packets
    self.femb = LOW_LEVEL()
    
    #Creates Tkinter object
    Tk.Frame.__init__(self,master) # hack to make work in python2
    self.pack()
    #Creates Matplotlib object
    self.figure = Figure(figsize=(20,7), dpi=100, facecolor='white')
    self.canvas = FigureCanvas(self.figure, master=self)
    self.canvas.show()
    self.canvas.get_tk_widget().pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)
    #Create toolbar for bottom
    self.toolbar = NavigationToolbar(self.canvas,self)
    self.toolbar.update()
    self.canvas._tkcanvas.pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)

    self.pauseButton = Tk.Button(self,text="Pause",command=self.pause)
    self.pauseButton.pack(side=Tk.LEFT)

    self.playButton = Tk.Button(self,text="Play",command=self.play,state=Tk.DISABLED)
    self.playButton.pack(side=Tk.LEFT)
    
    self.pulseButton = Tk.Button(self,text="Toggle Pulse",command=self.togglePulse,state=Tk.NORMAL)
    self.pulseButton.pack(side=Tk.LEFT)
#    self.pulseButton.grid(sticky=Tk.W,row=8,column=50+1)
    
    from femb_python.configuration import CONFIG
    self.config = CONFIG

    self.chip = 0
    self.pulseEnabled = False
    self.reset()

  def reset(self):
    self.figure.clf()
    self.subgs = [None]*16
    self.ax = [None]*16
    self.plot = [None]*16
    
    self.figure.text(0.5,0.02,'Time [us]',ha='center',color='black',fontsize='25.0',weight='bold')
    self.figure.text(0.08,0.625,'ADC counts',ha='center',rotation=90,color='black',fontsize='25.0',weight='bold') 

    # 4x4 grid, one cell per channel
    self.gs  = gridspec.GridSpec(4,4)
    self.gs.update(wspace=0.2,hspace=0.2)
    # 1 plots per channel, create axes objects
    for row in range(4):
      for col in range(4):        
        ch = col+4*row
        self.subgs[ch] = gridspec.GridSpecFromSubplotSpec(1, 1, subplot_spec=self.gs[ch],hspace=0.0)
        self.ax[ch] = self.figure.add_subplot(self.subgs[ch][0])
        self.ax[ch].tick_params(axis='x', colors='black',labelsize='medium')
        self.ax[ch].tick_params(axis='y', colors='black',labelsize='smaller')
        

    #Continually updates by calling self.plotData
    self.ani = animation.FuncAnimation(self.figure, self.plotData, interval=1000, blit=True)
    self.canvas.draw()
    
  def togglePulse(self):
      if (self.pulseEnabled == False):
          self.femb.setInternalPulser(period = 400, shift = 0, enable = True)
          self.pulseEnabled = True
      else:
          self.femb.setInternalPulser(period = 400, shift = 0, enable = False)
          self.pulseEnabled = False

  def pause(self):
    self.ani.event_source.stop()
    self.pauseButton['state'] = Tk.DISABLED
    self.playButton['state'] = Tk.NORMAL

  def play(self):
    self.ani.event_source.start()
    self.pauseButton['state'] = Tk.NORMAL
    self.playButton['state'] = Tk.DISABLED

  def plotData(self, iFrame):
    for a in self.ax:
        #Clears all previous traces
        a.cla()
        #Limits the number of traces on each subplot
        a.locator_params(tight=True, nbins=3)

    #In case no data, return an empty plot
#    self.plot[0] = self.ax[0].plot()
    t, adc, thistimestamp = self.getData()
    for r in range(4):
        for c in range(4):
            ch = c+4*r
            if not (t is None) and not (adc is None):
                self.plot[ch] = self.ax[ch].plot(t,adc[ch])
                if ch < 12: self.ax[ch].set_xticklabels([])
                self.ax[ch].title.set_text("Channel {}".format(ch))
    

    if not (thistimestamp is None):
        self.figure.suptitle(thistimestamp.replace(microsecond=0).isoformat(" "))
    self.canvas.draw()
    return self.plot[0]

  def getData(self):
    """
    Gets trace from FEMB and returns 4 1D arrays:
        times, ADC counts
    """
    
    data = self.femb.get_data_chipX(chip = self.chip, packets = 2, data_format = "counts", tagged = False, header = False)
    timestamp = datetime.datetime.now()

    if data == None:
        return None, None, None
    if len(data) == 0:
        return None, None, None

    xpoint = []
    for num,samp in enumerate(data[0]):
      xpoint.append(num*float(self.config["DEFAULT"]["SAMPLE_PERIOD"]))

    return xpoint, data, timestamp
    
def main_start():
    window = Tk.Tk()
    #This function will run when the window is closed
    def on_closing():
        window.destroy()
        window.quit()
        
    window.protocol("WM_DELETE_WINDOW", on_closing)
    window.title("Full Chip Waveform Viewer")
    TRACE_VIEWER(window)
    window.mainloop()