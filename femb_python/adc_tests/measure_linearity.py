from ..femb_udp import FEMB_UDP
from ..test_instrument_interface import RigolDG4000
import time
from uuid import uuid1 as uuid
import numpy
import matplotlib.pyplot as plt
from ROOT import TGraphErrors, TF1

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
        self.settlingTime = 0.5 # second

    def plotADCData(self):
        #data = self.getADCData(numpy.linspace(0.2,1.6,5),10)
        data = self.getADCData(numpy.linspace(0.2,2.5,10),10)
        fig, ax = plt.subplots(figsize=(8,8))
        for iChip in range(self.NASICS):
            for iChan in range(16):
                voltages = numpy.array(data[iChip][iChan]["vlt"])
                averages = numpy.array(data[iChip][iChan]["avg"])
                errors = numpy.array(data[iChip][iChan]["err"])

                x0, x0err, m, merr, chi2ondf, fsr = self.fitLineToData(voltages,averages,errors)
                print("Chip: {} Chan: {:2} x0: {:8.2g} +/- {:8.2g} mV m: {:8.2g} +/- {:8.2g} Counts/mV, chi2/ndf: {:10.2g}, FSR: {:10.3g} V".format(iChip,iChan,x0*1000.,x0err*1000.,m/1000.,merr/1000.,chi2ondf, fsr))
                lineplot = ax.plot(voltages,m*(voltages-x0),"b-",label="Fit")
                dataplot = ax.errorbar(voltages,averages,fmt="ko",yerr=errors,label="Data")
                ax.set_xlabel("Voltage [V]")
                ax.set_ylabel("ADC Output")
                ax.set_title("ADC Chip {} Channel {}".format(iChip,iChan))
                ax.legend(loc='best')
                filename = "ADC_Linearity_Chip{}_Chan{}".format(iChip,iChan)
                fig.savefig(filename+".png")
                fig.savefig(filename+".pdf")
                ax.cla()

    def fitLineToData(self,voltages,counts,errors):
        """
        Performs a least squares fit of y = counts +/- errors, x = voltages

        returns x-intercept [V], x-intercept error [V], slope [Counts/V], slope error [Counts/V], chi2/ndf, estimated full scale range [V]
        """
        assert(len(voltages)==len(counts))
        assert(len(errors)==len(counts))
        graph = TGraphErrors()
        for iPoint in range(len(voltages)):
            graph.SetPoint(iPoint,voltages[iPoint],counts[iPoint])
            graph.SetPointError(iPoint,0.,errors[iPoint])
        func = TF1(uuid().hex,"[0]*(x-[1])",voltages[0],voltages[-1])
        fitresult = graph.Fit(func,"QFMEN0S")
        chi2 = fitresult.Chi2()
        m = fitresult.Value(0)
        x0 = fitresult.Value(1)
        merr = fitresult.ParError(0)
        x0err = fitresult.ParError(1)
        ndf = len(counts) - 2
        fsr = 2**12 / m + x0
        return x0, x0err, m, merr, chi2/ndf, fsr

    def getADCData(self,voltages,nPackets):
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
                d = { "vlt":voltages, "avg":avgs, "err": errs}
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
    measure_linearity.plotADCData()
