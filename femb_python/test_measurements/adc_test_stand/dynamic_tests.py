from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals
from __future__ import absolute_import
from builtins import range
from future import standard_library
standard_library.install_aliases()
from ...femb_udp import FEMB_UDP
from ...test_instrument_interface import RigolDG4000
from ...write_root_tree import WRITE_ROOT_TREE
import sys
import os.path
import time
import glob
from uuid import uuid1 as uuid
import numpy
import matplotlib
if os.path.basename(sys.argv[0]) == "femb_adc_dynamic_tests":
    print("Using matplotlib AGG backend")
    matplotlib.use("AGG")
import matplotlib.pyplot as plt
import ROOT

class DYNAMIC_TESTS(object):
    """
    Dynamic (ADC) tests of the ADC using FFT
    """

    def __init__(self,config):
        """
        config is a femb_python.configuration.CONFIG object
        """
        self.config = config
        self.signalLeakageWidthBins = 20
        self.harmonicLeakageWidthBins = 20
        self.nHarmonics = 5 # total harmonic distortion includes up to this harmonic (and S/N excludes them)
        self.nBits = 12

    def analyze(self,fileprefix,diagnosticPlots=True,debugPlots=False):
        waveforms, adcSerial = self.loadWaveforms(fileprefix)
        frequencies = sorted(list(waveforms.keys()))
        #frequencies = frequencies[:3]
        amplitudes = []
        for freq in frequencies:
            for amp in waveforms[freq]:
              if not amp in amplitudes:
                amplitudes.append(amp)
        amplitudes.sort()
        chipstats = {}
        for iChan in range(16):
        #for iChan in range(1):
            #print(iChan)
            chanstats = {}
            for amp in amplitudes:
                chanstats[amp] = {}
                for freq in frequencies:
                    chanstats[amp][freq] = {}
                    waveform = waveforms[freq][amp][iChan]
                    if diagnosticPlots:
                        print("Chip: {}, Chan: {}, Freq: {} Hz, Amp: {} V".format(adcSerial,iChan,freq,amp))
                    freqStr = ""
                    freqExp = numpy.floor(numpy.log10(freq))
                    freqCoef = freq/10**freqExp
                    freqStr = "{:.0f}e{:.0f}".format(freqCoef,freqExp)
                    outputSuffix = "chip{}_chan{}_freq{}Hz_amp{:.0f}mV".format(adcSerial,iChan,freqStr,amp*1000)
                    maxAmpFreq, thd, snr, sinad, enob = self.getDynamicParameters(waveform,outputSuffix,debugPlots=debugPlots)
                    deltaFreqRel = (maxAmpFreq*1e6 - freq)/freq
                    if abs(deltaFreqRel) > 1e-2:
                        print("Warning: Chip: {} Channel: {} Frequency: {:.2g} Hz Amplitude: {:.2f} V FFT peak doesn't match input frequency, skipping. fft freq - input freq relative error: {:.2%}".format(adcSerial,iChan,freq,amp,deltaFreqRel))
                        #chanstats[amp][freq]['thds'] = float('nan')
                        #chanstats[amp][freq]['snrs'] = float('nan')
                        chanstats[amp][freq]['sinads'] = float('nan')
                        #chanstats[amp][freq]['enobs'] = float('nan')
                    else:
                        if diagnosticPlots:
                            print("  THD: {:4.1f} SNR: {:4.1f} SINAD: {:4.1f} ENOB: {:4.2f}".format(thd,snr,sinad,enob))
                        #chanstats[amp][freq]['thds'] = thd
                        #chanstats[amp][freq]['snrs'] = snr
                        chanstats[amp][freq]['sinads'] = sinad
                        #chanstats[amp][freq]['enobs'] = enob
            chipstats[iChan] = chanstats
        allstats = chipstats

        # Now put out plots
        if diagnosticPlots:
            figmanys = []
            for iKey, key in enumerate(['thds','snrs','sinads']):
                figmanys.append(plt.figure(figsize=(8,8)))
            # setup summary figures
            manyaxeses = []
            for iKey, key in enumerate(['thds','snrs','sinads']):
                figmany = figmanys[iKey]
                figmany.clf()
                manyaxes = []
                for iChan in range(16):
                    manyaxes.append(figmany.add_subplot(4,4,iChan+1))
                    manyaxes[iChan].set_xlim(0,1)
                    manyaxes[iChan].set_ylim(0,60)
                    if key == "thds":
                      manyaxes[iChan].set_ylim(-80,0)
                    manyaxes[iChan].set_title("Channel: {}".format(iChan),{'fontsize':'small'})
                    xticks = [0,0.5,1]
                    manyaxes[iChan].set_xticks(xticks)
                    if iChan % 4 != 0:
                        manyaxes[iChan].set_yticklabels([])
                    else:
                        manyaxes[iChan].set_ylabel("{} [dB]".format(key[:-1].upper()))
                    if iChan // 4 != 3:
                        manyaxes[iChan].set_xticklabels([])
                    else:
                        manyaxes[iChan].set_xlabel("Frequency [MHz]")
                        manyaxes[iChan].set_xticklabels(["0","0.5","1"])
                manyaxeses.append(manyaxes)
            # do analysis
            for iChan in range(16):
            #for iChan in range(1):
                chanstats = allstats[iChan]
                for iKey, key in enumerate(['thds','snrs','sinads']):
                    fig, ax = plt.subplots(figsize=(8,8))
                    for amp in amplitudes:
                        freqs = numpy.array(chanstats[amp]['freqs'])
                        ax.plot(freqs/1e6,chanstats[amp][key],label="{:.2f} V".format(amp))
                        manyaxeses[iKey][iChan].plot(freqs/1e6,chanstats[amp][key],label="{:.2f} V".format(amp))
                    ax.set_xlabel("Frequency [MHz]")
                    ax.set_ylabel("{} [dB]".format(key[:-1].upper()))
                    ax.set_xlim(0,1)
                    ax.set_ylim(0,60)
                    if key == "thds":
                      ax.set_ylim(-80,0)
                    ax.legend()
                    fig.savefig("{}_chip{}_chan{}.png".format(key,adcSerial,iChan))
                    plt.close(fig)
            for iKey, key in enumerate(['thds','snrs','sinads']):
              figmanys[iKey].savefig("{}_chip{}.png".format(key,adcSerial))
              plt.close(figmanys[iKey])

        return allstats

    def getDynamicParameters(self,data,outputSuffix,fake=False,debugPlots=False):
        """
        Performs the fft on the input sample data and returns:

            the frequency with maximum amplitude (MHz)
            total harmonic distortion (THD) of self.nHarmonics harmonics in DB w.r.t. max amplitude in dBc
            signal to noise ratio (SNR) amplitude of everything but signal, DC, and harmonics in dBc
            signal to noise and distortion ratio (SINAD) amplitude of everything but signal and DC in dBc
            effective number of bits (ENOB) computed from SINAD and the formula for ideal noise in terms of bits in dBc
        """
        if fake:
            N = 20124
            A = 1.
            freq = 5e-1
            #freq = 100.
            #phase = 0.12562362376
            phase = 0.
            freq /= 2. # b/c sample at 2MHz
            t = numpy.arange(N)
            Noise = 0.
            Noise += 1e-2*numpy.random.randn(N)
            #Noise += 1e-8*numpy.sin(2*numpy.pi*t/10.)
            #Noise += 1e-5*numpy.sin(2*numpy.pi*t/6.)
            harmonics = 0.
            for iHarmonic in range(2,10):
              harmonics += 1e-3*10**(-iHarmonic)*A*numpy.sin(2*numpy.pi*t*freq*iHarmonic+phase) + 0.
            data = numpy.zeros(N)
            data += Noise
            #data += harmonics
            data += A*numpy.sin(2*numpy.pi*t*freq+phase) + 0.
        dataNoDC = data - numpy.mean(data)
        #windowedData = dataNoDC
        windowedData = self.get7BlackmanHarrisWindow(len(data))*dataNoDC
        #windowedData = self.getHanningWindow(len(data))*dataNoDC
        fft = numpy.fft.rfft(windowedData)
        fftPower = numpy.real(fft*numpy.conj(fft))
        fftPower *= 2 / len(data)
        fftPowerRelative = fftPower/max(fftPower)
        fftPowerRelativeDB = 10*numpy.log10(fftPowerRelative)
        samplePeriod = 0.5 # microsecond -> freqs will be in MHz
        frequencies = numpy.fft.rfftfreq(len(data),samplePeriod)

        iFreqs = numpy.arange(len(frequencies))
        iMax = numpy.argmax(fftPowerRelativeDB)
        goodElements = numpy.logical_or(iFreqs > iMax + self.signalLeakageWidthBins , iFreqs < iMax - self.signalLeakageWidthBins)
        goodElements = numpy.logical_and(iFreqs > self.signalLeakageWidthBins, goodElements) # leakage from DC, just in case any left
        sinad = fftPower[iMax]/fftPower[goodElements].sum()
        sinadDB = 10*numpy.log10(sinad)
        enob = (sinadDB - 1.76) / (6.02)
        #enob = (sinad - 10*numpy.log10(1.5)) / (20*numpy.log10(2))
        
        if debugPlots:
            fig, ax = plt.subplots(figsize=(8,8))
            ax.plot(frequencies,fftPowerRelativeDB,'b-')
            ax.set_xlim(-0.025,1.025)
            ax.set_xlabel("Frequency [MHz]")
            ax.set_ylabel("Power [dB]")
            fig.savefig("fft_{}.png".format(outputSuffix))
            #fig.show()
            #input("Press Enter to continue...")
            plt.close(fig)

        thd = 0.

        #print(fft.shape,fftAmplitude.shape,fftAmplitudeRelative.shape,fftAmplitudeRelativeDB.shape,len(fftAmplitudeRelativeDB))
        for iHarmonic in range(2,self.nHarmonics+1):
            iBin = self.getHarmonicBin(iMax,iHarmonic,len(fftPowerRelativeDB))
            #print(iBin)

            thd += fftPower[iBin]

            goodElements = numpy.logical_and(goodElements,
                                        numpy.logical_or(
                                                iFreqs < iBin - self.harmonicLeakageWidthBins,
                                                iFreqs > iBin + self.harmonicLeakageWidthBins
                                            )
                                    )

            #print("iHarmonic: {}, iBin: {}, freq: {} MHz, Amplitude: {} dB".format(iHarmonic,iBin,frequencies[iBin],fftAmplitudeRelativeDB[iBin]))
            #ax.cla()
            #ax.plot(fftAmplitudeRelativeDB,'b-')
            #ax.axvline(iBin,c='r')
            #ax.set_xlim(iBin-20,iBin+20)
            #fig.savefig("fft_{}.png".format(iHarmonic))

        thdRatio = thd/fftPower[iMax]
        thdDB = 10*numpy.log10(thdRatio)
        #print("thd: {} power, thdRatio: {}, thdDB: {} dB".format(thd, thdRatio, thdDB))
        snr = fftPower[iMax]/fftPower[goodElements].sum()
        #print("noise: {} power".format(fftPower[goodElements].sum()))
        #print("snr: {} frac".format(snr))
        snrDB = 10*numpy.log10(snr)

        #print("nBins: {}".format(len(fft)))
        #print("Maximum: {} dB, {} MHz, {} element".format(fftAmplitudeRelativeDB[iMax],frequencies[iMax],iMax))
        #print("THD: {} = {} dB".format(thd,thdDB))
        #print("SNR: {} = {} dB".format(snr,snrDB))
        #print("SINAD: ",sinad," = ",sinadDB,"dB")
        #print("ENOB: ",enob,"bits")

        return frequencies[iMax], thdDB, snrDB, sinadDB, enob

    def dumpWaveformRootFile(self,freq,offsetV,amplitudeV):
        filename = "{}_freq{:.3f}_offset{:.3f}_amplitude{:.3f}.root".format(self.waveformRootFileName,freq,offsetV,amplitudeV)
        wrt = WRITE_ROOT_TREE(self.config,filename,10)
        wrt.run = self.iRun
        wrt.funcType = 2
        wrt.funcFreq = freq
        wrt.funcOffset = offsetV
        wrt.funcAmp = amplitudeV
        wrt.record_data_run()

    def loadWaveforms(self,fileprefix):
        """
        result[freq][amp][iChan][iSample]
        """
        filenames = glob.glob(fileprefix+"_functype2_"+"*.root")
        files = []
        trees = []
        metadataTrees = []
        for fn in filenames:
            f = ROOT.TFile(fn)
            files.append(f)
            trees.append(f.Get("femb_wfdata"))
            metadataTrees.append(f.Get("metadata"))
        metadatas = []
        amplitudes = set()
        frequencies = set()
        adcSerials = set()
        for mdt in metadataTrees:
            mdt.GetEntry(0)
            md = {
                'funcType': mdt.funcType,
                'funcAmp': mdt.funcAmp,
                'funcOffset': mdt.funcOffset,
                'funcFreq': mdt.funcFreq,
                'adcSerial': mdt.adcSerial
                }
            metadatas.append(md)
            if not mdt.funcAmp in amplitudes:
                amplitudes.add(mdt.funcAmp)
            if not mdt.funcFreq in frequencies:
                frequencies.add(mdt.funcFreq)
            if not mdt.adcSerial in adcSerials:
                adcSerials.add(mdt.adcSerial)
        if len(adcSerials) > 1:
            raise Exception("fileprefix '{}' matches files with more than one ADC serial number, only one serial number allowed at a time")
        elif len(adcSerials) == 0:
            raise Exception("fileprefix '{}' doesn't match to any files with functype2.")
        result = {}
        for freq in frequencies:
            result[freq] = {}
            for amp in amplitudes:
              thesePoints = []
              for iChannel in range(16):
                  thesePoints.append([])
              for iTree in range(len(metadatas)):
                md = metadatas[iTree]
                if md['funcType'] == 2 and md['funcAmp'] == amp and md['funcFreq'] == freq:
                  tree = trees[iTree]
                  for iEntry in range(tree.GetEntries()):
                      tree.GetEntry(iEntry)
                      iChannel = tree.chan
                      adccodes = list(tree.wf)
                      if self.nBits < 12:
                          adccodes = [i >> (12 - self.nBits) for i in adccodes]
                      thesePoints[iChannel].extend(adccodes)
              result[freq][amp] = thesePoints
        return result, adcSerials.pop()

    def getHanningWindow(self,N):
        """
        Hanning window
        """
        t = numpy.arange(N)
        return 0.5 - 0.5 * numpy.cos(2*numpy.pi * t / N)

    def get7BlackmanHarrisWindow(self,N):
        """
        7 term blackman-harris from 
        http://zone.ni.com/reference/en-XX/help/372058H-01/rfsapropref/pnirfsa_spectrum.fftwindowtype/
        """
        w = numpy.arange(N) * 2 * numpy.pi / N
        a0 = 0.27105140069342
        a1 = 0.43329793923448
        a2 = 0.21812299954311
        a3 = 0.06592544638803
        a4 = 0.01081174209837
        a5 = 0.00077658482522
        a6 = 0.00001388721735
        cos = numpy.cos
        result = a0 - a1*cos(w) + a2*cos(2*w) - a3*cos(3*w) + a4*cos(4*w) - a5*cos(5*w) + a6*cos(6*w)
        return result

    def getHarmonicBin(self,iCarrier,iHarmonic,nBins):
        """
        Gets the bin corresponding to the possibly aliased frequency 
        for iHarmonic of the carrier freqency given by iCarrier for 
        a nBins length real FFT
        """
        result = iHarmonic * iCarrier + iHarmonic # not sure why + iHarmonic helps
        result = result % (nBins*2)
        if result >= nBins:
            result = 2*nBins - result
        if result == nBins:
            result = 0
        return result

def main():
    from ...configuration.argument_parser import ArgumentParser
    from ...configuration import CONFIG
    parser = ArgumentParser(description="Dynamic (AC) tests of the ADC using FFT")
    parser.add_argument("infileprefix",help="Input file prefix. A string like 'adcTestData_2016-12-14T11:41:12' that is the beginning of the ROOT file names created by femb_adc_collect_data.")
    parser.add_argument("-q", "--quiet",help="Disables output plots and printing, just dumps stats to stdout.",action='store_true')
    parser.add_argument("-d", "--debug",help="Enables extra debug plots.",action='store_true')
    args = parser.parse_args()
  
    config = CONFIG()
  
    dynamic_tests = DYNAMIC_TESTS(config)
    stats = dynamic_tests.analyze(args.infileprefix,diagnosticPlots=not args.quiet, debugPlots=args.debug)
    if args.quiet:
        print(stats)
