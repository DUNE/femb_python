from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import
from builtins import range
from builtins import int
from builtins import str
from builtins import hex
import struct
from future import standard_library
standard_library.install_aliases()
from builtins import object
import sys
import os
import json
import datetime
from femb_python.configuration import CONFIG
from femb_python.configuration.config_base import FEMB_CONFIG_BASE
from femb_python.test_measurements.quad_FE_Board.Monitor_Data_Analysis import Data_Analysis

class MONITOR_TESTER(object):
    
    def __init__(self):
        self.config = CONFIG
        self.functions = FEMB_CONFIG_BASE(self.config)
        self.low_level = self.functions.lower_functions
        self.analyze = Data_Analysis(self.config)
        
        #json output, note module version number defined here
        self.jsondict = {'type':'baseline_test'}
        self.jsondict['monitor_code_version'] = '1.0'
        self.jsondict['monitor_timestamp']  = datetime.datetime.today().strftime('%Y%m%d%H%M%S')

        
    def check_setup(self):
        print("MONITOR - SETUP")
        self.functions.initBoard(default_sync = False)

    def record_data(self):
        print("MONITOR - COLLECT DATA")
        #Read from TEST output ADCs
        self.low_level.femb_udp.write_reg(int(self.config["REGISTERS"]["REG_READOUT_OPTIONS"]), int(self.config["DEFINITIONS"]["READOUT_TEST_ADC"]))
        
        #Select the monitor readout to ADC
        self.low_level.femb_udp.write_reg(int(self.config["REGISTERS"]["REG_MUX_MODE"]), int(self.config["DEFINITIONS"]["MUX_ADC_GND"]))
        #Adds tracer bits on data coming in when the internal pulser has an edge
        self.low_level.femb_udp.write_reg(int(self.config["REGISTERS"]["REG_TAGGING"]), int(self.config["DEFINITIONS"]["TAGGING_ON"]))
        
        #Get the ASIC to send out pulses
        self.low_level.setInternalPulser(period = int(self.config["MONITOR_SETTINGS"]["MONITOR_FREQ"]), shift = int(self.config["MONITOR_SETTINGS"]["MONITOR_DLY"]), enable = True)
        self.low_level.setExternalPulser(enable = False)
        
        for i in self.params['working_chips']:
            chip_name = self.params['chip_list'][i][1]
            chip_outpathlabel = os.path.join(self.params["datadir"], chip_name, self.params["outlabel"])
            data_directory = os.path.join(chip_outpathlabel, self.config["FILENAMES"]["DATA_NAME"])
            os.makedirs(data_directory, exist_ok=True)
            
            for chn in range(int(self.config["DEFAULT"]["NASICCH_MIN"]), int(self.config["DEFAULT"]["NASICCH_MAX"]) + 1, 1):
                self.functions.configFeAsic(test_cap="on", base=self.config["SYNC_SETTINGS"]["SYNC_BASELINE"], gain=self.config["SYNC_SETTINGS"]["SYNC_GAIN"], shape=self.config["SYNC_SETTINGS"]["SYNC_PEAK"], 
                                    monitor_ch=None, buffer=self.config["SYNC_SETTINGS"]["SYNC_BUFFER"], leak = self.config["SYNC_SETTINGS"]["SYNC_LEAK"], monitor_param = None, s16=None, 
                                    acdc=self.config["SYNC_SETTINGS"]["SYNC_ACDC"], test_dac="test_int", dac_value=int(self.config["MONITOR_SETTINGS"]["MONITOR_AMPL"]))
                self.functions.FE_Regs.set_fe_chn(chip = i, chn = chn, smn = 1)
                self.functions.writeFE()
                
                monitor_file_notation = self.config["FILENAMES"]["MONITOR_NAMING"]
                filename = monitor_file_notation.format(chn)
                full_filename = os.path.join(data_directory,filename)            
                packets = int(self.config["MONITOR_SETTINGS"]["MONITOR_PACKETS"])
                data = self.low_level.get_data_chipXchnX_tagged(chip = i, chn = chn, packets = packets, data_format = "bin", header = False)
                buffer = len(data)
                bin_data = struct.pack(">%dH"%buffer, *data)
                
                with open(full_filename,"wb") as f:
                    f.write(bin_data) 
                    f.close()
                    
        #Bring things back to normal
        self.low_level.femb_udp.write_reg(int(self.config["REGISTERS"]["REG_READOUT_OPTIONS"]), int(self.config["DEFINITIONS"]["READOUT_NORMAL"]))
        self.low_level.femb_udp.write_reg(int(self.config["REGISTERS"]["REG_TAGGING"]), int(self.config["DEFINITIONS"]["TAGGING_OFF"]))
        self.low_level.setInternalPulser(period = int(self.config["SYNC_SETTINGS"]["SYNC_INTERNAL_PULSE_FREQ"]), shift = int(self.config["SYNC_SETTINGS"]["SYNC_INTERNAL_PULSE_DLY"]), enable = False)

    def do_analysis(self):
        print("MONITOR - ANALYZE")
        self.results = []
        self.peaks = []
        self.differences = []
        self.average_peak = []
        for i in self.params["working_chips"]:
            chip_name = self.params['chip_list'][i][1]
            chip_outpathlabel = os.path.join(self.params["datadir"], chip_name, self.params["outlabel"])
            data_directory = os.path.join(chip_outpathlabel, self.config["FILENAMES"]["DATA_NAME"])
            #To grab baseline
            jsonFile = os.path.join(self.params["datadir"],chip_name,self.params["datasubdir"],self.config["FILENAMES"]["RESULTS"])
            
            result, peaks, differences, average_peak = self.analyze.monitor_directory(chip_outpathlabel, data_directory, chip_name, i, jsonFile)
            self.results.append(result)
            self.peaks.append(peaks)
            self.differences.append(differences)
            self.average_peak.append(average_peak)
        
    def archiveResults(self):
        print("MONITOR - ARCHIVE")
        
        self.jsondict['monitor_executable'] = self.params['executable']
        self.jsondict['monitor_datasubdir'] = self.params['datasubdir']
        self.jsondict['monitor_outlabel'] = self.params['outlabel']

        for chip in self.params["working_chips"]:
            chip_name = self.params['chip_list'][chip][1]
            jsonFile = os.path.join(self.params["datadir"],chip_name,self.params["datasubdir"],self.config["FILENAMES"]["RESULTS"])
            with open(jsonFile, mode='r') as f:
                existing_json = json.load(f)
            if (self.results[chip] == True):
                self.jsondict['monitor_result'] = "PASS"
            elif (self.results[chip] == False):
                self.jsondict['monitor_result'] = "FAIL"
            else:
                self.jsondict['monitor_result'] = "N/A"
                
            self.jsondict['monitor_average_peak'] = self.average_peak[chip]
            
            for chn in range(int(self.config["DEFAULT"]["NASICCH_MIN"]), int(self.config["DEFAULT"]["NASICCH_MAX"]) + 1, 1):
                jsname = "monitor_peaks{}".format(chn)
                self.jsondict[jsname] = self.peaks[chip][chn][1]
                jsname = "monitor_differences{}".format(chn)
                self.jsondict[jsname] = self.differences[chip][chn]
                
            with open(jsonFile,'w') as outfile:
                existing_json.update(self.jsondict)
                json.dump(existing_json, outfile, indent=4)            
        
def main():
    mon_test = MONITOR_TESTER()      
    params = json.loads(open(sys.argv[1]).read())    
    mon_test.params = params

    mon_test.check_setup()
    mon_test.record_data()
    mon_test.do_analysis()
    mon_test.archiveResults()
     
if __name__ == '__main__':
    main()