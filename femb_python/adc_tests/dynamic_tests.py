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
        self.signalLeakageWidthBins = 25

    def makePowerSpectrum(self,fake=False):
        data = None
        if fake:
            N = 2124
            A = 1e6
            Noise = 5.*numpy.random.randn(N)
            t = numpy.arange(N)
            freq = 5.
            data = numpy.zeros(N)
            data += Noise
            data += A*numpy.sin(2*numpy.pi*t/freq) + 0.
            true_sinad = (numpy.mean((A*numpy.sin(2*numpy.pi*t/freq))**2))**0.5
            true_sinad /= (numpy.mean(Noise**2))**0.5
            print("true SINAD: ",true_sinad,"=",10*numpy.log10(true_sinad),"dB")
        dataNoDC = data - numpy.mean(data)
        windowedData = self.getWindow(len(data))*dataNoDC
        fft = numpy.fft.rfft(windowedData)
        fftPower = numpy.real(fft*numpy.conj(fft))
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

        print("Maximum: {} dB, {} MHz, {} element".format(fftPowerRelativeDB[iMax],frequencies[iMax],iMax))
        print("SINAD: ",sinad," = ",sinadDB,"dB")
        print("ENOB: ",enob,"bits")
        
        fig, ax = plt.subplots(figsize=(8,8))
        ax.plot(frequencies,fftPowerRelativeDB,'b-')
        ax.set_xlim(-0.025,1.025)
        ax.set_xlabel("Frequency [MHz]")
        ax.set_ylabel("Power [dB]")
        fig.savefig("fft.png")

    def getWindow(self,N):
        """
        Hanning window
        """
        t = numpy.arange(N)
        return 0.5 - 0.5 * numpy.cos(2*numpy.pi * t / N)
        

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
    dynamic_tests.makePowerSpectrum(True)