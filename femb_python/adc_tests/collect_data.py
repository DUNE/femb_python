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
import datetime
import glob
from uuid import uuid1 as uuid
import numpy
import matplotlib.pyplot as plt
import ROOT

class COLLECT_DATA(object):
    """
    Collect data for ADC tests
    """

    def __init__(self,config,nPackets):
        """
        config is a femb_python.configuration.CONFIG object
        """
        self.config = config
        self.NASICS = config.NASICS
        self.femb = FEMB_UDP()
        self.funcgen = RigolDG4000("/dev/usbtmc0")
        self.settlingTime = 0.1 # second
        self.maxTries = 1000
        self.fitMinV = 0.5
        self.fitMaxV = 2.5
        self.nPackets = nPackets
        self.fileprefix = None
        self.nBits = 12

    def getData(self):
        """
        Creates histograms of data doing a linear ramp of 
        the full ADC range + 10% on each end.

        Returns (codeHists, codeMod12Hists, bitHists):
            where each one is a list of dicts of histograms, 
            and the histograms are just arrays of counts.

            codeHists[iChip][iChan][iCode] = count
            bitHists[iChip][iChan][iBit] = count
        """
        startDateTime = datetime.datetime.now().replace(microsecond=0).isoformat()
        self.fileprefix = "adcTestData_{}".format(startDateTime)

        linearFitData = self.doLinearFit(numpy.linspace(0.0,3.5,15))

        fig, ax = plt.subplots(figsize=(8,8))
        codeHists = []
        bitHists = []
        for iChip in range(self.NASICS):
            for iChan in range(16):
                x0 = None
                FSR = None
                try:
                  x0 = linearFitData[iChip][iChan]["x0"]
                  FSR = linearFitData[iChip][iChan]["FSR"]
                except KeyError:
                  print("Error: Linear fit failed, not recording data for chip {} chan {}".format(iChip,iChan))
                if x0:
                    xLow = x0 + 0.1*FSR
                    xHigh = x0 + 0.9*FSR
                    if xHigh > 3.5: 
                        xHigh = 3.5
                    if xLow < 0.:
                        xLow = 0.
                    ## Ramp
                    freq = 734
                    self.funcgen.startRamp(freq,xLow,xHigh)
                    self.config.selectChannel(iChip,iChan)
                    time.sleep(self.settlingTime)
                    offsetV = (xLow + xHigh)*0.5
                    amplitudeV = (xLow - xHigh)*0.5
                    thisfileprefix = self.fileprefix + "_chip{}_chan{}".format(iChip,iChan)
                    self.dumpWaveformRootFile(thisfileprefix,3,freq,offsetV,amplitudeV)
                    ## Sin
                    for freq in numpy.logspace(3.,6.,6): #1kHz to 1MHz
                      offsetV = x0 + 0.5*FSR
                      amplitudeV = FSR*0.5
                      self.funcgen.startSin(freq,amplitudeV,offsetV)
                      self.dumpWaveformRootFile(thisfileprefix,2,freq,offsetV,amplitudeV,self.femb.MAX_NUM_PACKETS)
        for freq in numpy.logspace(3.,6.,6): #1kHz to 1MHz
          for amplitudeV in [0.25,0.75,1.25]:
            offsetV = 1.5
            self.funcgen.startSin(freq,amplitudeV,offsetV)
            self.dumpWaveformRootFile(self.fileprefix,2,freq,offsetV,amplitudeV)
        self.funcgen.stop()
        return codeHists,bitHists

    def doLinearFit(self,voltageList):
        """
        Performs a linear fit to the average ADC value for various voltages

        voltageList: list of voltage values in V to check
        nPackets: number of packets to average over for each voltage

        returns 2D list of dicts:

             result[iChip][iChan]["x0" or "x0err" or "m" or "merr", or "chi2/ndf" or 'FSR']

             where x0 is the x intercept in and x0err is the x intercept error, both in volts.
             m is the number of ADC counts per input V, and merr is its error in counts per V.
             chi2/ndf is the quality of fit and FSR is the estimated full scale range in V--the difference 
                between the value for ADC = 0 to the value of ADC=2^12

             They will be set to None if the fit fails
        """
        data = self.getADCDataDC(voltageList)
        fig, ax = plt.subplots(figsize=(8,8))
        figmany = plt.figure(figsize=(8,8))

        result = []
        for iChip in range(self.NASICS):
            result.append([])
            figmany.clf()
            manyaxes = []
            for iChan in range(16):
                manyaxes.append(figmany.add_subplot(4,4,iChan+1))
                manyaxes[iChan].set_xlim(0,3.5)
                manyaxes[iChan].set_ylim(0,2**self.nBits)
                manyaxes[iChan].set_title("Channel: {}".format(iChan),{'fontsize':'small'})
                manyaxes[iChan].set_xticks([0,1,2,3])
                yticks = [x*1024 for x in range(5)]
                manyaxes[iChan].set_yticks(yticks)
                if iChan % 4 != 0:
                    manyaxes[iChan].set_yticklabels([])
                else:
                    manyaxes[iChan].set_ylabel("ADC Counts")
                if iChan // 4 != 3:
                    manyaxes[iChan].set_xticklabels([])
                else:
                    manyaxes[iChan].set_xlabel("Voltage [V]")
            for iChan in range(16):
                voltages = numpy.array(data[iChip][iChan]["vlt"])
                averages = numpy.array(data[iChip][iChan]["avg"])
                errors = numpy.array(data[iChip][iChan]["err"])

                x0, x0err, m, merr, chi2ondf, fsr = self.fitLineToData(voltages,averages,errors)
                result[iChip].append({
                    "x0": x0,
                    "x0err": x0err,
                    "m": m,
                    "merr": merr,
                    "chi2/ndf": chi2ondf,
                    "FSR": fsr,
                })
                if x0:
                  print("Chip: {} Chan: {:2} x0: {:8.2g} +/- {:8.2g} mV m: {:8.2g} +/- {:8.2g} Counts/mV, chi2/ndf: {:10.2g}, FSR: {:10.3g} V".format(iChip,iChan,x0*1000.,x0err*1000.,m/1000.,merr/1000.,chi2ondf, fsr))
                  lineVoltages = numpy.array([self.fitMinV,self.fitMaxV])
                  ax.plot(lineVoltages,m*(lineVoltages-x0),"b-",label="Fit")
                  manyaxes[iChan].plot(lineVoltages,m*(lineVoltages-x0),"b-",label="Fit")
                else:
                  print("Chip: {} Chan: {:2} fit failed".format(iChip,iChan))
                ax.errorbar(voltages,averages,fmt="ko",yerr=errors,xerr=0.,label="Data")
                manyaxes[iChan].plot(voltages,averages,"ko",label="Data",markersize=3)
                ax.set_xlabel("Voltage [V]")
                ax.set_ylabel("ADC Output")
                ax.set_xlim(0,3.5)
                ax.set_ylim(0,2**self.nBits)
                ax.set_title("ADC Chip {} Channel {}".format(iChip,iChan))
                ax.legend(loc='best')
                filename = "ADC_Linearity_Chip{}_Chan{}".format(iChip,iChan)
                fig.savefig(filename+".png")
                #fig.savefig(filename+".pdf")
                ax.cla()
            figmany.savefig("ADC_Linearity_Chip{}.png".format(iChip))
            #figmany.savefig("ADC_Linearity_Chip{}.pdf".format(iChip))
        return result

    def fitLineToData(self,voltages,counts,errors):
        """
        Performs a least squares fit of y = counts +/- errors, x = voltages

        returns x-intercept [V], x-intercept error [V], slope [Counts/V], slope error [Counts/V], chi2/ndf, estimated full scale range [V]
        """
        assert(len(voltages)==len(counts))
        assert(len(errors)==len(counts))
        graph = ROOT.TGraphErrors()
        for iPoint in range(len(voltages)):
            graph.SetPoint(iPoint,voltages[iPoint],counts[iPoint])
            graph.SetPointError(iPoint,0.,errors[iPoint])
        func = ROOT.TF1(uuid().hex,"[0]*(x-[1])",self.fitMinV,self.fitMaxV)
        fitresult = graph.Fit(func,"QFMEN0S","",self.fitMinV,self.fitMaxV)

        ndf = len(counts) - 2
        chi2ondf = None
        m = None
        x0 = None
        merr = None
        x0err = None
        fsr = None

        valid = fitresult.IsValid()
        if valid:
            chi2ondf = fitresult.Chi2() / ndf
            m = fitresult.Value(0)
            x0 = fitresult.Value(1)
            merr = fitresult.ParError(0)
            x0err = fitresult.ParError(1)
            fsr = 2**self.nBits / m + x0
        return x0, x0err, m, merr, chi2ondf, fsr

    def getADCDataDC(self,voltages):
        """
        Finds the average value and error on the average for 
        multiple voltages for all of the chips and channels.

        voltages is a list of voltage values to get data for.
        averages over nPackets worth of data

        Returns a 2D list of dictinoaries of lists: 

             result[iChip][iChan]["avg" or "err" or "vlt"][iSample]

        """
        data = {}
        self.funcgen.stop()
        for voltage in voltages:
            self.funcgen.startDC(voltage)
            time.sleep(self.settlingTime)
            avgs, errs = self.getAverageForAllChannels()
            data[voltage] = { "avg": avgs, "err": errs}
            self.dumpWaveformRootFile(self.fileprefix,1,0,voltage,0)
        self.funcgen.stop()

        ####data setup:
        #### data[voltage]["avg" or "err"][iChip][iChan]

        # now put the data inside out in a more useful way
        voltages = list(data.keys())
        voltages.sort()

        result = []
        for iChip in range(self.NASICS):
            result.append([])
            for iChan in range(16):
                avgs = []
                errs = []
                for voltage in voltages:                
                    avgs.append(data[voltage]["avg"][iChip][iChan])
                    errs.append(data[voltage]["err"][iChip][iChan])
                d = { "vlt":numpy.array(voltages), "avg":numpy.array(avgs), "err": numpy.array(errs)}
                result[iChip].append(d)
        return result

    def getAverageForAllChannels(self):
        """
        Returns 2D arrays for all of the chips and channels
        of the average and error on the average.

        averages over nPackets worth of data
        """
        averages = []
        errors = []
        for iChip in range(self.NASICS):
            averages.append([])
            errors.append([])
            for iChan in range(16):
                avg, err = self.getAverage(iChip,iChan)
                averages[iChip].append(avg)
                errors[iChip].append(err)
        return averages, errors
    
    def getAverage(self,iChip,iChan):
        """
        Find iChip iChan average for nPackets worth of data
        for whatever signal is going into the ADC now.

        Returns the average and its statistical error
        """
        samples = []
        self.config.selectChannel(iChip,iChan)
        time.sleep(0.01)

        raw_data = self.femb.get_data(self.nPackets)
        
        for samp in raw_data:
            chNum = ((samp >> 12 ) & 0xF)
            if chNum != iChan:
                print("computeAverage: chNum {} != iChan {}".format(chNum,iChan))
                continue
            sampVal = (samp & 0xFFF)
            if self.nBits < 12:
                sampVal = sampVal >> (12 - self.nBits)
            samples.append(sampVal)
        avg = numpy.mean(samples)
        stddev = numpy.std(samples,ddof=1)
        avgerr = stddev/numpy.sqrt(len(samples))
        return avg, avgerr

    def dumpWaveformRootFile(self,fileprefix,functype,freq,offsetV,amplitudeV,nPackets=None):
        filename = "{}_functype{}_freq{:.3f}_offset{:.3f}_amplitude{:.3f}.root".format(fileprefix,functype,freq,offsetV,amplitudeV)
        if not nPackets:
          nPackets = self.nPackets
        if functype > 1:
            nPackets = 100
        wrt = WRITE_ROOT_TREE(self.config,filename,nPackets)
        wrt.funcType = functype
        wrt.funcFreq = freq
        wrt.funcOffset = offsetV
        wrt.funcAmp = amplitudeV
        wrt.record_data_run()

def main():
    from ..configuration.argument_parser import ArgumentParser
    from ..configuration import CONFIG
    ROOT.gROOT.SetBatch(True)
    parser = ArgumentParser(description="Collects data for ADC tests")
    parser.addNPacketsArgs(False,100)
    #parser.add_argument("outfilename",help="Output root file name")
    args = parser.parse_args()
  
    config = CONFIG()
  
    collect_data = COLLECT_DATA(config,args.nPackets)
    collect_data.getData()
