from ..femb_udp import FEMB_UDP
from ..test_instrument_interface import RigolDG4000
import time
from uuid import uuid1 as uuid
import numpy
import matplotlib.pyplot as plt

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
        self.signalLeakageWidthBins = 50

    def makeAmplitudeSpectrum(self,fake=False):
        data = None
        if fake:
            N = 20124
            A = 1.
            freq = 0.6
            phase = 0.12562362376
            freq /= 2. # b/c sample at 2MHz
            t = numpy.arange(N)
            Noise = 0.
            Noise += 1e-6*numpy.random.randn(N)
            #Noise += 1e-8*numpy.sin(2*numpy.pi*t/10.)
            #Noise += 1e-5*numpy.sin(2*numpy.pi*t/6.)
            harmonics = 0.
            harmonics += 1e-5*A*numpy.sin(2*numpy.pi*t*freq*2.+phase) + 0.
            harmonics += 1e-7*A*numpy.sin(2*numpy.pi*t*freq*3.+phase) + 0.
            data = numpy.zeros(N)
            data += Noise
            data += harmonics
            data += A*numpy.sin(2*numpy.pi*t*freq+phase) + 0.
            true_sinad = (numpy.mean((A*numpy.sin(2*numpy.pi*t*freq))**2))**0.5
            true_sinad /= (numpy.mean(Noise**2))**0.5
            print("true SINAD: ",true_sinad,"=",10*numpy.log10(true_sinad),"dB")
        dataNoDC = data - numpy.mean(data)
        windowedData = self.getWindow(len(data))*dataNoDC
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

        print("Maximum: {} dB, {} MHz, {} element".format(fftAmplitudeRelativeDB[iMax],frequencies[iMax],iMax))
        print("SINAD: ",sinad," = ",sinadDB,"dB")
        print("ENOB: ",enob,"bits")
        
        fig, ax = plt.subplots(figsize=(8,8))
        ax.plot(frequencies,fftAmplitudeRelativeDB,'b-')
        ax.set_xlim(-0.025,1.025)
        ax.set_xlabel("Frequency [MHz]")
        ax.set_ylabel("Amplitude [dB]")
        fig.savefig("fft.png")

    def getWindow(self,N):
        #"""
        #Hanning window
        #"""
        #t = numpy.arange(N)
        #return 0.5 - 0.5 * numpy.cos(2*numpy.pi * t / N)
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
        result = iHarmonic * iCarrier
        

def main():
    from ..configuration.argument_parser import ArgumentParser
    from ..configuration import CONFIG
    from ..configuration.config_file_finder import get_env_config_file, config_file_finder
    parser = ArgumentParser(description="Dynamic (AC) tests of the ADC using FFT")
    parser.addConfigFileArgs()
    parser.addNPacketsArgs(False,10)
    #parser.add_argument("outfilename",help="Output root file name")
    args = parser.parse_args()
  
    config_filename = args.config
    if config_filename:
      config_filename = config_file_finder(config_filename)
    else:
      config_filename = get_env_config_file()
    config = CONFIG(config_filename)
  
    dynamic_tests = DYNAMIC_TESTS(config)
    dynamic_tests.makeAmplitudeSpectrum(True)
