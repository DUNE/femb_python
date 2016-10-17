#!/usr/bin/python3.4
import sys 
import string
import time
import math

from ..femb_udp import FEMB_UDP
from ..configuration import CONFIG, get_env_config_file

def main():
    config_file = get_env_config_file()
    femb_config = CONFIG(config_file)
    noiseMeasurements = []
    for ch in range(0,128,1):
        chan = int(ch)
        femb_config.selectChannel( chan/16, chan % 16)
        time.sleep(0.05)
        data = femb_config.femb.get_data(1)
        meanAndRms = calcMeanAndRms(data)
        rms = 0
        if len(meanAndRms) == 2 :
            rms = round(meanAndRms[1],2)
        #print meanAndRms[0]
        #print meanAndRms[1]
        #print "Ch " + str(ch) + "\tRMS " + str(rms)
        noiseMeasurements.append(rms)
    
    for asic in range(0,8,1):
        line = "ASIC " + str(asic)
        baseCh = int(asic)*16
        for ch in range(baseCh,baseCh + 16,1):
            line = line + "\t" + str( noiseMeasurements[ch])
        print( line )

def calcMeanAndRms( data ):
    mean = 0
    count = 0
    for samp in data:
        if (samp & 0x3F) == 0x0 or (samp & 0x3F) == 0x3F:
            continue
        mean = mean + int(samp)
        count = count + 1
    if count > 0 :
        mean = mean / float(count)
    else:
        mean = 0

    rms = 0
    count = 0
    for samp in data:
        if (samp & 0x3F) == 0x0 or (samp & 0x3F) == 0x3F:
            continue
        rms = rms + (samp - mean)*(samp-mean)
        count = count + 1
    if count > 1 :
        rms = math.sqrt( rms / float(count - 1 ) )
    else:
        rms = 0

    return (mean,rms)

