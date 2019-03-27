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
import datetime
import sys
import os
import json
import time
import struct
from femb_python.configuration import CONFIG
from femb_python.configuration.config_base import FEMB_CONFIG_BASE
from femb_python.test_instrument_interface.power_supply_interface import Power_Supply
from femb_python.test_measurements.quad_FE_Board.Tests.Alive_Data_Analysis import Data_Analysis

class ALIVE_TESTER(object):
    
    def __init__(self):
        self.config = CONFIG
        self.functions = FEMB_CONFIG_BASE(self.config)
        self.low_level = self.functions.lower_functions
        self.analyze = Data_Analysis(self.config)
        
        #json output, note module version number defined here
        self.jsondict = {'type':'baseline_test'}
        self.jsondict['alive_code_version'] = '1.0'
        self.jsondict['alive_timestamp']  = datetime.datetime.today().strftime('%Y%m%d%H%M%S')
        
    def check_setup(self):
        print("ALIVE - SETUP")
        self.functions.initBoard(default_sync = False)
        if (self.params['using_power_supply'] == True):
            self.PowerSupply = Power_Supply(self.config)
            if (self.PowerSupply.interface == None):
                sys.exit("SYNCHRONIZATION --> Power Supply not found!")    
        
    def record_data(self):
        
        print("ALIVE - COLLECT DATA")
        #Read from regular ADCs
        self.low_level.femb_udp.write_reg(int(self.config["REGISTERS"]["REG_READOUT_OPTIONS"]), int(self.config["DEFINITIONS"]["READOUT_NORMAL"]))
        
        #Adds tracer bits on data coming in when the internal pulser has an edge
        self.low_level.femb_udp.write_reg(int(self.config["REGISTERS"]["REG_TAGGING"]), int(self.config["DEFINITIONS"]["TAGGING_ON"]))
        
        #Make sure no unwanted pulses
        self.low_level.setInternalPulser(enable = False)
        
        
        self.low_level.femb_udp.write_reg(int(self.config["REGISTERS"]["REG_MUX_MODE"]), int(self.config["DEFINITIONS"]["MUX_GND_DACPULSE"]))
        self.low_level.setExternalPulser(period = int(self.config["MONITOR_SETTINGS"]["MONITOR_FREQ"]), shift = int(self.config["MONITOR_SETTINGS"]["MONITOR_DLY"]), enable = True)
        self.power_info_total = []
        for i in self.params['working_chips']:
            chip_name = self.params['chip_list'][i][1]
            chip_outpathlabel = os.path.join(self.params["datadir"], chip_name, self.params["outlabel"])
            data_directory = os.path.join(chip_outpathlabel, self.config["FILENAMES"]["DATA_NAME"])
            os.makedirs(data_directory, exist_ok=True)
            
            for test in ["test_off", "test_ext"]:
                self.functions.configFeAsic(test_cap="on", base=self.config["ALIVE_SETTINGS"]["ALIVE_BASELINE"], gain=self.config["ALIVE_SETTINGS"]["ALIVE_GAIN"], shape=self.config["ALIVE_SETTINGS"]["ALIVE_PEAK"], 
                                    monitor_ch=None, buffer="on", leak = self.config["ALIVE_SETTINGS"]["ALIVE_LEAK"], monitor_param = None, s16=None, 
                                    acdc=self.config["ALIVE_SETTINGS"]["ALIVE_ACDC"], test_dac=test, dac_value=0)
                self.functions.writeFE()
                
                if (test == "test_off"):
                    self.low_level.femb_udp.write_reg(int(self.config["REGISTERS"]["REG_MUX_MODE"]), int(self.config["DEFINITIONS"]["MUX_GND_DACPULSE"]))
                    self.low_level.setExternalPulser(val = int(self.config["ALIVE_SETTINGS"]["ALIVE_DAC_IN"]), 
                                                    period = int(self.config["ALIVE_SETTINGS"]["ALIVE_TP_PERIOD"]), shift = int(self.config["ALIVE_SETTINGS"]["ALIVE_TP_SHIFT"]), enable = True)
                elif (test == "test_ext"):
                    self.low_level.femb_udp.write_reg(int(self.config["REGISTERS"]["REG_MUX_MODE"]), int(self.config["DEFINITIONS"]["MUX_DACPULSE_GND"]))
                    self.low_level.setExternalPulser(val = int(self.config["ALIVE_SETTINGS"]["ALIVE_DAC_MON"]), 
                                                    period = int(self.config["ALIVE_SETTINGS"]["ALIVE_TP_PERIOD"]), shift = int(self.config["ALIVE_SETTINGS"]["ALIVE_TP_SHIFT"]), enable = True)
                
                packets = int(self.config["ALIVE_SETTINGS"]["ALIVE_PACKETS"])
                data = self.low_level.get_data_chipX(chip = i, tagged = True, packets = packets, header = False)
                for chn in range(int(self.config["DEFAULT"]["NASICCH_MIN"]), int(self.config["DEFAULT"]["NASICCH_MAX"]) + 1, 1):
                    alive_file_notation = self.config["FILENAMES"]["ALIVE_NAMING"]
                    filename = alive_file_notation.format(chn,self.config["ALIVE_SETTINGS"]["ALIVE_LEAK"],test)
                    full_filename = os.path.join(data_directory,filename)
                    chn_data = data[chn]
                    buffer = len(chn_data)
                    bin_data = struct.pack(">%dH"%buffer, *chn_data)
                    
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
        
        self.power_cycle_PCB_power = []
        self.power_cycle_heating_results = []
        self.power_cycle_quad_results = []
        self.power_cycle_fpga_results = []
        print("Test--> Testing {} power cycles ({} seconds in between)".format(self.config["ALIVE_SETTINGS"]["ALIVE_POWER_CYCLES"], self.config["ALIVE_SETTINGS"]["ALIVE_TIME_OFF"]))
        for cycle in range(int(self.config["ALIVE_SETTINGS"]["ALIVE_POWER_CYCLES"])):
            self.power_cycle_PCB_power.append([])
            print("Test--> Cycle {}".format(cycle))
            
            self.functions.turnOffAsics()
            time.sleep(int(self.config["ALIVE_SETTINGS"]["ALIVE_TIME_OFF"]))
            self.functions.turnOnAsics()
            
            for test in ["test_off", "test_ext"]:
                self.functions.configFeAsic(test_cap="on", base=self.config["ALIVE_SETTINGS"]["ALIVE_BASELINE"], gain=self.config["ALIVE_SETTINGS"]["ALIVE_GAIN"], shape=self.config["ALIVE_SETTINGS"]["ALIVE_PEAK"], 
                                    monitor_ch=None, buffer="on", leak = self.config["ALIVE_SETTINGS"]["ALIVE_LEAK"], monitor_param = None, s16=None, 
                                    acdc=self.config["ALIVE_SETTINGS"]["ALIVE_ACDC"], test_dac=test, dac_value=0)
                self.functions.writeFE()
                
                if (test == "test_off"):
                    self.low_level.femb_udp.write_reg(int(self.config["REGISTERS"]["REG_MUX_MODE"]), int(self.config["DEFINITIONS"]["MUX_GND_DACPULSE"]))
                    self.low_level.setExternalPulser(val = int(self.config["ALIVE_SETTINGS"]["ALIVE_DAC_IN"]), 
                                                    period = int(self.config["ALIVE_SETTINGS"]["ALIVE_TP_PERIOD"]), shift = int(self.config["ALIVE_SETTINGS"]["ALIVE_TP_SHIFT"]), enable = True)
                elif (test == "test_ext"):
                    self.low_level.femb_udp.write_reg(int(self.config["REGISTERS"]["REG_MUX_MODE"]), int(self.config["DEFINITIONS"]["MUX_DACPULSE_GND"]))
                    self.low_level.setExternalPulser(val = int(self.config["ALIVE_SETTINGS"]["ALIVE_DAC_MON"]), 
                                                    period = int(self.config["ALIVE_SETTINGS"]["ALIVE_TP_PERIOD"]), shift = int(self.config["ALIVE_SETTINGS"]["ALIVE_TP_SHIFT"]), enable = True)
                
                packets = int(self.config["BASELINE_SETTINGS"]["BASELINE_PACKETS"])
                for i in self.params['working_chips']:
                    chip_name = self.params['chip_list'][i][1]
                    chip_outpathlabel = os.path.join(self.params["datadir"], chip_name, self.params["outlabel"])
                    data_directory = os.path.join(chip_outpathlabel, self.config["FILENAMES"]["DATA_NAME"])
                    os.makedirs(data_directory, exist_ok=True)
                    data = self.low_level.get_data_chipXchnX_tagged(chn = 1, chip = i, packets = packets, header = False)
                    
                    cycle_file_notation = self.config["FILENAMES"]["ALIVE_NAMING2"]
                    filename = cycle_file_notation.format(self.config["ALIVE_SETTINGS"]["ALIVE_LEAK"],test,cycle)
                    full_filename = os.path.join(data_directory,filename)
                    buffer = len(data)
                    bin_data = struct.pack(">%dH"%buffer, *data)
                    
                    with open(full_filename,"wb") as f:
                        f.write(bin_data) 
                        f.close()
                        
                    power_info = self.functions.PCB_power_monitor(chips = i)
                    self.power_cycle_PCB_power[cycle].append(power_info)
            
            if (self.params['using_power_supply'] == True):   
                pwr = self.config["POWER_SUPPLY"]
                self.power_cycle_heating_results.append(self.PowerSupply.measure_params(channel = int(pwr["PS_HEATING_CHN"])))
                self.power_cycle_quad_results.append(self.PowerSupply.measure_params(channel = int(pwr["PS_QUAD_CHN"])))
                self.power_cycle_fpga_results.append(self.PowerSupply.measure_params(channel = int(pwr["PS_FPGA_CHN"])))
                        
        print ("Test--> Input Alive data completed")
        
    def do_analysis(self):
        print("ALIVE - ANALYZE")
        self.results = []
        for i in self.params["working_chips"]:
            chip_name = self.params['chip_list'][i][1]
            chip_outpathlabel = os.path.join(self.params["datadir"], chip_name, self.params["outlabel"])
            data_directory = os.path.join(chip_outpathlabel, self.config["FILENAMES"]["DATA_NAME"])
            
            result = self.analyze.alive_directory(chip_outpathlabel, chip_name, data_directory, ["test_off", "test_ext"], self.config["ALIVE_SETTINGS"]["ALIVE_LEAK"])
            self.results.append(result)
            
    def archiveResults(self):
        print("ALIVE - ARCHIVE")
        
        self.jsondict['alive_executable'] = self.params['executable']
        self.jsondict['alive_datasubdir'] = self.params['datasubdir']
        self.jsondict['alive_outlabel'] = self.params['outlabel']
        self.jsondict['alive_gain'] = self.config["ALIVE_SETTINGS"]["ALIVE_GAIN"]
        self.jsondict['alive_peak'] = self.config["ALIVE_SETTINGS"]["ALIVE_PEAK"]
        self.jsondict['alive_leak'] = self.config["ALIVE_SETTINGS"]["ALIVE_LEAK"]
        self.jsondict['alive_acdc'] = self.config["ALIVE_SETTINGS"]["ALIVE_ACDC"]
        self.jsondict['alive_baseline'] = self.config["ALIVE_SETTINGS"]["ALIVE_BASELINE"]
        
        self.jsondict['PS_heating_voltage'] = self.heating_results[0]
        self.jsondict['PS_heating_current'] = self.heating_results[1]
        self.jsondict['PS_quad_voltage'] = self.quad_results[0]
        self.jsondict['PS_quad_current'] = self.quad_results[1]
        self.jsondict['PS_fpga_voltage'] = self.fpga_results[0]
        self.jsondict['PS_fpga_current'] = self.fpga_results[1]
        
        for cycle in range(int(self.config["ALIVE_SETTINGS"]["ALIVE_POWER_CYCLES"])):
            self.jsondict['PS_heating_voltage_cycle{}'.format(cycle)] = self.power_cycle_heating_results[cycle][0]
            self.jsondict['PS_heating_current_cycle{}'.format(cycle)] = self.power_cycle_heating_results[cycle][1]
            self.jsondict['PS_quad_voltage_cycle{}'.format(cycle)] = self.power_cycle_quad_results[cycle][0]
            self.jsondict['PS_quad_current_cycle{}'.format(cycle)] = self.power_cycle_quad_results[cycle][1]
            self.jsondict['PS_fpga_voltage_cycle{}'.format(cycle)] = self.power_cycle_fpga_results[cycle][0]
            self.jsondict['PS_fpga_current_cycle{}'.format(cycle)] = self.power_cycle_fpga_results[cycle][1]

        for num, i in enumerate(self.params['working_chips']):
            chip_name = self.params['chip_list'][i][1]
            jsonFile = os.path.join(self.params["datadir"],chip_name,self.params["datasubdir"],self.params["outlabel"], self.config["FILENAMES"]["RESULTS"])
            if (self.results[num] == True):
                self.jsondict['alive_result'] = "PASS"
            elif (self.results[num] == False):
                self.jsondict['alive_result'] = "FAIL"
            else:
                self.jsondict['alive_result'] = "N/A"
                
            #TODO add which channels, cycles, tests, failed
                
            self.jsondict['vdda_shunt_voltage'] = self.power_info_total[num][0][0]
            self.jsondict['vdda_bus_voltage'] = self.power_info_total[num][0][1]
            self.jsondict['vdda_current'] = self.power_info_total[num][0][2]
            self.jsondict['vddp_shunt_voltage'] = self.power_info_total[num][1][0]
            self.jsondict['vddp_bus_voltage'] = self.power_info_total[num][1][1]
            self.jsondict['vddp_current'] = self.power_info_total[num][1][2]
                
                
            for cycle in range(int(self.config["ALIVE_SETTINGS"]["ALIVE_POWER_CYCLES"])):
                print(self.power_cycle_PCB_power)
                self.jsondict['vdda_shunt_voltage_cycle{}'.format(cycle)] = self.power_cycle_PCB_power[cycle][num][0][0]
                self.jsondict['vdda_bus_voltage_cycle{}'.format(cycle)] = self.power_cycle_PCB_power[cycle][num][0][1]
                self.jsondict['vdda_current_cycle{}'.format(cycle)] = self.power_cycle_PCB_power[cycle][num][0][2]
                self.jsondict['vddp_shunt_voltage_cycle{}'.format(cycle)] = self.power_cycle_PCB_power[cycle][num][1][0]
                self.jsondict['vddp_bus_voltage_cycle{}'.format(cycle)] = self.power_cycle_PCB_power[cycle][num][1][1]
                self.jsondict['vddp_current_cycle{}'.format(cycle)] = self.power_cycle_PCB_power[cycle][num][1][2]
                
            with open(jsonFile,'a') as outfile:
                json.dump(self.jsondict, outfile, indent=4)
                
            jsonFile = os.path.join(self.params["datadir"],chip_name,self.params["datasubdir"],self.config["FILENAMES"]["RESULTS"])
            with open(jsonFile,'r') as f:
                existing_json = json.load(f)
            
            existing_json['alive_outlabel'] = self.params['outlabel']
            with open(jsonFile,'w') as outfile:
                json.dump(existing_json, outfile, indent=4)
                
def main():
    alive_test = ALIVE_TESTER()      
    params = json.loads(open(sys.argv[1]).read())    
    alive_test.params = params

    alive_test.check_setup()
    alive_test.record_data()
    alive_test.do_analysis()
    alive_test.archiveResults()
     
if __name__ == '__main__':
    main()
