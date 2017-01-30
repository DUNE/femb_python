"""
This module contains a class that displays a live ADC readout and its FFT.
Configuration and channel selection are handled elsewhere.
"""
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()

import time
import numpy as np

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg as FigureCanvas
from matplotlib.backends.backend_tkagg import NavigationToolbar2TkAgg as NaviationToolbar
from matplotlib.figure import Figure
from matplotlib import animation

import tkinter as Tk

from .femb_udp import FEMB_UDP

class TRACE_FFT_WINDOW(Tk.Frame):
  """
  This window displays a live ADC redout and its FFT
  """

  def __init__(self, master=None):
    self.maxtraces = 5



    super().__init__(master)
    self.pack()

    self.figure = Figure(figsize=(8,8), dpi=100)
    
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
    self.data = []
    self.reset()

  def reset(self,data=None):
    self.femb = FEMB_UDP()
    self.figure.clf()
    self.ax1 = self.figure.add_subplot(211)
    self.ax2 = self.figure.add_subplot(212)
    self.plot1 = self.ax1.plot([],[])
    self.plot2 = self.ax2.plot([],[])
    if data is None:
        self.ani = animation.FuncAnimation(self.figure, self.plotData,
                                   interval=1000, blit=True)
    else:
        self.ani.event_source.stop()
        self.plotData(0,data)
    self.canvas.draw()

  def pause(self):
    print(self.iTrace)
    self.reset(self.data[self.iTrace])
    self.pauseButton['state'] = Tk.DISABLED
    self.playButton['state'] = Tk.NORMAL
    self.prevButton['state'] = Tk.NORMAL
    #self.nextButton['state'] = Tk.NORMAL

  def play(self):
    self.ani.event_source.start()
    self.pauseButton['state'] = Tk.NORMAL
    self.playButton['state'] = Tk.DISABLED
    self.prevButton['state'] = Tk.DISABLED
    self.nextButton['state'] = Tk.DISABLED

  def prevTrace(self):
    self.iTrace -= 1
    print(self.iTrace)
    self.reset(self.data[self.iTrace])
    if self.iTrace < 1:
        self.prevButton['state'] = Tk.DISABLED
    else:
        self.prevButton['state'] = Tk.NORMAL
    if (len(self.data) - self.iTrace) < 1:
        self.nextButton['state'] = Tk.DISABLED
    else:
        self.nextButton['state'] = Tk.NORMAL

  def nextTrace(self):
    self.iTrace += 1
    print(self.iTrace)
    self.reset(self.data[self.iTrace])
    if self.iTrace < 1:
        self.prevButton['state'] = Tk.DISABLED
    else:
        self.prevButton['state'] = Tk.NORMAL
    if (len(self.data) - self.iTrace) < 1:
        self.nextButton['state'] = Tk.DISABLED
    else:
        self.nextButton['state'] = Tk.NORMAL

  def plotData(self,iFrame,data=None):
    print("Running Plot Data")
    self.ax1.cla()
    self.ax2.cla()
    self.ax1.set_xlabel("Time [us]")
    self.ax1.set_ylabel("Sample Value [ADC Counts]")
    self.ax2.set_xlabel("Frequency [MHz]")
    self.ax2.set_ylabel("|Y(freq)|")
    t, adc, frq, ampl = self.getTraceAndFFT(data=data)
    if t and adc:
        self.plot1 = self.ax1.plot(t,adc)
    #else:
    #    t = np.arange(100)
    #    adc = np.random.randn(100)
    #    self.plot1 = self.ax1.plot(t,adc)
    #    self.data.append(adc)
    #    if len(self.data) > self.maxtraces:
    #        self.data.pop(0)
    #    self.iTrace = len(self.data) - 1
    if frq and ampl:
        self.plot2 = self.ax2.plot(frq, ampl,'r')
    #else:
    #    frq = np.arange(100)
    #    ampl = frq**(np.random.randn()+1)
    #    self.plot2 = self.ax2.plot(frq, ampl,'r')
    self.canvas.draw()
    return self.plot1

  def getTraceAndFFT(self,data=None):
    """
    Gets trace from FEMB and returns 4 1D arrays:
        times, ADC counts, frequencies, Amplitude
    """
    Yfft_total = []
    first = 1
    if data == None:
        data = self.femb.get_data(10)
        if data == None:
            #time.sleep(1.)
            return None, None, None, None
        if len(data ) == 0:
            #time.sleep(1.)
            return None, None, None, None
        self.data.append(data)
        if len(self.data) > self.maxtraces:
            self.data.pop(0)
        self.iTrace = len(self.data) - 1
    xpoint = []
    ypoint = []
    num = 0
    
    for samp in data:
        chNum = ((samp >> 12 ) & 0xF)
        sampVal = (samp & 0xFFF)
        #print str(chNum) + "\t" + str(sampVal) + "\t" + str( hex(sampVal) )
        #if chNum == 0:
        xpoint.append(num*0.5)
        ypoint.append(sampVal)
        num = num + 1
    
    xarr = np.array(xpoint)
    yarr = np.array(ypoint)
    
    Fs = 2.0;  # sampling rate
    Ts = 1.0/Fs; # sampling interval
    t = np.arange(0,1,Ts) # time vector
    
    n = len(yarr) # length of the signal
    k = np.arange(n)
    T = n/Fs
    frq = k/T # two sides frequency range
    frq = frq[:n//2] # one side frequency range
    
    Yfft = np.fft.fft(yarr)/n # fft computing and normalization
    Yfft = Yfft[:n//2]
    frq = frq[1:]
    Yfft = Yfft[1:]
    
    #do averaging and normalization, very messy
    pos = 0
    total = 0
    for x in np.nditer(Yfft):
        #print abs(x)
        total = total + abs(x)
        if first == 1:
            Yfft_total.append( abs(x) )
        else:
            Yfft_total[pos] = Yfft_total[pos] + abs(x)
        pos = pos + 1	
    
    first = 0
    if total < 0 :
        #time.sleep(0.1)
        return None, None, None, None
    
    pos = 0
    Yfft_norm = []
    for bin in Yfft_total:
        Yfft_norm.append( bin / total)

    return xarr, yarr, frq, Yfft_norm
    
def main():
    window = Tk.Tk()
    window.title("FEMB Trace & FFT Viewer")
    trace_fft = TRACE_FFT_WINDOW(window)
    window.mainloop()
