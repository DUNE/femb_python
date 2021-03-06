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
import time
from femb_python.configuration import CONFIG
from femb_python.configuration.config_base import FEMB_CONFIG_BASE
from femb_python.test_instrument_interface.power_supply_interface import Power_Supply

class SYNC_ADCS(object):
    
    def __init__(self):      
        
        self.config = CONFIG
        self.functions = FEMB_CONFIG_BASE(self.config)
        self.low_level = self.functions.lower_functions
        self.sync_functions = self.functions.sync
        self.plotting = self.functions.sync.plot

        #json output, note module version number defined here
        self.syncdict = {'type':'sync_adcs'}
        self.syncdict['sync_code_version'] = '1.1'
        self.syncdict['sync_timestamp']  = datetime.datetime.today().strftime('%Y%m%d%H%M%S')
        
    def check_setup(self):
        print("SYNCHRONIZATION - SETUP")
        self.functions.initBoard(default_sync = False)
        if (self.params['using_power_supply'] == True):
            self.PowerSupply = Power_Supply(self.config)
            if (self.PowerSupply.interface == None):
                sys.exit("SYNCHRONIZATION --> Power Supply not found!")            
        
    def sync(self):
        print("SYNCHRONIZATION - COLLECT DATA")
        self.return_results = self.sync_functions.syncADC(**self.params)
        
        self.low_level.femb_udp.write_reg(int(self.config["REGISTERS"]["REG_TAGGING"]), int(self.config["DEFINITIONS"]["TAGGING_ON"]))
        self.low_level.setExternalPulser(val=int(self.config["INITIAL_SETTINGS"]["DEFAULT_EXTERNAL_DAC_VAL"], 16), 
                               period=int(self.config["INITIAL_SETTINGS"]["DEFAULT_EXTERNAL_DAC_TP_PERIOD"]), shift=int(self.config["INITIAL_SETTINGS"]["DEFAULT_EXTERNAL_DAC_TP_SHIFT"]), enable=True)

        self.functions.configFeAsic(test_cap="on", base=self.config["SYNC_SETTINGS"]["SYNC_BASELINE"], gain=self.config["SYNC_SETTINGS"]["SYNC_GAIN"], shape=self.config["SYNC_SETTINGS"]["SYNC_PEAK"], 
                                        monitor_ch=None, buffer=self.config["SYNC_SETTINGS"]["SYNC_BUFFER"], leak = self.config["SYNC_SETTINGS"]["SYNC_LEAK"], monitor_param = None, s16=None, 
                                        acdc=self.config["SYNC_SETTINGS"]["SYNC_ACDC"], test_dac="test_int", dac_value=int(self.config["SYNC_SETTINGS"]["SYNC_DAC_PEAK_HEIGHT"]))
        self.functions.writeFE()
        self.low_level.femb_udp.write_reg(int(self.config["REGISTERS"]["REG_MUX_MODE"]), int(self.config["DEFINITIONS"]["MUX_GND_GND_INTPULSE"]))
        self.power_info_total = []
        for i in self.params['working_chips']:
            chip_index = self.params['chip_list'][i][0]
            chip_name = self.params['chip_list'][i][1]
            chip_outpathlabel = os.path.join(self.params["datadir"], chip_name, self.params["outlabel"])
            data = self.low_level.get_data_chipX(chip = chip_index, packets = int(self.config["SYNC_SETTINGS"]["SYNC_PACKETS"]), tagged = True)
            print("quad_sync_adcs--> Printing internal synchronization plot for Chip {}".format(chip_name))
            sync_int_text = self.config["FILENAMES"]["SYNC_FILE_INT"].format(chip_name)
            savefig = os.path.join(chip_outpathlabel, sync_int_text)
            power_info = self.functions.PCB_power_monitor(chips = i)
            self.power_info_total.append(power_info)
            self.plotting.plot_chip(data = data, plot_name = savefig, title_name = "Chip {} Internal Sync: Gain = {}/fC, Peaking Time = {}".format(chip_name, self.config["SYNC_SETTINGS"]["SYNC_GAIN"],
                                                                                                                                                        self.config["SYNC_SETTINGS"]["SYNC_PEAK"]), 
                                                                                                                                                        power = power_info, length = 1000)
        if (self.params['using_power_supply'] == True):                                                                                                                                            
            pwr = self.config["POWER_SUPPLY"]
            self.heating_results = self.PowerSupply.measure_params(channel = int(pwr["PS_HEATING_CHN"]))
            self.quad_results = self.PowerSupply.measure_params(channel = int(pwr["PS_QUAD_CHN"]))
            self.fpga_results = self.PowerSupply.measure_params(channel = int(pwr["PS_FPGA_CHN"]))
        self.low_level.femb_udp.write_reg(int(self.config["REGISTERS"]["REG_MUX_MODE"]), int(self.config["DEFINITIONS"]["MUX_GND_DACPULSE"]))

        for i in self.params['working_chips']:
            chip_index = self.params['chip_list'][i][0]
            chip_name = self.params['chip_list'][i][1]
            chip_outpathlabel = os.path.join(self.params["datadir"], chip_name, self.params["outlabel"])
            data = self.low_level.get_data_chipX(chip = chip_index, packets = int(self.config["SYNC_SETTINGS"]["SYNC_PACKETS"]), tagged = True)
            print("quad_sync_adcs--> Printing external synchronization plot for Chip {}".format(chip_name))
            sync_ext_text = self.config["FILENAMES"]["SYNC_FILE_EXT"].format(chip_name)
            savefig = os.path.join(chip_outpathlabel, sync_ext_text)
            power_info = self.functions.PCB_power_monitor(chips = i)
            self.plotting.plot_chip(data = data, plot_name = savefig, title_name = "Chip {} External Sync: Gain = {}/fC, Peaking Time = {}".format(chip_name, self.config["SYNC_SETTINGS"]["SYNC_GAIN"],
                                                                                                                                                        self.config["SYNC_SETTINGS"]["SYNC_PEAK"]), 
                                                                                                                                                        power = power_info, length = 1000)
            
        self.low_level.setExternalPulser(enable=False)
        self.low_level.femb_udp.write_reg(int(self.config["REGISTERS"]["REG_MUX_MODE"]), int(self.config["DEFINITIONS"]["MUX_GND_GND"]))
        self.low_level.femb_udp.write_reg(int(self.config["REGISTERS"]["REG_TAGGING"]), int(self.config["DEFINITIONS"]["TAGGING_OFF"]))
        
    def do_analysis(self, ):
        print("SYNCHRONIZATION - ANALYZE")
        self.results = self.params["chip_list"]
        for num, i in enumerate(range(len(self.results))):
            if (self.return_results[num] == True):
                self.results[i].append("PASS")
            elif (self.return_results[num] == False):
                self.results[i].append("FAIL")
            else:
                self.results[i].append("NOT TESTED (SPI ERROR)")
                
    def archiveResults(self):
        print("SYNCHRONIZATION - ARCHIVE")
        
        self.jsondict = {'boardID':self.params['boardid']}
        self.jsondict['fw_ver'] = self.params['fw_ver']
        self.jsondict['test_category'] = self.params['test_category']
        self.jsondict['test_stand'] = self.params['test_stand']
        self.jsondict['chipver'] = self.params['chipver']
        self.jsondict['sw_version'] = self.params['sw_version']
        self.jsondict['fpgamezz'] = self.params['fpgamezz']
        self.jsondict['femb_config'] = self.params['femb_config']
        self.jsondict['paramfile'] = self.params['paramfile']
        self.jsondict['sync_outlabel'] = self.params['outlabel']
        for i in self.params['working_chips']:
            chip_index = self.params['chip_list'][i][0]
            chip_name = self.params['chip_list'][i][1]
            jsonFile = os.path.join(self.params["datadir"],chip_name,self.params["datasubdir"],self.config["FILENAMES"]["RESULTS"])
            self.jsondict['chip_index'] = chip_index
            self.jsondict['chip_name'] = chip_name
            self.jsondict['socket'] = self.params["socket{}id".format(chip_index)]
            with open(jsonFile,'a') as outfile:
                json.dump(self.jsondict, outfile, indent=4)
        
        self.syncdict['sync_baseline'] = self.config["SYNC_SETTINGS"]["SYNC_BASELINE"]
        self.syncdict['sync_buffer'] = self.config["SYNC_SETTINGS"]["SYNC_BUFFER"]
        self.syncdict['sync_gain'] = self.config["SYNC_SETTINGS"]["SYNC_GAIN"]
        self.syncdict['sync_peak'] = self.config["SYNC_SETTINGS"]["SYNC_PEAK"]
        self.syncdict['sync_acdc'] = self.config["SYNC_SETTINGS"]["SYNC_ACDC"]
        self.syncdict['sync_leak'] = self.config["SYNC_SETTINGS"]["SYNC_LEAK"]
        self.syncdict['sync_executable'] = self.params['executable']
        self.syncdict['sync_datasubdir'] = self.params['datasubdir']
        
        if (self.params['using_power_supply'] == True):  
            self.syncdict['PS_heating_voltage'] = self.heating_results[0]
            self.syncdict['PS_heating_current'] = self.heating_results[1]
            self.syncdict['PS_quad_voltage'] = self.quad_results[0]
            self.syncdict['PS_quad_current'] = self.quad_results[1]
            self.syncdict['PS_fpga_voltage'] = self.fpga_results[0]
            self.syncdict['PS_fpga_current'] = self.fpga_results[1]

        for num, i in enumerate(self.params['working_chips']):
            chip_index = self.params['chip_list'][i][0]
            chip_name = self.params['chip_list'][i][1]
            jsonFile = os.path.join(self.params["datadir"],chip_name,self.params["datasubdir"],self.params["outlabel"],self.config["FILENAMES"]["RESULTS"])
            self.syncdict['sync_result'] = self.results[chip_index][2]
            self.syncdict['vdda_shunt_voltage'] = self.power_info_total[num][0][0]
            self.syncdict['vdda_bus_voltage'] = self.power_info_total[num][0][1]
            self.syncdict['vdda_current'] = self.power_info_total[num][0][2]
            self.syncdict['vddp_shunt_voltage'] = self.power_info_total[num][1][0]
            self.syncdict['vddp_bus_voltage'] = self.power_info_total[num][1][1]
            self.syncdict['vddp_current'] = self.power_info_total[num][1][2]
            with open(jsonFile,'a') as outfile:
                json.dump(self.syncdict, outfile, indent=4)

def main():
    '''
    sync the ADCs
    '''
    sync_adcs = SYNC_ADCS()
    params = json.loads(open(sys.argv[1]).read())
    params["to_print"] = True
    sync_adcs.params = params
    sync_adcs.check_setup()
    sync_adcs.sync()
    sync_adcs.do_analysis()
    sync_adcs.archiveResults()

if __name__ == '__main__':
    main()