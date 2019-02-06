from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import
from builtins import range
from builtins import int
from builtins import str
from builtins import hex
from future import standard_library
standard_library.install_aliases()
from builtins import object
import sys
import string
from subprocess import check_call as call
import os
import ntpath
import glob
import struct
import json
import time
import matplotlib.pyplot as plt

from femb_python.configuration import CONFIG
from femb_python.write_data import WRITE_DATA
from femb_python.configuration.config_base import FEMB_CONFIG_BASE

class SYNC_ADCS(object):
    
    def __init__(self, datadir="data", outlabel="syncData"):
        self.outpathlabel = os.path.join(datadir, outlabel)        
        
        self.config = CONFIG
        self.functions = FEMB_CONFIG_BASE(self.config)
        self.low_level = self.functions.lower_functions
        self.sync_functions = self.functions.sync
        self.plotting = self.functions.sync.plot
        
        
        self.write_data = WRITE_DATA(datadir)
        #set appropriate packet size
        
        self.write_data.femb.MAX_PACKET_SIZE = 8000
        
        #json output, note module version number defined here
        self.jsondict = {'type':'sync_adcs'}
        self.jsondict['version'] = '1.0'
        self.jsondict['timestamp']  = str(self.write_data.date)
    
        
        
    def sync(self):
        self.sync_functions.syncADC(**self.params)
        
#        self.femb_config.syncADC()
        #Tells the FPGA to turn on each DAC
        self.femb_config.femb.write_reg(61, 0x0)
        
        #Read from DATA output ADCs
        self.femb_config.femb.write_reg(60, 0)
    
        #Set to Regular Mode (not sampling scope)
        self.femb_config.femb.write_reg(10, 0)
        
        #Select TP FE Mode
        self.femb_config.femb.write_reg(9, 3)
        
        #Pulses the internal ASIC pulse (this changes the way packets are outputted through UDP and can screw things up 
        #if you don't know how it works.  Use caution and make sure register 17 goes back to 0 when done)
        #The way it works is that whenever the FPGA is ready to send out an ASIC pulse, it 
        self.reg_17_value = (self.femb_config.default_TP_Period << 16) + (self.femb_config.default_TP_Shift << 8) + (0b01000000)
        self.femb_config.femb.write_reg(17, self.reg_17_value)

        for num,i in enumerate(self.chip_list):
            chip_outpathlabel = os.path.join(self.datadir, i[1], self.datasubdir)
            data = self.femb_config.get_data_chipX(chip = i[0], packets = 25)[1]
            print("Test--> Printing synchronization plot for Chip {}".format(i[1]))
        
            feed_index = []
            for j in range(len(data)):
                if (data[j] > self.femb_config.adc_full_scale):
                    if (data[j] & (0b01 << 14)):
                        data[j] = data[j] & self.femb_config.adc_full_scale
                        
                    if (data[j] & (0b10 << 14)):
                        data[j] = data[j] & self.femb_config.adc_full_scale
                        feed_index.append(j)
                
            self.plotting.plot(data = data, plot_name = "Sync_Plot.png", 
                                 title_name = "Pulses for synchronization: Gain = 14 mv/fC, Peaking Time = 3 us, Buffer on, "
                                              "DAC Pulse at {} \nPeaks should be between {} and {}, Baseline should be between "
                                              "{} and {}".format(hex(self.femb_config.default_DAC), self.femb_config.sync_peak_min, 
                                                self.femb_config.sync_peak_max, self.femb_config.sync_baseline_min, self.femb_config.sync_baseline_max),
                                length = 1000)
            plotname = "chipname_{}-syncPlot.png".format(i)
            call(["mv", "Sync_Plot.png", os.path.join(chip_outpathlabel,plotname)])
            
            self.femb_config.fe_reg.set_fe_chn(chip = i[0], chn = 0, smn = 1)
            self.config_list = self.femb_config.configFeAsic()
            
            #Read from TEST output ADCs
            self.femb_config.femb.write_reg(60, 1)
            
            #Select the monitor readout
            self.femb_config.femb.write_reg(9, 3)
            data = []
            for j in range(5):
                data.extend(self.femb_config.get_data_chipXchnX(chip = i[0], chn = 0, packets = 1, data_format = "counts"))
            monitor_plot = self.plotting.quickPlot(data = data)
            plot_name = "Sync_Plot_Monitor.png"
            monitor_plot[1].savefig ("{}".format(os.path.join(chip_outpathlabel,plot_name)))
            plt.close(monitor_plot[1])
            print("Plot--> Data Saved as " + plot_name + "_{}".format(i[0]))
            
            self.femb_config.fe_reg.set_fe_chn(chip = i[0], chn = 0, smn = 0)
            self.config_list = self.femb_config.configFeAsic()
            
            #Read from TEST output ADCs
            self.femb_config.femb.write_reg(60, 0)
            
#            #Select the TP FE Mode
            self.femb_config.femb.write_reg(9, 3)
            
        self.femb_config.femb.write_reg(17,0)
        
        self.archiveResults()        
        
    def archiveResults(self):
        print("SYNCHRONIZATION RESULTS - ARCHIVE")
        
        self.jsondict['filedir'] = str( self.write_data.filedir )
        self.jsondict['boardID'] = str( self.boardID )
        self.jsondict['working_chips'] = self.working_chips

        for chip in self.chip_list:
            jsonFile = os.path.join(self.datadir,chip[1],self.datasubdir,"results.json")
            with open(jsonFile,'w') as outfile:
                json.dump(self.jsondict, outfile, indent=4)

def main():
    '''
    sync the ADCs
    '''
    sync_adcs = SYNC_ADCS()
    params = json.loads(open(sys.argv[1]).read())
    params["to_print"] = True
    params["outputdir"] = True
    sync_adcs.params = params
    
#    for array in params["chip_list"]:
#        params["data_dir_chip{}".format(array[0])] = "{}/{}".format(sync_adcs.datadir, array[1])
#        print(params["data_dir_chip{}".format(array[0])])
#        
#    jsonFile = os.path.join(sync_adcs.datadir,"params.json")
#    with open(jsonFile,'w') as outfile:
#        json.dump(params, outfile, indent=4)
        
    sync_adcs.sync()

    

if __name__ == '__main__':
    main()