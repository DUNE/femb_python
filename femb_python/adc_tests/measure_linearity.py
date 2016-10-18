from ..femb_udp import FEMB_UDP
from ..test_instrument_interface import RigolDG4000
import time
import numpy
import matplotlib.pyplot as plt

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
        self.settlingTime = 1. # second

    def plotADCData(self):
        data = self.getADCData(numpy.linspace(0.2,1.6,3),10)
        fig, ax = plt.subplots(figsize=(8,8))
        for iChip in range(self.NASICS):
            for iChan in range(16):
                voltages = data[iChip][iChan]["vlt"]
                averages = data[iChip][iChan]["avg"]
                errors = data[iChip][iChan]["err"]
                ax.errorbar(voltages,averages,fmt="o",yerr=errors)
                ax.set_xlabel("Voltage [V]")
                ax.set_ylabel("ADC Output")
                filename = "ADC_Linearity_Chip{}_Chan{}".format(iChip,iChan)
                fig.savefig(filename+".png")
                fig.savefig(filename+".pdf")
                ax.cla()

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
