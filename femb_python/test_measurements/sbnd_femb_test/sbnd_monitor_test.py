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
plt.switch_backend('agg')
import pickle


from femb_python.configuration import CONFIG
from femb_python.write_data import WRITE_DATA
from femb_python.test_measurements.sbnd_femb_test.plotting import plot_functions
from femb_python.configuration.cppfilerunner import CPP_FILE_RUNNER

from femb_python.test_measurements.sbnd_femb_test.Data_Analysis2 import Data_Analysis2

class MONITOR_TESTER(object):
    
    def __init__(self, datadir="data", outlabel="monitorTest"):
        self.outpathlabel = os.path.join(datadir, outlabel)        
        
        #import femb_udp modules from femb_udp package
        self.femb_config = CONFIG()
        self.write_data = WRITE_DATA(datadir)
        #import data analysis and plotting objects
        self.plotting = plot_functions()
        self.analyze2 = Data_Analysis2()
        
        #set appropriate packet size
        self.write_data.femb.MAX_PACKET_SIZE = 8000

        self.cppfr = CPP_FILE_RUNNER()
        
        #json output, note module version number defined here
        self.jsondict = {'type':'monitor_test'}
        self.jsondict['version'] = '1.0'
        self.jsondict['timestamp']  = str(self.write_data.date)     

        
    def get_data(self):
        for num,i in enumerate(self.chip_list):
            folder_path = os.path.join(self.datadir,i[1])
            self.save_monitor_data(folder_path, chip_index=i[0], chip_name=i[1])

    def save_monitor_data(self, folder_path, chip_index, chip_name):
        sys.stdout.flush()
		
        test_directory = os.path.join(folder_path,self.datasubdir)
        os.makedirs(test_directory)
		
        data_directory = os.path.join(test_directory,"Data")
        os.makedirs(data_directory)
		
        #Select the monitor readout
        self.femb_config.femb.write_reg(9, 3)
            
        #Get the ASIC to send out pulses.  Bit 6 needs to be high for ASIC DAC
        reg17_value = (self.femb_config.monitor_freq << 16) + (self.femb_config.monitor_delay << 8) + (0b01000000)
        self.femb_config.femb.write_reg(17, reg17_value)
        
        #Make sure the input to the DAC is not on
        self.femb_config.femb.write_reg(7, 0)
        
        #Read from test output ADCs
        self.femb_config.femb.write_reg(60, 1)
		
        for chn in range(self.femb_config.channels):
#            This was from the old code, not sure why the choice of hardcoded values
#            self.femb_config.set_fe_board(sts=a["test_int"][0], snc=a["200mV"], sg=a["14mV"], st=a["2us"], 
#					smn=0, sbf=a["b_on"], slk = a["500pA"][1], stb = 0, s16=0, slkh=a["500pA"][0], sdc=0, 
#					sdacsw2=1, sdacsw1=0, sdac=settings.monitor_amplitude)
        
            self.femb_config.fe_reg.set_fe_board(sts=0, snc=0, sg=2, st=2, 
					smn=0, sbf=1, slk = 0, stb = 0, s16=0, slkh=0, sdc=0, 
					sdacsw2=1, sdacsw1=0, sdac=self.femb_config.monitor_amplitude)
                                           
            self.femb_config.fe_reg.set_fe_chn(chip=chip_index, chn=chn, sts=1, snc=-1, sg=-1, st=-1, smn=1, sbf=-1)
            self.femb_config.configFeAsic(to_print = False)
    			
            self.femb_config.select_chip_chn(chip = chip_index, chn = chn)
            filename = self.femb_config.Monitor_Naming.format(chn)
            rawdata = bytearray()
            full_filename = os.path.join(data_directory,filename)
    
#            rawdata += self.femb_config.femb.get_data_packets(data_type = "bin", num = 1, header = True)
            rawdata += self.femb_config.femb.get_data_packets(data_type = "bin", num = 1, header = False)[2:]
            for pack in range (self.femb_config.monitor_length):
                rawdata += self.femb_config.femb.get_data_packets(data_type = "bin", num = 1, header = False)[2:]
                with open(full_filename,"wb") as f:
                    f.write(rawdata) 
                    f.close()
                    
        self.femb_config.femb.write_reg(17, 0)
		            
        print ("Test--> Monitor check data collected for Chip {}".format(chip_name))


    def analyze_data(self):
        for num,i in enumerate(self.chip_list):
            folder_path = os.path.join(self.datadir,i[1])
            self.result, self.peaks, self.differences, self.average_peak = self.analyze2.monitor_directory(folder_path, i[1], self.datasubdir, self.datadir, self.gain, self.shape, self.leak, self.buff, self.base)
            self.archive_results(i[1],i[0])
            if (self.result == True):
                print("Chip {} (Socket {}) PASSED!".format(i[1], i[0]))
            if (self.result == False):
                print("Chip {} (Socket {}) FAILED!".format(i[1], i[0]))
        
    def archive_results(self, chip_name, chip_index):
        print("MONITOR DATA RESULTS - ARCHIVE")
        
        #add summary variables to output
 #add summary variables to output
        self.jsondict['filedir'] = str( self.write_data.filedir )
        self.jsondict['config_gain'] = str( self.femb_config.gainArray[self.gain] )
        self.jsondict['config_shape'] = str( self.femb_config.shapeArray[self.shape] )
        self.jsondict['config_base'] = str( self.femb_config.baseArray[self.base] )
        self.jsondict['config_buff'] = str ( self.femb_config.buffArray[self.buff] )
        self.jsondict['average_peak'] = str( self.average_peak )
        self.jsondict['chip_name'] = str( chip_name )
        if self.result:
            self.jsondict['result'] = "Pass"
        else:
            self.jsondict['result'] = "Fail"
            
        self.jsondict['average_peak'] = self.average_peak
        
        results = []
        for i,ch_peak in enumerate(self.peaks):
            measurement = {}
            measurement["ch"] = str(ch_peak[0])
            measurement["peak"] = str(ch_peak[1])
            measurement["difference"] = str(self.differences[i])
            results.append(measurement)
        self.jsondict['results'] = results
        #dump results 
        jsonFile = os.path.join(self.datadir,chip_name,self.datasubdir,"results.json")
        with open(jsonFile,'w') as outfile:
            json.dump(self.jsondict, outfile, indent=4)
            
        
def main():
    '''
    sync the ADCs
    '''
    monitor_test = MONITOR_TESTER()      

    params = json.loads(open(sys.argv[1]).read())        
    
    start_test_time = time.strftime("%H:%M:%S", time.localtime(time.time()))
#    print("starting sbnd_monitor_test:main at {}".format(start_test_time))
    
    
    monitor_test.datadir = params['datadir']
    monitor_test.chip_list = params['chip_list']
    monitor_test.gain = params['gain_ind']
    monitor_test.shape = params['shape_ind']
    monitor_test.leak = params['leakage_ind']
    monitor_test.buff = params['buffer_ind']
    monitor_test.base = params['base_ind']
    monitor_test.datasubdir = params['datasubdir']
    
    monitor_test.get_data()
    monitor_test.analyze_data()
#    
#    #end of test so tell FPGA to turn off ASICs
#    monitor_test.femb_config.femb.write_reg(12, 0xF)
    
    
#    print("ending sbnd_monitor_test:main at {}".format(time.strftime("%H:%M:%S", time.localtime(time.time()))))
 
if __name__ == '__main__':
    main()