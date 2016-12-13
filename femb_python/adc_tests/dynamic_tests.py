from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals
from __future__ import absolute_import
from builtins import range
from future import standard_library
standard_library.install_aliases()
from ..femb_udp import FEMB_UDP
from ..test_instrument_interface import RigolDG4000
from ..write_root_tree import WRITE_ROOT_TREE
import time
import glob
from uuid import uuid1 as uuid
import numpy
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
        self.NASICS = config.NASICS
        self.femb = FEMB_UDP()
        self.funcgen = RigolDG4000("/dev/usbtmc0")
        self.settlingTime = 0.1
        self.signalLeakageWidthBins = 20
        self.harmonicLeakageWidthBins = 20
        self.nHarmonics = 5 # total harmonic distortion includes up to this harmonic (and S/N excludes them)
        self.offsetV = 1.5
        self.waveformRootFileName = None
        self.loadWaveformRootFileName = None
        self.iRun = 0
        self.nBits = 12

    def analyze(self,fake=False):
        waveforms = {}
        if self.loadWaveformRootFileName:
            waveforms = self.loadWaveforms()
        else:
            for freq in numpy.logspace(3,5.5,2):
                waveforms[freq] = {}
                for amplitude in [0.75,1.25,1.45]:
                    waveforms[freq][amplitude] = self.getSinWaveforms(freq,self.offsetV,amplitude)
            self.funcgen.stop()
        print(waveforms.keys())
        frequencies = sorted(list(waveforms.keys()))
        for iChip in range(self.NASICS):
            for iChan in range(16):
                print(iChip,iChan)
                for freq in frequencies:
                    amplitudes = sorted(list(waveforms[freq].keys()))
                    for amp in amplitudes:
                        waveform = waveforms[freq][amp][iChip][iChan]
                        print("Chip: {}, Chan: {}, Freq: {} Hz, Amp: {} V".format(iChip,iChan,freq,amp))
                        freqStr = ""
                        freqExp = numpy.floor(numpy.log10(freq))
                        freqCoef = freq/10**freqExp
                        freqStr = "{:.0f}e{:.0f}".format(freqCoef,freqExp)
                        outputSuffix = "chip{}_chan{}_freq{}Hz_amp{:.0f}mV".format(iChip,iChan,freqStr,amp*1000)
                        maxAmpFreq, thd, snr, sinad, enob = self.getDynamicParameters(waveform,outputSuffix)
                        print("  maxAmpFreq: {:.2e} THD: {:4.1f} SNR: {:4.1f} SINAD: {:4.1f} ENOB: {:4.2f}".format(maxAmpFreq,thd,snr,sinad,enob))

    def getDynamicParameters(self,data,outputSuffix,fake=False):
        """
        Performs the fft on the input sample data and returns:

            the frequency with maximum amplitude
            total harmonic distortion (THD) of self.nHarmonics harmonics in DB w.r.t. max amplitude
            signal to noise ratio (SNR) amplitude of everything but signal, DC, and harmonics
            signal to noise and distortion ratio (SINAD) amplitude of everything but signal and DC
            effective number of bits (ENOB) computed from SINAD and the formula for ideal noise in terms of bits
        """
        if fake:
            N = 20124
            A = 1.
            freq = 0.235
            phase = 0.12562362376
            freq /= 2. # b/c sample at 2MHz
            t = numpy.arange(N)
            Noise = 0.
            Noise += 1e-6*numpy.random.randn(N)
            #Noise += 1e-8*numpy.sin(2*numpy.pi*t/10.)
            #Noise += 1e-5*numpy.sin(2*numpy.pi*t/6.)
            harmonics = 0.
            for iHarmonic in range(2,10):
              harmonics += 1e-3*10**(-iHarmonic)*A*numpy.sin(2*numpy.pi*t*freq*iHarmonic+phase) + 0.
            data = numpy.zeros(N)
            data += Noise
            data += harmonics
            data += A*numpy.sin(2*numpy.pi*t*freq+phase) + 0.
            true_sinad = (numpy.mean((A*numpy.sin(2*numpy.pi*t*freq))**2))**0.5
            true_sinad /= (numpy.mean(Noise**2))**0.5
            print("true SINAD: ",true_sinad,"=",10*numpy.log10(true_sinad),"dB")
        dataNoDC = data - numpy.mean(data)
        windowedData = self.get7BlackmanHarrisWindow(len(data))*dataNoDC
        #windowedData = self.getHanningWindow(len(data))*dataNoDC
        fft = numpy.fft.rfft(windowedData)
        fftAmplitude = numpy.sqrt(numpy.real(fft*numpy.conj(fft)))
        fftAmplitudeRelative = fftAmplitude/max(fftAmplitude)
        fftAmplitudeRelativeDB = 10*numpy.log10(fftAmplitudeRelative)
        samplePeriod = 0.5 # microsecond -> freqs will be in MHz
        frequencies = numpy.fft.rfftfreq(len(data),samplePeriod)

        iFreqs = numpy.arange(len(frequencies))
        iMax = numpy.argmax(fftAmplitudeRelativeDB)
        goodElements = numpy.logical_or(iFreqs > iMax + self.signalLeakageWidthBins , iFreqs < iMax - self.signalLeakageWidthBins)
        goodElements = numpy.logical_and(iFreqs > self.signalLeakageWidthBins, goodElements) # leakage from DC, just in case any left
        sinad = fftAmplitude[iMax]/fftAmplitude[goodElements].sum()
        sinadDB = 10*numpy.log10(sinad)
        enob = (sinadDB - 1.76) / (6.02)
        #enob = (sinad - 10*numpy.log10(1.5)) / (20*numpy.log10(2))
        
        fig, ax = plt.subplots(figsize=(8,8))
        ax.plot(frequencies,fftAmplitudeRelativeDB,'b-')
        ax.set_xlim(-0.025,1.025)
        ax.set_xlabel("Frequency [MHz]")
        ax.set_ylabel("Amplitude [dB]")
        fig.savefig("fft_{}.png".format(outputSuffix))
        plt.close()

        thdDenom = 0.

        for iHarmonic in range(2,self.nHarmonics+1):
            iBin = self.getHarmonicBin(iMax,iHarmonic,len(fftAmplitudeRelativeDB))

            thdDenom += fftAmplitude[iBin]

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

        thd = fftAmplitude[iMax]/thdDenom
        thdDB = 10*numpy.log10(thd)
        snr = fftAmplitude[iMax]/fftAmplitude[goodElements].sum()
        snrDB = 10*numpy.log10(snr)

        #print("nBins: {}".format(len(fft)))
        #print("Maximum: {} dB, {} MHz, {} element".format(fftAmplitudeRelativeDB[iMax],frequencies[iMax],iMax))
        #print("THD: {} = {} dB".format(thd,thdDB))
        #print("SNR: {} = {} dB".format(snr,snrDB))
        #print("SINAD: ",sinad," = ",sinadDB,"dB")
        #print("ENOB: ",enob,"bits")

        return frequencies[iMax], thdDB, snrDB, sinadDB, enob

    def getSinWaveforms(self,freq,offsetV,amplitudeV,fake=False):
        self.funcgen.startSin(freq,amplitudeV,offsetV)
        if self.waveformRootFileName:
            self.dumpWaveformRootFile(freq,offsetV,amplitudeV)

        result = []
        for iChip in range(self.NASICS):
            result.append([])
            for iChan in range(16):
                waveform = self.getWaveform(iChip,iChan,freq,offsetV,amplitudeV)
                result[iChip].append(waveform)
        self.iRun += 1
        return result

    def dumpWaveformRootFile(self,freq,offsetV,amplitudeV):
        filename = "{}_freq{:.3f}_offset{:.3f}_amplitude{:.3f}.root".format(self.waveformRootFileName,freq,offsetV,amplitudeV)
        wrt = WRITE_ROOT_TREE(self.config,filename,10)
        wrt.run = self.iRun
        wrt.funcType = 2
        wrt.funcFreq = freq
        wrt.funcOffset = offsetV
        wrt.funcAmp = amplitudeV
        wrt.record_data_run()

    def getWaveform(self,iChip,iChan,freq,offsetV,amplitudeV,fake=False):
        """
        Gets an array of ADC counts for a given waveform generator offset, A and freq.
        """

        self.config.selectChannel(iChip,iChan)
        time.sleep(self.settlingTime)

        if not fake:
            samples = []
            raw_data = self.femb.get_data(1)
            
            for samp in raw_data:
                chNum = ((samp >> 12 ) & 0xF)
                if chNum != iChan:
                    print("makeRampHist: chNum {} != iChan {}".format(chNum,iChan))
                    continue
                sampVal = (samp & 0xFFF)
                if self.nBits < 12:
                    sampVal = sampVal >> (12 - self.nBits)
                samples.append(sampVal)
            return numpy.array(samples)
        else:
            raise NotImplementedError()

    def loadWaveforms(self):
        """
        result[freq][amp][iChip][iChan][iSample]
        """
        filenames = glob.glob(self.loadWaveformRootFileName+"*.root")
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
        for mdt in metadataTrees:
            mdt.GetEntry(0)
            md = {
                'funcType': mdt.funcType,
                'funcAmp': mdt.funcAmp,
                'funcOffset': mdt.funcOffset,
                'funcFreq': mdt.funcFreq,
                }
            metadatas.append(md)
            if not mdt.funcAmp in amplitudes:
                amplitudes.add(mdt.funcAmp)
            if not mdt.funcFreq in frequencies:
                frequencies.add(mdt.funcFreq)
        
        result = {}
        for freq in frequencies:
            result[freq] = {}
            for amp in amplitudes:
              thesePoints = []
              for iChip in range(self.config.NASICS):
                thesePoints.append([])
                for iChannel in range(16):
                  thesePoints[iChip].append([])
              for iTree in range(len(metadatas)):
                md = metadatas[iTree]
                if md['funcType'] == 2 and md['funcAmp'] == amp and md['funcFreq'] == freq:
                  tree = trees[iTree]
                  for iEntry in range(tree.GetEntries()):
                      tree.GetEntry(iEntry)
                      iChip = tree.chan//16
                      iChannel = tree.chan % 16
                      adccodes = list(tree.wf)
                      if self.nBits < 12:
                          adccodes = [i >> (12 - self.nBits) for i in adccodes]
                      thesePoints[iChip][iChannel].extend(adccodes)
              result[freq][amp] = thesePoints
        return result

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
        return result

def main():
    from ..configuration.argument_parser import ArgumentParser
    from ..configuration import CONFIG
    parser = ArgumentParser(description="Dynamic (AC) tests of the ADC using FFT")
    parser.addDumpWaveformRootFileArgs()
    parser.addLoadWaveformRootFileArgs()
    parser.addNPacketsArgs(False,10)
    #parser.add_argument("outfilename",help="Output root file name")
    args = parser.parse_args()
  
    config = CONFIG()
  
    dynamic_tests = DYNAMIC_TESTS(config)
    if args.dumpWaveformRootFile:
        dynamic_tests.waveformRootFileName = args.dumpWaveformRootFile
    if args.loadWaveformRootFile:
        dynamic_tests.loadWaveformRootFileName = args.loadWaveformRootFile
    dynamic_tests.analyze()
