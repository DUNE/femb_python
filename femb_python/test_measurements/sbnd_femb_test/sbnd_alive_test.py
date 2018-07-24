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

class ALIVE_TESTER(object):
    
    def __init__(self, datadir="data", outlabel="aliveTest"):        
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
        self.jsondict = {'type':'alive_test'}
        self.jsondict['version'] = '1.0'
        self.jsondict['timestamp']  = str(self.write_data.date) 
        self.tests = ["test_ext", "test_off"]            
        self.leaks = "500pA"
        
    def get_data(self):
        self.femb_config.make_filepaths(self.datadir,self.chip_list, os.path.join(self.datasubdir,"Data"))
        for num,i in enumerate(self.chip_list):
            if self.asic_pass[i[0]] == [1,1,-1] and self.config_list[i[0]]:
                folder_path = os.path.join(self.datadir,i[1])
                self.save_alive_data(folder_path, chip_index=i[0], chip_name=i[1])

        #Tells the FPGA to turn off the ASICs
        self.femb_config.femb.write_reg(12, 0xF)

    def save_alive_data(self, folder_path, chip_index, chip_name):
        test_directory = os.path.join(folder_path,self.datasubdir)
        data_directory = os.path.join(test_directory,"Data")
        
        #Give the test pulse timing
        self.femb_config.femb.write_reg(7, (self.femb_config.test_TP_Shift << 16) + self.femb_config.test_TP_Period)

        #Make sure nothing is coming from the FPGA DAC or for the signal for the ASIC's internal DAC
        self.femb_config.femb.write_reg(17, 0)
        
        #Read from FE output ADCs
        self.femb_config.femb.write_reg(60,0)
        print("Test--> Collecting Input Alive data for Chip {}...".format(chip_name))
        sys.stdout.flush()
        for test in self.tests:
            leak = self.leaks
            #commented out is Eric's hard coded config settings, I adjusted the syntax for femb_python
#            self.femb_config.fe_reg.set_fe_board(sts=a[test][0], snc=a["200mV"], sg=a["14mV"], st=a["2us"], 
#                        smn=0, sbf=a["b_off"], slk = a[leak][1], stb = 0, s16=0, slkh=a[leak][0], sdc=0, 
#                        sdacsw2=0, sdacsw1=a[test][0], sdac=0)

            self.femb_config.fe_reg.set_fe_board(sts=self.femb_config.testArray(test)[0], snc=0, sg=2, st=2, smn=0, sbf=0,
                                                 slk=self.femb_config.leakArray(leak)[1], stb=0, s16=0, slkh=self.femb_config.leakArray(leak)[0], sdacsw2=0, sdacsw1=self.femb_config.testArray(test)[0], sdac=0, remapping=True)
                                                 #remapping is to make gain/shaping times/base settings (0-3) consecutive in output and GUI
             
            self.config_list = self.femb_config.configFeAsic(to_print = False)
#                print ("Input Alive --> Collecting Data for {}, {}".format(test, leak))
            for chn in range(self.femb_config.channels):
                time.sleep(.1)
                self.femb_config.select_chip_chn(chip = chip_index, chn = chn)
                filename = self.femb_config.Alive_Naming.format(chn,leak,test)
                time.sleep(.1)
                if (test == "test_off"):
                    #Select Ground to Test input and DAC pulse to FE input
                    self.femb_config.femb.write_reg(9, 8)
                    #Give the test DAC value
                    self.femb_config.femb.write_reg(1, self.femb_config.test_DAC_in)
                    self.femb_config.femb.write_reg(2, 1)
                    self.femb_config.femb.write_reg(2, 0)
                    
                elif (test == "test_ext"):
                    #Select DAC pulse to Test input and Ground to FE input
                    self.femb_config.femb.write_reg(9, 4)
                    #Give the test DAC value
                    self.femb_config.femb.write_reg(1, self.femb_config.test_DAC_mon)
                    self.femb_config.femb.write_reg(2, 1)
                    self.femb_config.femb.write_reg(2, 0)
                    
                rawdata = bytearray()
                full_filename = os.path.join(data_directory,filename)
        
                rawdata += self.femb_config.femb.get_data_packets(data_type = "bin", num = 1, header = True)
                for pack in range (self.femb_config.alive_length):
                    rawdata += self.femb_config.femb.get_data_packets(data_type = "bin", num = 1, header = False)
        
                with open(full_filename,"wb") as f:
                    f.write(rawdata) 
                    f.close()
                        
