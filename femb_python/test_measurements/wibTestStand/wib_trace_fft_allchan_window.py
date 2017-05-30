"""
This module contains a class that displays a live ADC readout and its FFT for all
16 channels of an ASIC:
                       _______________
1 | 2 | 3 | 4          |              |
---------------        | ADC vs time  |
5 | 6 | 7 | 8          |              |
---------------        |--------------|
9 | 10| 11| 12         |              |
---------------        |     FFT      |
13| 14| 15| 16         |              |
                       ----------------

Configurations handled elsewhere.

TODO: this code can be made much shorter. there are 32 plots; there are a lot of
copied lines which could be improved with loops. the rows alternate between ADC
and FFT, meaning implementing loops will require some thought
"""
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import absolute_import
from builtins import super
from future import standard_library
standard_library.install_aliases()

import time
import datetime
import numpy as np

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg as FigureCanvas
from matplotlib.backends.backend_tkagg import NavigationToolbar2TkAgg as NaviationToolbar
from matplotlib.figure import Figure
from matplotlib import animation

import tkinter as Tk
import matplotlib.pyplot as plt

matplotlib.rc('xtick',labelsize=8)
matplotlib.rc('ytick',labelsize=8)

from femb_python.femb_udp import FEMB_UDP

class TRACE_FFT_WINDOW(Tk.Frame):
  """
  This window displays a live ADC redout and its FFT
  """

  def __init__(self, master=None):
    self.maxtraces = 5
    self.selChan = 0

    Tk.Frame.__init__(self,master) # hack to make work in python2

    self.pack()

    self.figure = Figure(figsize=(14,9), dpi=100)
       
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
    self.figure.clf()

    # TODO: put this in a loop
    #self.fig, self.axarr = plt.subplots(8,4)

    self.ax1 = self.figure.add_subplot(8,4,1)
    self.ax1.xaxis.label.set_color('blue')
    self.ax1.yaxis.label.set_color('blue')
    self.ax2 = self.figure.add_subplot(8,4,2,sharex=self.ax1,sharey=self.ax1)
    self.ax3 = self.figure.add_subplot(8,4,3,sharex=self.ax1,sharey=self.ax1)
    self.ax4 = self.figure.add_subplot(8,4,4,sharex=self.ax1,sharey=self.ax1)
    self.ax5 = self.figure.add_subplot(8,4,5)
    self.ax5.xaxis.label.set_color('red')
    self.ax5.yaxis.label.set_color('red')
    self.ax6 = self.figure.add_subplot(8,4,6,sharex=self.ax5,sharey=self.ax5)
    self.ax7 = self.figure.add_subplot(8,4,7,sharex=self.ax5,sharey=self.ax5)
    self.ax8 = self.figure.add_subplot(8,4,8,sharex=self.ax5,sharey=self.ax5)
    self.ax9 = self.figure.add_subplot(8,4,9,sharex=self.ax1,sharey=self.ax1)
    self.ax10 = self.figure.add_subplot(8,4,10,sharex=self.ax1,sharey=self.ax1)
    self.ax11 = self.figure.add_subplot(8,4,11,sharex=self.ax1,sharey=self.ax1)
    self.ax12 = self.figure.add_subplot(8,4,12,sharex=self.ax1,sharey=self.ax1)
    self.ax13 = self.figure.add_subplot(8,4,13,sharex=self.ax5,sharey=self.ax5)
    self.ax14 = self.figure.add_subplot(8,4,14,sharex=self.ax5,sharey=self.ax5)
    self.ax15 = self.figure.add_subplot(8,4,15,sharex=self.ax5,sharey=self.ax5)
    self.ax16 = self.figure.add_subplot(8,4,16,sharex=self.ax5,sharey=self.ax5)
    self.ax17 = self.figure.add_subplot(8,4,17,sharex=self.ax1,sharey=self.ax1)
    self.ax18 = self.figure.add_subplot(8,4,18,sharex=self.ax1,sharey=self.ax1)
    self.ax19 = self.figure.add_subplot(8,4,19,sharex=self.ax1,sharey=self.ax1)
    self.ax20 = self.figure.add_subplot(8,4,20,sharex=self.ax1,sharey=self.ax1)
    self.ax21 = self.figure.add_subplot(8,4,21,sharex=self.ax5,sharey=self.ax5)
    self.ax22 = self.figure.add_subplot(8,4,22,sharex=self.ax5,sharey=self.ax5)
    self.ax23 = self.figure.add_subplot(8,4,23,sharex=self.ax5,sharey=self.ax5)
    self.ax24 = self.figure.add_subplot(8,4,24,sharex=self.ax5,sharey=self.ax5)
    self.ax25 = self.figure.add_subplot(8,4,25,sharex=self.ax1,sharey=self.ax1)
    self.ax26 = self.figure.add_subplot(8,4,26,sharex=self.ax1,sharey=self.ax1)
    self.ax27 = self.figure.add_subplot(8,4,27,sharex=self.ax1,sharey=self.ax1)
    self.ax28 = self.figure.add_subplot(8,4,28,sharex=self.ax1,sharey=self.ax1)
    self.ax29 = self.figure.add_subplot(8,4,29,sharex=self.ax1,sharey=self.ax5)
    self.ax30 = self.figure.add_subplot(8,4,30,sharex=self.ax5,sharey=self.ax5)
    self.ax31 = self.figure.add_subplot(8,4,31,sharex=self.ax5,sharey=self.ax5)
    self.ax32 = self.figure.add_subplot(8,4,32,sharex=self.ax5,sharey=self.ax5)

    if iTrace is None:
        self.ani = animation.FuncAnimation(self.figure, self.plotData,
                                   interval=1000, blit=True)
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
    # TODO: put this in a loop
    #for ax in self.axarr:
    #   ax.cla()

    self.ax1.cla()
    self.ax2.cla()
    self.ax3.cla()
    self.ax4.cla()
    self.ax5.cla()
    self.ax6.cla()
    self.ax7.cla()
    self.ax8.cla()
    self.ax9.cla()
    self.ax10.cla()
    self.ax11.cla()
    self.ax12.cla()
    self.ax13.cla()
    self.ax14.cla()
    self.ax15.cla()
    self.ax16.cla()
    self.ax17.cla()
    self.ax18.cla()
    self.ax19.cla()
    self.ax20.cla()
    self.ax21.cla()
    self.ax22.cla()
    self.ax23.cla()
    self.ax24.cla()
    self.ax25.cla()
    self.ax26.cla()
    self.ax27.cla()
    self.ax28.cla()
    self.ax29.cla()
    self.ax30.cla()
    self.ax31.cla()
    self.ax32.cla()

    plt.setp(self.ax1.get_xticklabels(),visible=False)
    plt.setp(self.ax2.get_xticklabels(),visible=False)
    plt.setp(self.ax3.get_xticklabels(),visible=False)
    plt.setp(self.ax4.get_xticklabels(),visible=False)
    plt.setp(self.ax5.get_xticklabels(),visible=False)
    plt.setp(self.ax6.get_xticklabels(),visible=False)
    plt.setp(self.ax7.get_xticklabels(),visible=False)
    plt.setp(self.ax8.get_xticklabels(),visible=False)
    plt.setp(self.ax9.get_xticklabels(),visible=False)
    plt.setp(self.ax10.get_xticklabels(),visible=False)
    plt.setp(self.ax11.get_xticklabels(),visible=False)
    plt.setp(self.ax12.get_xticklabels(),visible=False)
    plt.setp(self.ax13.get_xticklabels(),visible=False)
    plt.setp(self.ax14.get_xticklabels(),visible=False)
    plt.setp(self.ax15.get_xticklabels(),visible=False)
    plt.setp(self.ax16.get_xticklabels(),visible=False)
    plt.setp(self.ax17.get_xticklabels(),visible=False)
    plt.setp(self.ax18.get_xticklabels(),visible=False)
    plt.setp(self.ax19.get_xticklabels(),visible=False)
    plt.setp(self.ax20.get_xticklabels(),visible=False)
    plt.setp(self.ax21.get_xticklabels(),visible=False)
    plt.setp(self.ax22.get_xticklabels(),visible=False)
    plt.setp(self.ax23.get_xticklabels(),visible=False)
    plt.setp(self.ax24.get_xticklabels(),visible=False)

    plt.setp(self.ax2.get_yticklabels(),visible=False)
    plt.setp(self.ax3.get_yticklabels(),visible=False)
    plt.setp(self.ax4.get_yticklabels(),visible=False)
    plt.setp(self.ax6.get_yticklabels(),visible=False)
    plt.setp(self.ax7.get_yticklabels(),visible=False)
    plt.setp(self.ax8.get_yticklabels(),visible=False)
    plt.setp(self.ax10.get_yticklabels(),visible=False)
    plt.setp(self.ax11.get_yticklabels(),visible=False)
    plt.setp(self.ax12.get_yticklabels(),visible=False)
    plt.setp(self.ax14.get_yticklabels(),visible=False)
    plt.setp(self.ax15.get_yticklabels(),visible=False)
    plt.setp(self.ax16.get_yticklabels(),visible=False)
    plt.setp(self.ax18.get_yticklabels(),visible=False)
    plt.setp(self.ax19.get_yticklabels(),visible=False)
    plt.setp(self.ax20.get_yticklabels(),visible=False)
    plt.setp(self.ax22.get_yticklabels(),visible=False)
    plt.setp(self.ax23.get_yticklabels(),visible=False)
    plt.setp(self.ax24.get_yticklabels(),visible=False)
    plt.setp(self.ax26.get_yticklabels(),visible=False)
    plt.setp(self.ax27.get_yticklabels(),visible=False)
    plt.setp(self.ax28.get_yticklabels(),visible=False)
    plt.setp(self.ax30.get_yticklabels(),visible=False)
    plt.setp(self.ax31.get_yticklabels(),visible=False)
    plt.setp(self.ax32.get_yticklabels(),visible=False)
  
    # in case no data, return an empty plot
    self.plot1 = self.ax1.plot()

    t, adc, frq, ampl, thistimestamp = self.getTraceAndFFT(iTrace=iTrace,chan=0)
    if not (t is None) and not (adc is None):
        self.plot1 = self.ax1.plot(t,adc)
    if not (frq is None) and not (ampl is None):
        self.plot5 = self.ax5.plot(frq, ampl,'r')

    t, adc, frq, ampl, thistimestamp = self.getTraceAndFFT(iTrace=iTrace,chan=1)
    if not (t is None) and not (adc is None):
        self.plot2 = self.ax2.plot(t,adc)
    if not (frq is None) and not (ampl is None):
        self.plot6 = self.ax6.plot(frq, ampl,'r')

    t, adc, frq, ampl, thistimestamp = self.getTraceAndFFT(iTrace=iTrace,chan=2)
    if not (t is None) and not (adc is None):
        self.plot3 = self.ax3.plot(t,adc)
    if not (frq is None) and not (ampl is None):
        self.plot7 = self.ax7.plot(frq, ampl,'r')

    t, adc, frq, ampl, thistimestamp = self.getTraceAndFFT(iTrace=iTrace,chan=3)
    if not (t is None) and not (adc is None):
        self.plot4 = self.ax4.plot(t,adc)
    if not (frq is None) and not (ampl is None):
        self.plot8 = self.ax8.plot(frq, ampl,'r')

    t, adc, frq, ampl, thistimestamp = self.getTraceAndFFT(iTrace=iTrace,chan=4)
    if not (t is None) and not (adc is None):
        self.plot9 = self.ax9.plot(t,adc)
    if not (frq is None) and not (ampl is None):
        self.plot13 = self.ax13.plot(frq, ampl,'r')

    t, adc, frq, ampl, thistimestamp = self.getTraceAndFFT(iTrace=iTrace,chan=5)
    if not (t is None) and not (adc is None):
        self.plot10 = self.ax10.plot(t,adc)
    if not (frq is None) and not (ampl is None):
        self.plot14 = self.ax14.plot(frq, ampl,'r')

    t, adc, frq, ampl, thistimestamp = self.getTraceAndFFT(iTrace=iTrace,chan=6)
    if not (t is None) and not (adc is None):
        self.plot11 = self.ax11.plot(t,adc)
    if not (frq is None) and not (ampl is None):
        self.plot15 = self.ax15.plot(frq, ampl,'r')

    t, adc, frq, ampl, thistimestamp = self.getTraceAndFFT(iTrace=iTrace,chan=7)
    if not (t is None) and not (adc is None):
        self.plot12 = self.ax12.plot(t,adc)
    if not (frq is None) and not (ampl is None):
        self.plot16 = self.ax16.plot(frq, ampl,'r')

    t, adc, frq, ampl, thistimestamp = self.getTraceAndFFT(iTrace=iTrace,chan=8)
    if not (t is None) and not (adc is None):
        self.plot17 = self.ax17.plot(t,adc)
    if not (frq is None) and not (ampl is None):
        self.plot21 = self.ax21.plot(frq, ampl,'r')

    t, adc, frq, ampl, thistimestamp = self.getTraceAndFFT(iTrace=iTrace,chan=9)
    if not (t is None) and not (adc is None):
        self.plot18 = self.ax18.plot(t,adc)
    if not (frq is None) and not (ampl is None):
        self.plot22 = self.ax22.plot(frq, ampl,'r')

    t, adc, frq, ampl, thistimestamp = self.getTraceAndFFT(iTrace=iTrace,chan=10)
    if not (t is None) and not (adc is None):
        self.plot19 = self.ax19.plot(t,adc)
    if not (frq is None) and not (ampl is None):
        self.plot23 = self.ax23.plot(frq, ampl,'r')

    t, adc, frq, ampl, thistimestamp = self.getTraceAndFFT(iTrace=iTrace,chan=11)
    if not (t is None) and not (adc is None):
        self.plot20 = self.ax20.plot(t,adc)
    if not (frq is None) and not (ampl is None):
        self.plot24 = self.ax24.plot(frq, ampl,'r')

    t, adc, frq, ampl, thistimestamp = self.getTraceAndFFT(iTrace=iTrace,chan=12)
    if not (t is None) and not (adc is None):
        self.plot25 = self.ax25.plot(t,adc)
    if not (frq is None) and not (ampl is None):
        self.plot29 = self.ax29.plot(frq, ampl,'r')

    t, adc, frq, ampl, thistimestamp = self.getTraceAndFFT(iTrace=iTrace,chan=13)
    if not (t is None) and not (adc is None):
        self.plot26 = self.ax26.plot(t,adc)
    if not (frq is None) and not (ampl is None):
        self.plot30 = self.ax30.plot(frq, ampl,'r')

    t, adc, frq, ampl, thistimestamp = self.getTraceAndFFT(iTrace=iTrace,chan=14)
    if not (t is None) and not (adc is None):
        self.plot27 = self.ax27.plot(t,adc)
    if not (frq is None) and not (ampl is None):
        self.plot31 = self.ax31.plot(frq, ampl,'r')

    t, adc, frq, ampl, thistimestamp = self.getTraceAndFFT(iTrace=iTrace,chan=15)
    if not (t is None) and not (adc is None):
        self.plot28 = self.ax28.plot(t,adc)
    if not (frq is None) and not (ampl is None):
        self.plot32 = self.ax32.plot(frq, ampl,'r')

    self.figure.text(0.45,0.04,'Time [us]',ha='center',color='blue')
    self.figure.text(0.55,0.04,'Frequency [MHz]',ha='center',color='red')
    self.figure.text(0.042,0.45,'ADC',ha='center',rotation=90,color='blue') 
    self.figure.text(0.04,0.55,'|Y(freq)|',ha='center',rotation=90,color='red') 

    if not (thistimestamp is None):
        self.figure.suptitle(thistimestamp.replace(microsecond=0).isoformat(" "))
    self.canvas.draw()
    return self.plot1

  def getTraceAndFFT(self,iTrace=None,chan=0):
    """
    Gets trace from FEMB and returns 4 1D arrays:
        times, ADC counts, frequencies, Amplitude
    """
    Yfft_total = []
    first = 1
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
        #time.sleep(1.)
        return None, None, None, None, None
    if len(data ) == 0:
        #time.sleep(1.)
        return None, None, None, None, None
    xpoint = []
    ypoint = []
    num = 0

    packetNum = 0
    wordArray = []
    for word in data:
        #print(str(packetNum) + "\t" + str(hex(word)) )
        if str(hex(word)) == "0xface" :
          packetNum = 0
          wordArray = []
        if packetNum > 0 and packetNum < 13 :
          wordArray.append( word )
        if packetNum == 12 :
          chSamp = []
          for i in range(0,16,1):
            chSamp.append(0)
          chSamp[0] = ((wordArray[5] & 0xFFF0 ) >> 4)
          chSamp[1] = ((wordArray[4] & 0xFF00 ) >> 8) | ((wordArray[5] & 0x000F ) << 8)
          chSamp[2] = ((wordArray[4] & 0x00FF ) << 4) | ((wordArray[3] & 0xF000 ) >> 12)
          chSamp[3] = ((wordArray[3] & 0x0FFF ) >> 0)
          chSamp[4] = ((wordArray[2] & 0xFFF0 ) >> 4)
          chSamp[5] = ((wordArray[2] & 0x000F ) << 8) | ((wordArray[1] & 0xFF00 ) >> 8)
          chSamp[6] = ((wordArray[1] & 0x00FF ) << 4) | ((wordArray[0] & 0xF000 ) >> 12)
          chSamp[7] = ((wordArray[0] & 0x0FFF ) >> 0)				
          chSamp[8] = ((wordArray[11] & 0xFFF0 ) >> 4) 
          chSamp[9] = ((wordArray[11] & 0x000F ) << 8) | ((wordArray[10] & 0xFF00 ) >> 8) 
          chSamp[10] = ((wordArray[10] & 0x00FF ) << 4) | ((wordArray[9] & 0xF000 ) >> 12) 
          chSamp[11] = ((wordArray[9] & 0x0FFF ))
          chSamp[12] = ((wordArray[8] & 0xFFF0 ) >> 4)
          chSamp[13] = ((wordArray[8] & 0x000F ) << 8) | ((wordArray[7] & 0xFF00 ) >> 8) 
          chSamp[14] = ((wordArray[7] & 0x00FF ) << 4) | ((wordArray[6] & 0xF000 ) >> 12) 
          chSamp[15] = ((wordArray[6] & 0x0FFF ) )

          xpoint.append(num*0.5)
          ypoint.append( chSamp[ int(chan) ] )
          num = num + 1

        packetNum = packetNum + 1

    #return None, None, None, None, None
    
    #for samp in data:
    #    chNum = ((samp >> 12 ) & 0xF)
    #    sampVal = (samp & 0xFFF)
    #    #print str(chNum) + "\t" + str(sampVal) + "\t" + str( hex(sampVal) )
    #    #if chNum == 0:
    #    xpoint.append(num*0.5)
    #    ypoint.append(sampVal)
    #    num = num + 1
    
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

    return xarr, yarr, frq, Yfft_norm, timestamp
    
def main():
    window = Tk.Tk()
    window.title("FEMB Trace & FFT Viewer")
    trace_fft = TRACE_FFT_WINDOW(window)
    window.mainloop()
