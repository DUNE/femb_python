#!/usr/bin/python3.4

import sys 
import string
import time

import numpy as np
from matplotlib import pyplot

from .femb_udp_cmdline import FEMB_UDP

from pylab import rcParams
rcParams['figure.figsize'] = 16, 8

def main():
    femb = FEMB_UDP()
    
    pyplot.ion()
    pyplot.show()
    
    fig, ax = pyplot.subplots(2, 1)
    
    Yfft_total = []
    first = 1

    while 1:
        data = femb.get_data(10)
        if data == None:
            time.sleep(1.)
            continue
        if len(data ) == 0:
            time.sleep(1.)
            continue
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
            time.sleep(0.1)
            continue
    
        pos = 0
        Yfft_norm = []
        for bin in Yfft_total:
            Yfft_norm.append( bin / total)
    
        ax[0].cla()
        ax[1].cla()
        ax[0].plot(xarr,yarr)
        ax[0].set_xlabel('Time [us]')
        ax[0].set_ylabel('Sample Value (ADC counts)')
        #ax[1].plot(frq,abs(Yfft),'r') # plotting the spectrum
        ax[1].plot(frq,Yfft_norm,'r') # plotting the spectrum
        ax[1].set_xlabel('Freq (MHz)')
        ax[1].set_ylabel('|Y(freq)|')
    
        pyplot.draw()
        time.sleep(0.1)
        #pyplot.clf()
	
if __name__ == "__main__":
    main()