#        self.femb_config.femb.write_reg(9, 8)
        print("Test--> Testing {} power cycles (1 minute in between)".format(self.femb_config.power_cycles))
        sys.stdout.flush()
        for cycle in range(self.femb_config.power_cycles):
            print("Test--> Cycle {}".format(cycle))
            sys.stdout.flush()
            filename = self.femb_config.Alive_Naming2.format(chn,leak,test,cycle)
            sys.stdout.flush()
            self.femb_config.select_chip_chn(chip = 0, chn = 2)
            #Tells the FPGA to turn off the ASICs
            self.femb_config.femb.write_reg(12, 0xF)
            time.sleep(60)
            #Tells the FPGA to turn on the ASICs
            self.femb_config.femb.write_reg(12, 0x0)
            time.sleep(5)
            #The hard coded values from Eric's code
#            self.femb_config.fe_reg.set_fe_board(sts=0, snc=a["200mV"], sg=a["14mV"], st=a["2us"], 
#                            smn=0, sbf=a["b_off"], slk = 0, stb = 0, s16=0, slkh=0, sdc=0, 
#                            sdacsw2=0, sdacsw1=0, sdac=0)
            self.femb_config.fe_reg.set_fe_board(sts=0, snc=0, sg=2, st=2,
                                          smn=0, sbf=0, slk = 0, stb = 0, s16=0, slkh=0, sdc=0,
                                          sdacsw2=0, sdacsw1=0, sdac=0, remapping=True)
                                          #remapping is to make gain/shaping setting values consecutive (0-3)
                           
            self.config_list = self.femb_config.configFeAsic(to_print = False)
            
            time.sleep(1)
            self.femb_config.femb.write_reg(1, self.femb_config.test_DAC_in)
            self.femb_config.femb.write_reg(2, 1)
            self.femb_config.femb.write_reg(2, 0)
            self.femb_config.femb.write_reg(61, 0x0)
            self.femb_config.femb.write_reg(7, (self.femb_config.test_TP_Shift << 16) + self.femb_config.test_TP_Period)
            self.femb_config.select_chip_chn(chip = 0, chn = 1)
            self.femb_config.femb.write_reg(9, 8)
            time.sleep(1)

            for num,i in enumerate(self.chip_list):
                self.femb_config.select_chip_chn(chip = i[0], chn = 1)
                print ("Test--> Input Alive power cycle data collecting for Chip {}".format(i[1]))
                sys.stdout.flush()
                full_filename = os.path.join(data_directory,filename)
                rawdata = bytearray()
                rawdata += self.femb_config.femb.get_data_packets(data_type = "bin", num = 1, header = True)
                for pack in range (self.femb_config.alive_length):
                    rawdata += self.femb_config.femb.get_data_packets(data_type = "bin", num = 1, header = False)
                
                with open(full_filename,"wb") as f:
                    f.write(rawdata) 
                    f.close()
        print ("Test--> Input Alive data completed")
        

    def analyze_data(self):
        for num,i in enumerate(self.chip_list):
            if self.asic_pass[i[0]] == [1,1,-1] and self.config_list[i[0]]:
                folder_path = os.path.join(self.datadir, i[1])
                self.result = self.analyze.alive_directory(folder_path, i[1], self.datasubdir, self.tests, self.leaks)
                self.archive_results(chip_name = i[1], chip_index = i[0])
            
    def archive_results(self, chip_name, chip_index):
        print("INPUT ALIVE POWER CYCLE RESULTS - ARCHIVE")
        
        #add summary variables to output
 #add summary variables to output
        self.jsondict['filedir'] = str( self.write_data.filedir )
        self.jsondict['config_gain'] = str( self.femb_config.gainArray[self.gain] )
        self.jsondict['config_shape'] = str( self.femb_config.shapeArray[self.shape] )
        self.jsondict['config_base'] = str( self.femb_config.baseArray[self.base] )
        self.jsondict['config_buff'] = str ( self.femb_config.buffArray[self.buff] )
        self.jsondict['chip_name'] = str( chip_name )
        self.jsondict['chip_index'] = str ( chip_index )
        self.jsondict['config_list'] = self.config_list
        if self.result:
            self.jsondict['result'] = "Pass"
        else:
            self.jsondict['result'] = "Fail"
                    
        #dump results 
        jsonFile = os.path.join(self.datadir,chip_name,self.datasubdir,"results.json")
        with open(jsonFile,'w') as outfile:
            json.dump(self.jsondict, outfile, indent=4)
            
        
def main():
    '''
    sync the ADCs
    '''
    alive_test = ALIVE_TESTER()      

    params = json.loads(open(sys.argv[1]).read())           
    
    alive_test.datadir = params['datadir']
    alive_test.chip_list = params['chip_list']
    alive_test.gain = params['gain_ind']
    alive_test.shape = params['shape_ind']
    alive_test.leak = params['leakage_ind']
    alive_test.buff = params['buffer_ind']
    alive_test.base = params['base_ind']
    alive_test.datasubdir = params['datasubdir']
    alive_test.asic_pass = params['asic_pass']
    alive_test.config_list = params['config_list']
    
    alive_test.get_data()
    alive_test.analyze_data()
     
if __name__ == '__main__':
    main()