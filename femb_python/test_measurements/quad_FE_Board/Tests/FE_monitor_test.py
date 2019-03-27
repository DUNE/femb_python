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
from femb_python.test_measurements.quad_FE_Board.Tests.Monitor_Data_Analysis import Data_Analysis
from femb_python.test_instrument_interface.power_supply_interface import Power_Supply

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
        if (self.params['using_power_supply'] == True):
            self.PowerSupply = Power_Supply(self.config)
            if (self.PowerSupply.interface == None):
                sys.exit("SYNCHRONIZATION --> Power Supply not found!")      

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
        self.power_info_total = []
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
                    
            power_info = self.functions.PCB_power_monitor(chips = i)
            self.power_info_total.append(power_info)
            
        if (self.params['using_power_supply'] == True):   
            pwr = self.config["POWER_SUPPLY"]
            self.heating_results = self.PowerSupply.measure_params(channel = int(pwr["PS_HEATING_CHN"]))
            self.quad_results = self.PowerSupply.measure_params(channel = int(pwr["PS_QUAD_CHN"]))
            self.fpga_results = self.PowerSupply.measure_params(channel = int(pwr["PS_FPGA_CHN"]))
                    
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
            with open(jsonFile,'r') as f:
                existing_json = json.load(f)
            baseline_outlabel = existing_json["baseline_outlabel"]
            jsonFile = os.path.join(self.params["datadir"],chip_name,self.params["datasubdir"],baseline_outlabel, self.config["FILENAMES"]["RESULTS"])
            
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
        
        self.jsondict['PS_heating_voltage'] = self.heating_results[0]
        self.jsondict['PS_heating_current'] = self.heating_results[1]
        self.jsondict['PS_quad_voltage'] = self.quad_results[0]
        self.jsondict['PS_quad_current'] = self.quad_results[1]
        self.jsondict['PS_fpga_voltage'] = self.fpga_results[0]
        self.jsondict['PS_fpga_current'] = self.fpga_results[1]

        for num, i in enumerate(self.params['working_chips']):
            chip_name = self.params['chip_list'][i][1]
            jsonFile = os.path.join(self.params["datadir"],chip_name,self.params["datasubdir"],self.params["outlabel"], self.config["FILENAMES"]["RESULTS"])
            if (self.results[num] == True):
                self.jsondict['monitor_result'] = "PASS"
            elif (self.results[num] == False):
                self.jsondict['monitor_result'] = "FAIL"
            else:
                self.jsondict['monitor_result'] = "N/A"
                
            self.jsondict['monitor_average_peak'] = self.average_peak[num]
            self.jsondict['vdda_shunt_voltage'] = self.power_info_total[num][0][0]
            self.jsondict['vdda_bus_voltage'] = self.power_info_total[num][0][1]
            self.jsondict['vdda_current'] = self.power_info_total[num][0][2]
            self.jsondict['vddp_shunt_voltage'] = self.power_info_total[num][1][0]
            self.jsondict['vddp_bus_voltage'] = self.power_info_total[num][1][1]
            self.jsondict['vddp_current'] = self.power_info_total[num][1][2]
            
            for chn in range(int(self.config["DEFAULT"]["NASICCH_MIN"]), int(self.config["DEFAULT"]["NASICCH_MAX"]) + 1, 1):
                jsname = "monitor_peak{}".format(chn)
                self.jsondict[jsname] = self.peaks[num][chn][1]
                jsname = "monitor_difference{}".format(chn)
                self.jsondict[jsname] = self.differences[num][chn]
                
            with open(jsonFile,'a') as outfile:
                json.dump(self.jsondict, outfile, indent=4)        
                
            jsonFile = os.path.join(self.params["datadir"],chip_name,self.params["datasubdir"],self.config["FILENAMES"]["RESULTS"])
            with open(jsonFile,'r') as f:
                existing_json = json.load(f)
            
            existing_json['monitor_outlabel'] = self.params['outlabel']
            with open(jsonFile,'w') as outfile:
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