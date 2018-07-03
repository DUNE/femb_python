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

from femb_python.test_measurements.sbnd_femb_test.Data_Analysis import Data_Analysis

class BASELINE_TESTER(object):
    
    def __init__(self, datadir="data", outlabel="baselineTest"):
        
        #import femb_udp modules from femb_udp package
        self.femb_config = CONFIG()
        self.write_data = WRITE_DATA(datadir)
        #import data analysis and plotting objects
        self.plotting = plot_functions()
        self.analyze = Data_Analysis()
        
        #set appropriate packet size
        self.write_data.femb.MAX_PACKET_SIZE = 8000

        self.cppfr = CPP_FILE_RUNNER()
        
        #json output, note module version number defined here
        self.jsondict = {'type':'baseline_test'}
        self.jsondict['version'] = '1.0'
        self.jsondict['timestamp']  = str(self.write_data.date)     

        
    def get_data(self):
        self.femb_config.make_filepaths(self.datadir,self.chip_list,self.datasubdir+"/Data")       
        for num,i in enumerate(self.chip_list):
            self.save_rms_noise(chip_index=i[0], chip_name=i[1])
        
#    def do_analysis(self):
#        continue

    def save_rms_noise(self, chip_index, chip_name):
        print("Test--> Collecting Baseline data for Chip {}...".format(chip_name))
        #Because the statement will never print until after the giant for loop
        sys.stdout.flush()      
        data_directory = os.path.join(self.datadir,chip_name,self.datasubdir,"Data")
        
        #Select Ground to Test and FE input of all chips
        self.femb_config.femb.write_reg(9, 2)
            
        #Make sure nothing is coming from the FPGA DAC or for the signal for the ASIC's internal DAC
        self.femb_config.femb.write_reg(17, 0)
        
        #Read from FE output ADCs
        self.femb_config.femb.write_reg(60, 0)
        
#        #Set the DAC to be on permanently (and sample at the lower clock speed)
#        self.femb_config.femb.write_reg(13, 0b10000)
#        originals = []
#        for reg in range(65,69,1):
#            value = self.femb_config.femb.read_reg(reg)
#            originals.append(value)
#            self.femb_config.femb.write_reg(reg, 0xFFFFFFFF)
##            print ("The original register {} was {}".format(reg, hex(value)))
#            
#        original_phase = []
#        for reg in range(69,73,1):
#            value = self.femb_config.femb.read_reg(reg)
#            original_phase.append(value)
#            self.femb_config.femb.write_reg(reg, 0xAAAAAAAA)
##            print ("The original register {} was {}".format(reg, hex(value)))
            
#        print("Old registers are {}".format(originals))
        self.femb_config.fe_reg.set_fe_board(sts=0, snc=self.base, sg=self.gain, st=self.shape,
                                      smn=0, sbf=self.buff, slk = self.leak, stb = 0, s16=0, slkh=self.leak,
                                      sdc=0, sdacsw2=0, sdacsw1=0, sdac=0, remapping=True)
                                      #remapping is to make gain/shaping times/base settings (0-3) consecutive in output and GUI
                   
        self.femb_config.configFeAsic(to_print = False)
#                            raw_input("Baseline Data --> Collecting Data for {}, {}, {}, {}, {}".format(gain, peak, leak, buff, base))
#                            print ("Baseline Data --> Collecting Data for {}, {}, {}, {}, {}".format(gain, peak, leak, buff, base))
        sys.stdout.flush()
        time.sleep(0.5)
        for chn in range(self.femb_config.channels):
            self.femb_config.select_chip_chn(chip = chip_index, chn = chn)
            filename = self.femb_config.Baseline_Naming.format(chn,self.femb_config.gainArray[self.gain],self.femb_config.shapeArray[self.shape],self.leak,self.femb_config.buffArray[self.buff],self.femb_config.baseArray[self.base])
            
            rawdata = bytearray()
            full_filename = os.path.join(data_directory,filename)
    
            rawdata += self.femb_config.femb.get_data_packets(data_type = "bin", num = 1, header = True)
            for pack in range (self.femb_config.baseline_length):
                rawdata += self.femb_config.femb.get_data_packets(data_type = "bin", num = 1, header = False)
    
            with open(full_filename,"wb") as f:
                f.write(rawdata) 
                f.close()


    def analyze_data(self):
        for num,i in enumerate(self.chip_list):
            self.result, self.average_baseline, self.baselines = self.analyze.baseline_directory(os.path.join(self.datadir,i[1]), i[1], self.datasubdir, self.outlabel, self.femb_config.gainArray[self.gain],self.femb_config.shapeArray[self.shape],self.leak,self.femb_config.buffArray[self.buff],self.femb_config.baseArray[self.base])
            self.archive_results(i[1],i[0])
            
    def archive_results(self, chip_name, chip_index):
        print("BASELINE AND RMS RESULTS - ARCHIVE")
        
        #add summary variables to output
        self.jsondict['filedir'] = str( self.write_data.filedir )
        self.jsondict['config_gain'] = str( self.femb_config.gainArray[self.gain] )
        self.jsondict['config_shape'] = str( self.femb_config.shapeArray[self.shape] )
        self.jsondict['config_base'] = str( self.femb_config.baseArray[self.base] )
        self.jsondict['config_buff'] = str ( self.femb_config.buffArray[self.buff] )
        self.jsondict['average_baseline'] = str( self.average_baseline )
        self.jsondict['chip_name'] = str( chip_name )
        self.jsondict['chip_index'] = str ( chip_index )
        if self.result:
            self.jsondict['result'] = "Pass"
        else:
            self.jsondict['result'] = "Fail"
        
        results = []
        for i,ch_base in enumerate(self.baselines):
            measurement = {}
            measurement["ch"] = str(ch_base[0])
            measurement["baseline"] = str(ch_base[1])
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
    base_test = BASELINE_TESTER()      
    print(sys.argv[1])
    params = json.loads(open(sys.argv[1]).read())    
    
    start_test_time = time.strftime("%H:%M:%S", time.localtime(time.time()))
#    print("starting sbnd_baseline_test:main at {}".format(start_test_time))
    
    
    base_test.datadir = params['datadir']
    base_test.outlabel = params['outlabel']    
    base_test.chip_list = params['chip_list']
    base_test.gain = params['gain_ind']
    base_test.shape = params['shape_ind']
    base_test.leak = params['leakage_ind']
    base_test.buff = params['buffer_ind']
    base_test.base = params['base_ind']
    base_test.datasubdir = params['datasubdir']
        
    base_test.get_data()
    base_test.analyze_data()
    
#    print("ending sbnd_baseline_test:main at {}".format(time.strftime("%H:%M:%S", time.localtime(time.time()))))
 
if __name__ == '__main__':
    main()