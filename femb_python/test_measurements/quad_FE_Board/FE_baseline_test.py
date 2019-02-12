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
import os
import json
import time
import matplotlib.pyplot as plt
plt.switch_backend('agg')
import datetime


from femb_python.configuration import CONFIG
from femb_python.configuration.config_base import FEMB_CONFIG_BASE
from femb_python.test_measurements.quad_FE_Board.Data_Analysis import Data_Analysis

class BASELINE_TESTER(object):
    
    def __init__(self, datadir="data", outlabel="baselineTest"):
        
        #import femb_udp modules from femb_udp package
        self.femb_config = CONFIG()
        self.functions = FEMB_CONFIG_BASE(self.config)
        self.low_level = self.functions.lower_functions
        self.sync_functions = self.functions.sync
        self.plotting = self.functions.sync.plot
        self.analyze = Data_Analysis()
        
        #json output, note module version number defined here
        self.jsondict = {'type':'baseline_test'}
        self.jsondict['version'] = '1.1'
        self.jsondict['timestamp']  = datetime.datetime.today().strftime('%Y%m%d%H%M%S')

        
    def check_setup(self):
        self.functions.initBoard(default_sync = False)
        for i in self.params['working_chips']:
            chip_name = self.params['chip_list'][i][1]
            os.makedirs(self.params['datadir'],chip_name,self.params['outlabel'],"Data", exist_ok=True)

    def record_data(self, chip_index, chip_name):

        
        data_directory = os.path.join(self.datadir,chip_name,self.datasubdir,"Data")
        
        #Select Ground to Test and FE input of all chips
        self.femb_config.femb.write_reg(9, 2)
            
        #Make sure nothing is coming from the FPGA DAC or for the signal for the ASIC's internal DAC
        self.femb_config.femb.write_reg(17, 0)
        
        #Read from FE output ADCs
        self.femb_config.femb.write_reg(60, 0)
        
#        #TODO Sample at the lower clock speed
            
        #TODO, check if basic or full characterization
        #TODO, check for working chips and make for loop based on that
            
        self.femb_config.fe_reg.set_fe_board(sts=0, snc=self.base, sg=self.gain, st=self.shape,
                                      smn=0, sbf=self.buff, slk = self.leak, stb = 0, s16=0, slkh=self.leak,
                                      sdc=0, sdacsw2=0, sdacsw1=0, sdac=0, remapping=True)
                                      #remapping is to make gain/shaping times/base settings (0-3) consecutive in output and GUI
                   
        self.config_list = self.femb_config.configFeAsic(to_print = False)
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

    def do_analysis(self):
        for num,i in enumerate(self.chip_list):
            if self.config_list[i[0]]:
                print ("Baseline analysis for chip {}".format(i[1]))
                self.result, self.average_baseline, self.baselines = self.analyze.baseline_directory(os.path.join(self.datadir,i[1]), i[1], self.datasubdir, self.outlabel, self.femb_config.gainArray[self.gain],self.femb_config.shapeArray[self.shape],self.leak,self.femb_config.buffArray[self.buff],self.femb_config.baseArray[self.base])
                self.archive_results(i[1],i[0])
            
    def archive_results(self, chip_name, chip_index):
        print("BASELINE AND RMS RESULTS - ARCHIVE")
        
        #add summary variables to output
        self.jsondict['config_gain'] = str( self.femb_config.gainArray[self.gain] )
        self.jsondict['config_shape'] = str( self.femb_config.shapeArray[self.shape] )
        self.jsondict['config_base'] = str( self.femb_config.baseArray[self.base] )
        self.jsondict['config_buff'] = str ( self.femb_config.buffArray[self.buff] )
        self.jsondict['average_baseline'] = str( self.average_baseline )
        self.jsondict['chip_name'] = str( chip_name )
        self.jsondict['chip_index'] = str ( chip_index )
        self.jsondict['config_list'] = self.config_list
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
    print("baseline test!")
    base_test = BASELINE_TESTER()      
    params = json.loads(open(sys.argv[1]).read())    
    base_test.params = params

    base_test.check_setup()
    base_test.record_data()
    base_test.do_analysis()
    base_test.archiveResults()
    
    return base_test.results
     
if __name__ == '__main__':
    main()
