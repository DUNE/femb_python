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
import datetime


from femb_python.configuration import CONFIG
from femb_python.configuration.config_base import FEMB_CONFIG_BASE
from femb_python.test_measurements.quad_FE_Board.Baseline_Data_Analysis import Data_Analysis

class BASELINE_TESTER(object):
    
    def __init__(self):
        self.config = CONFIG
        self.functions = FEMB_CONFIG_BASE(self.config)
        self.low_level = self.functions.lower_functions
        self.analyze = Data_Analysis(self.config)
        
        #json output, note module version number defined here
        self.jsondict = {'type':'baseline_test'}
        self.jsondict['baseline_code_version'] = '1.0'
        self.jsondict['baseline_timestamp']  = datetime.datetime.today().strftime('%Y%m%d%H%M%S')
        
    def check_setup(self):
        print("BASELINE - SETUP")
        self.functions.initBoard(default_sync = False)

    def record_data(self):
        print("BASELINE - COLLECT DATA")
        for i in self.params['working_chips']:
            chip_name = self.params['chip_list'][i][1]
            chip_outpathlabel = os.path.join(self.params["datadir"], chip_name, self.params["outlabel"])
            data_directory = os.path.join(chip_outpathlabel, self.config["FILENAMES"]["DATA_NAME"])
            os.makedirs(data_directory, exist_ok=True)
            self.low_level.femb_udp.write_reg(int(self.config["REGISTERS"]["REG_MUX_MODE"]), int(self.config["DEFINITIONS"]["MUX_GND_GND"]))
                
            #TODO options if user wants to try other ones
            self.gain = self.config["BASELINE_SETTINGS"]["BASELINE_GAIN"]
            self.shape = self.config["BASELINE_SETTINGS"]["BASELINE_PEAK"]
            self.leak = self.config["BASELINE_SETTINGS"]["BASELINE_LEAK"]
            self.buff = self.config["BASELINE_SETTINGS"]["BASELINE_BUFFER"]
                
            if (self.buff == "on"):
                self.low_level.femb_udp.write_reg(int(self.config["REGISTERS"]["REG_SAMPLESPEED"]), int(self.config["INITIAL_SETTINGS"]["DEFAULT_SAMPLE_SPEED"]))
            elif (self.buff == "off"):
                self.low_level.femb_udp.write_reg(int(self.config["REGISTERS"]["REG_SAMPLESPEED"]), int(self.config["INITIAL_SETTINGS"]["UNBUFFERED_SAMPLE_SPEED"]))
            else:
                print("FE_baseline_test --> buffer is not defined.  Should be 'on' or 'off', but is {}".format(self.buff))
            
            for base in ["200mV", "900mV"]:
                self.functions.configFeAsic(test_cap="off", base=base, gain=self.gain, shape=self.shape, monitor_ch=None, buffer=self.buff, 
                       leak = self.leak, monitor_param = None, s16=None, acdc="dc", test_dac="test_off", dac_value=0)
            
                self.functions.writeFE()
                
                for chn in range(int(self.config["DEFAULT"]["NASICCH_MIN"]), int(self.config["DEFAULT"]["NASICCH_MAX"]) + 1, 1):
                    self.low_level.selectChipChannel(chip = i, chn = chn)
                    baseline_file_notation = self.config["FILENAMES"]["BASELINE_NAMING"]
                    filename = baseline_file_notation.format(chn,self.gain,self.shape,self.leak,base, self.buff)
                    full_filename = os.path.join(data_directory,filename)            
                    packets = int(self.config["BASELINE_SETTINGS"]["BASELINE_PACKETS"])
                    rawdata = self.low_level.get_data_chipXchnX(chip = i, chn = chn, packets = packets, data_format = "bin", header = False)
            
                    with open(full_filename,"wb") as f:
                        f.write(rawdata) 
                        f.close()
                        
        self.low_level.femb_udp.write_reg(int(self.config["REGISTERS"]["REG_SAMPLESPEED"]), int(self.config["INITIAL_SETTINGS"]["DEFAULT_SAMPLE_SPEED"]))

    def do_analysis(self):
        print("BASELINE - ANALYZE")
        analysis = ["mean"]
        self.results = []
        self.average_baseline_200 = []
        self.average_baseline_900 = []
        self.baseline_200 = []
        self.baseline_900 = []
        for i in self.params["working_chips"]:
            chip_name = self.params['chip_list'][i][1]
            chip_outpathlabel = os.path.join(self.params["datadir"], chip_name, self.params["outlabel"])
            data_directory = os.path.join(chip_outpathlabel, self.config["FILENAMES"]["DATA_NAME"])
            result, average_200, average_900, baselines_200, baselines_900 = self.analyze.baseline_directory(chip_outpathlabel, data_directory, chip_name, i, analysis)
            self.results.append(result)
            self.average_baseline_200.append(average_200)
            self.average_baseline_900.append(average_900)
            self.baseline_200.append(baselines_200)
            self.baseline_900.append(baselines_900)
            
    def archiveResults(self):
        print("BASELINE - ARCHIVE")
        
        self.jsondict['baseline_executable'] = self.params['executable']
        self.jsondict['baseline_datasubdir'] = self.params['datasubdir']
        self.jsondict['baseline_outlabel'] = self.params['outlabel']
        self.jsondict['baseline_gain'] = self.config["BASELINE_SETTINGS"]["BASELINE_GAIN"]
        self.jsondict['baseline_peak'] = self.config["BASELINE_SETTINGS"]["BASELINE_PEAK"]
        self.jsondict['baseline_leak'] = self.config["BASELINE_SETTINGS"]["BASELINE_LEAK"]
        self.jsondict['baseline_buffer'] = self.config["BASELINE_SETTINGS"]["BASELINE_BUFFER"]

        for num,i in enumerate(self.params['working_chips']):
            chip_name = self.params['chip_list'][i][1]
            jsonFile = os.path.join(self.params["datadir"],chip_name,self.params["datasubdir"],self.config["FILENAMES"]["RESULTS"])
            with open(jsonFile, mode='r') as f:
                existing_json = json.load(f)
            if (self.results[num] == True):
                self.jsondict['baseline_result'] = "PASS"
            elif (self.results[num] == False):
                self.jsondict['baseline_result'] = "FAIL"
            else:
                self.jsondict['baseline_result'] = "N/A"
                
            self.jsondict['baseline_200_average'] = self.average_baseline_200[num]
            self.jsondict['baseline_900_average'] = self.average_baseline_900[num]
            
            for chn in range(int(self.config["DEFAULT"]["NASICCH_MIN"]), int(self.config["DEFAULT"]["NASICCH_MAX"]) + 1, 1):
                jsname = "baseline_200_channel{}".format(chn)
                self.jsondict[jsname] = self.baseline_200[num][chn]
                jsname = "baseline_900_channel{}".format(chn)
                self.jsondict[jsname] = self.baseline_900[num][chn]
                
            with open(jsonFile,'w') as outfile:
                existing_json.update(self.jsondict)
                json.dump(existing_json, outfile, indent=4)
        
def main():
    base_test = BASELINE_TESTER()      
    params = json.loads(open(sys.argv[1]).read())    
    base_test.params = params

    base_test.check_setup()
    base_test.record_data()
    base_test.do_analysis()
    base_test.archiveResults()
     
if __name__ == '__main__':
    main()
