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
from femb_python.test_measurements.sbnd_femb_test.plotting import plot_functions
from femb_python.configuration.cppfilerunner import CPP_FILE_RUNNER

class SYNC_ADCS(object):
    
    def __init__(self, datadir="data", outlabel="syncData"):
        self.outpathlabel = os.path.join(datadir, outlabel)        
        
        #import femb_udp modules from femb_udp package
        self.femb_config = CONFIG()
        self.write_data = WRITE_DATA(datadir)
        #set appropriate packet size
        self.plotting = plot_functions()
        self.write_data.femb.MAX_PACKET_SIZE = 8000

        self.cppfr = CPP_FILE_RUNNER()
        
        #json output, note module version number defined here
        self.jsondict = {'type':'sync_adcs'}
        self.jsondict['version'] = '1.0'
        self.jsondict['timestamp']  = str(self.write_data.date)
    
        
        
    def sync(self):
        self.femb_config.femb.write_reg(12,0x0)
        time.sleep(1)
#        for num,i in enumerate(chip_list):
#            self.femb_config.map_directory(os.path.join(datadir,i[1]))
        #stablish IP addresses for board and machine running this program
        #make sure IP address for the ethernet port is set correctly
        self.femb_config.femb.init_ports(hostIP = self.femb_config.PC_IP, destIP = self.femb_config.FPGA_IP)
        time.sleep(0.1)
        print("Chip tester verion {}".format(hex(self.femb_config.femb.read_reg(0x64))))
        #make filepaths to store the synchronization plots
        self.femb_config.make_filepaths(self.datadir,self.chip_list,self.datasubdir)

        self.femb_config.resetFEMBBoard()
        self.femb_config.initBoard()
        
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
        #if you don't know how it works.  Use caution and makes ure register 17 goes back to 0 when done)
        #The way it works is that whenever the FPGA is ready to send out an ASIC pulse, it 
        self.reg_17_value = (self.femb_config.default_TP_Period << 16) + (self.femb_config.default_TP_Shift << 8) + (0b01000000)
        self.femb_config.femb.write_reg(17, self.reg_17_value)

        for num,i in enumerate(self.chip_list):
            chip_outpathlabel = os.path.join(self.datadir, i[1], self.datasubdir)
            data = self.femb_config.get_data_chipX(chip = i[0], packets = 5)
            print("Test--> Printing synchronization plot for Chip {}".format(i[1]))
            self.plotting.plot(data = data, plot_name = "Sync_Plot.png", 
                                 title_name = "Pulses for synchronization: Gain = 14 mv/fC, Peaking Time = 3 us, Buffer on, "
                                              "DAC Pulse at {} \nPeaks should be between {} and {}, Baseline should be between "
                                              "{} and {}".format(hex(self.femb_config.default_DAC), self.femb_config.sync_peak_min, 
                                                self.femb_config.sync_peak_max, self.femb_config.sync_baseline_min, self.femb_config.sync_baseline_max))
            plotname = "chipname_{}-syncPlot.png".format(i[1])
            call(["mv", "Sync_Plot.png", os.path.join(chip_outpathlabel,plotname)])
            
            self.femb_config.fe_reg.set_fe_chn(chip = i[0], chn = 0, smn = 1)
            self.femb_config.configFeAsic()
            
            #Read from TEST output ADCs
            self.femb_config.femb.write_reg(60, 1)
            
            #Select the monitor readout
            self.femb_config.femb.write_reg(9, 3)
            data = []
            for j in range(5):
                data.extend(self.femb_config.get_data_chipXchnX(chip = i[0], chn = 0, packets = 1, data_format = "triggered"))
            monitor_plot = self.plotting.quickPlot(data = data)
            plot_name = "Sync_Plot_Monitor.png"
            monitor_plot[1].savefig ("{}".format(os.path.join(chip_outpathlabel,plot_name)))
            plt.close(monitor_plot[1])
            print("Plot--> Data Saved as " + plot_name + "_{}".format(i[0]))
            
            self.femb_config.fe_reg.set_fe_chn(chip = i[0], chn = 0, smn = 0)
            self.femb_config.configFeAsic()
            
            #Read from TEST output ADCs
            self.femb_config.femb.write_reg(60, 0)
            
#            #Select the TP FE Mode
            self.femb_config.femb.write_reg(9, 3)
            
        self.femb_config.femb.write_reg(17,0)


def main():
    '''
    sync the ADCs
    '''
    sync_adcs = SYNC_ADCS()  
    
    params = json.loads(open(sys.argv[1]).read())            
    sync_adcs.datadir = params['datadir']
    sync_adcs.outlabel = params['outlabel']    
    sync_adcs.chip_list = params['chiplist']
    sync_adcs.datasubdir = params['datasubdir']
    
    sync_adcs.sync()

    

if __name__ == '__main__':
    main()