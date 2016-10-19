from ..femb_udp import FEMB_UDP
from ..test_instrument_interface import RigolDG4000
import time
from uuid import uuid1 as uuid
import numpy
import matplotlib.pyplot as plt
import ROOT

class MEASURE_LINEARITY(object):
    """
    Measures ADC Linearity
    """

    def __init__(self,config):
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

    def doHistograms(self,nSamples):
        """
        Creates histograms of data doing a linear ramp of 
        the full ADC range + 10% on each end.
        """

        linearFitData = self.doLinearFit(numpy.linspace(0.0,3.5,5),10)

        #canvas = ROOT.TCanvas()
        #result = []
        #for iChip in range(self.NASICS):
        #    result.append([])
        #    for iChan in range(16):
        #        x0 = linearFitData[iChip][iChan]["x0"]
        #        FSR = linearFitData[iChip][iChan]["FSR"]
        #        if x0:
        #            xLow = x0 - 0.1*FSR
        #            xHigh = x0 + 1.1*FSR
        #            if xHigh > 3.5: 
        #                xHigh = 3.5
        #            if xLow < 0.:
        #                xLow = 0.
        #            hist = self.makeRampHist(iChip,iChan,xLow,xHigh,nSamples)
        #            hist.Draw()
        #            canvas.SaveAs("ADC_Hist_Chip{}_Chan{}.png".format(iChip,iChan))
        #            canvas.SaveAs("ADC_Hist_Chip{}_Chan{}.pdf".format(iChip,iChan))
        #self.funcgen.stop()

    def makeRampHist(self,iChip,iChan,xLow,xHigh,nSamples):
        """
        Makes a histogram of linear ramp data between xLow and xHigh 
        for iChip and iChan. The histogram will have at leas nSamples entries.
        """
        #print("makeRampHist: ",iChip,iChan,xLow,xHigh,nSamples)
        hist = ROOT.TH1F(uuid().hex,
                        "Chip: {} Channel: {}".format(iChip,iChan),
                        2**12,-0.5,2**12-0.5
                        )
        hist.Sumw2()
        hist.GetXaxis().SetTitle("ADC Code")
        hist.GetYaxis().SetTitle("Entries / ADC Code")

        self.funcgen.startRamp(734,xLow,xHigh)
        self.config.selectChannel(iChip,iChan)
        time.sleep(self.settlingTime)

        for iTry in range(self.maxTries):
            raw_data = self.femb.get_data(100)
        
            samples = []
            for samp in raw_data:
                chNum = ((samp >> 12 ) & 0xF)
                if chNum != iChan:
                    print("makeRampHist: chNum {} != iChan {}".format(chNum,iChan))
                    continue
                sampVal = (samp & 0xFFF)
                hist.Fill(sampVal)
            if len(samples) > nSamples:
                break
        return hist

    def doLinearFit(self,voltageList,nPackets):
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
        data = self.getADCDataDC(voltageList,nPackets)
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
                manyaxes[iChan].set_ylim(0,2**12)
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
                ax.errorbar(voltages,averages,fmt="ko",yerr=errors,label="Data")
                manyaxes[iChan].errorbar(voltages,averages,fmt="ko",yerr=errors,label="Data")
                ax.set_xlabel("Voltage [V]")
                ax.set_ylabel("ADC Output")
                ax.set_xlim(0,3.5)
                ax.set_ylim(0,2**12)
                ax.set_title("ADC Chip {} Channel {}".format(iChip,iChan))
                ax.legend(loc='best')
                filename = "ADC_Linearity_Chip{}_Chan{}".format(iChip,iChan)
                fig.savefig(filename+".png")
                fig.savefig(filename+".pdf")
                ax.cla()
            figmany.savefig("ADC_Linearity_Chip{}.png".format(iChan))
            figmany.savefig("ADC_Linearity_Chip{}.pdf".format(iChan))
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
        fitresult = graph.Fit(func,"QFMEN0S")

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
            fsr = 2**12 / m + x0
        return x0, x0err, m, merr, chi2ondf, fsr

    def getADCDataDC(self,voltages,nPackets):
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
            avgs, errs = self.getAverageForAllChannels(nPackets)
            data[voltage] = { "avg": avgs, "err": errs}
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

    def getAverageForAllChannels(self,nPackets):
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
                avg, err = self.getAverage(iChip,iChan,nPackets)
                averages[iChip].append(avg)
                errors[iChip].append(err)
        return averages, errors
    
    def getAverage(self,iChip,iChan,nPackets):
        """
        Find iChip iChan average for nPackets worth of data
        for whatever signal is going into the ADC now.

        Returns the average and its statistical error
        """
        self.config.selectChannel(iChip,iChan)
        time.sleep(0.01)

        raw_data = self.femb.get_data(nPackets)
        
        samples = []
        for samp in raw_data:
            chNum = ((samp >> 12 ) & 0xF)
            if chNum != iChan:
                print("computeAverage: chNum {} != iChan {}".format(chNum,iChan))
                continue
            sampVal = (samp & 0xFFF)
            samples.append(sampVal)
        avg = numpy.mean(samples)
        stddev = numpy.std(samples,ddof=1)
        avgerr = stddev/numpy.sqrt(len(samples))
        return avg, avgerr
        
def main():
    from ..configuration.argument_parser import ArgumentParser
    from ..configuration import CONFIG
    from ..configuration.config_file_finder import get_env_config_file, config_file_finder
    ROOT.gROOT.SetBatch(True)
    parser = ArgumentParser(description="Measures ADC Linearity")
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
  
    measure_linearity = MEASURE_LINEARITY(config)
    measure_linearity.doHistograms(1e5)