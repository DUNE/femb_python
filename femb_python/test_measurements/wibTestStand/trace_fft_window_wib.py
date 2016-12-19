"""
This module contains a class that displays a live ADC readout and its FFT.
Configuration and channel selection are handled elsewhere.
"""
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

import time
import numpy as np
from matplotlib.figure import Figure
from matplotlib import animation
from matplotlib.backends.backend_gtk3cairo import FigureCanvasGTK3Cairo as FigureCanvas
from femb_python.femb_udp import FEMB_UDP

class TRACE_FFT_WINDOW_WIB(Gtk.Window):
  """
  This window displays a live ADC redout and its FFT
  """

  def __init__(self):
    Gtk.Window.__init__(self, title="ADC View Window")

    self.set_default_size(800, 800)

    self.figure = Figure(figsize=(8,8), dpi=100)
    
    sw = Gtk.ScrolledWindow()
    self.add(sw)
    # A scrolled window border goes outside the scrollbars and viewport
    sw.set_border_width(10)
    
    canvas = FigureCanvas(self.figure)  # a Gtk.DrawingArea
    canvas.set_size_request(750, 750)
    sw.add_with_viewport(canvas)
    
    self.show_all()

    self.sw = sw
    self.canvas = canvas

    self.femb = None
    self.reset()

  def reset(self):
    self.femb = FEMB_UDP()
    self.figure.clf()
    self.ax1 = self.figure.add_subplot(211)
    self.ax2 = self.figure.add_subplot(212)
    self.plot1 = self.ax1.plot([],[])
    self.plot2 = self.ax2.plot([],[])
    self.ani = animation.FuncAnimation(self.figure, self.plotData,
                                   interval=1000)#, blit=True)
    self.canvas.draw()

  def plotData(self,iFrame):
    self.ax1.cla()
    self.ax2.cla()
    self.ax1.set_xlabel("Time [us]")
    self.ax1.set_ylabel("Sample Value [ADC Counts]")
    self.ax2.set_xlabel("Frequency [MHz]")
    self.ax2.set_ylabel("|Y(freq)|")
    t, adc, frq, ampl = self.getTraceAndFFT()
    if t == None:
        return None
    self.plot1 = self.ax1.plot(t,adc)
    self.plot2 = self.ax2.plot(frq, ampl,'r')
    self.canvas.draw()
    return self.plot1

  def getTraceAndFFT(self):
    """
    Gets trace from FEMB and returns 4 1D arrays:
        times, ADC counts, frequencies, Amplitude
    """
    Yfft_total = []
    first = 1
    #data = self.femb.get_data(10)
    data = self.femb.get_data_packets(1)
    if data == None:
        #time.sleep(1.)
        return None, None, None, None
    if len(data ) == 0:
        #time.sleep(1.)
        return None, None, None, None
    xpoint = []
    ypoint = []
    num = 0
   
    print("HERE") 
    for samp in data:
        print(samp)

    return None, None, None, None
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
    window = TRACE_FFT_WINDOW_WIB()
    window.connect("delete-event", Gtk.main_quit)
    window.connect("destroy", Gtk.main_quit)
    Gtk.main()
