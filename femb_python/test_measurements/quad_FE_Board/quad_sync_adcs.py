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

class SYNC_ADCS(object):
    
    def __init__(self):      
        
        self.config = CONFIG
        self.functions = FEMB_CONFIG_BASE(self.config)
        self.low_level = self.functions.lower_functions
        self.sync_functions = self.functions.sync
        self.plotting = self.functions.sync.plot

        #json output, note module version number defined here
        self.jsondict = {'type':'sync_adcs'}
        self.jsondict['version'] = '1.1'
        self.jsondict['timestamp']  = datetime.datetime.today().strftime('%Y%m%d%H%M%S')
        
    def sync(self):
        print("SYNCHRONIZATION - COLLECT DATA")
        
        self.functions.initBoard(default_sync = False)
        self.return_results = self.sync_functions.syncADC(**self.params)
        
        self.low_level.femb_udp.write_reg(int(self.config["REGISTERS"]["REG_TAGGING"]), int(self.config["DEFINITIONS"]["TAGGING_ON"]))
        self.low_level.setExternalPulser(val=0x380, 
                               period=int(self.config["INITIAL_SETTINGS"]["DEFAULT_EXTERNAL_DAC_TP_PERIOD"]), shift=int(self.config["INITIAL_SETTINGS"]["DEFAULT_EXTERNAL_DAC_TP_SHIFT"]), enable=True)

        self.functions.ASIC_functions.configFeAsic(test_cap="on", base=self.config["SYNC_SETTINGS"]["SYNC_BASELINE"], gain=self.config["SYNC_SETTINGS"]["SYNC_GAIN"], shape=self.config["SYNC_SETTINGS"]["SYNC_PEAK"], 
                                        monitor_ch=None, buffer=self.config["SYNC_SETTINGS"]["SYNC_BUFFER"], leak = self.config["SYNC_SETTINGS"]["SYNC_LEAK"], monitor_param = None, s16=None, 
                                        acdc=self.config["SYNC_SETTINGS"]["SYNC_ACDC"], test_dac="test_int", dac_value=int(self.config["SYNC_SETTINGS"]["SYNC_DAC_PEAK_HEIGHT"]))
                       
        self.low_level.femb_udp.write_reg(int(self.config["REGISTERS"]["REG_MUX_MODE"]), int(self.config["DEFINITIONS"]["MUX_GND_GND_INTPULSE"]))
        
        self.low_level.setInternalPulser(period = int(self.config["SYNC_SETTINGS"]["SYNC_INTERNAL_PULSE_FREQ"]), shift = int(self.config["SYNC_SETTINGS"]["SYNC_INTERNAL_PULSE_DLY"]), enable = True)

        for num,i in enumerate(self.params["chip_list"]):
            chip_outpathlabel = os.path.join(self.params["datadir"], i[1], self.params["outlabel"])
            data = self.low_level.get_data_chipX(chip = i[0], packets = 5, tagged = True)
            print("quad_sync_adcs--> Printing synchronization plot for Chip {}".format(i[1]))
            savefig = os.path.join(chip_outpathlabel, "Sync_Plot_Internal")
            self.plotting.plot_chip(data = data, plot_name = savefig, title_name = "Pulses for synchronization: Gain = 14 mv/fC, Peaking Time = 2 us, Buffer on", length = 1000)
            
#        self.low_level.setInternalPulser(enable=False)
        self.low_level.femb_udp.write_reg(int(self.config["REGISTERS"]["REG_MUX_MODE"]), int(self.config["DEFINITIONS"]["MUX_GND_DACPULSE"]))

        for num,i in enumerate(self.params["chip_list"]):
            chip_outpathlabel = os.path.join(self.params["datadir"], i[1], self.params["outlabel"])
            data = self.low_level.get_data_chipX(chip = i[0], packets = 5, tagged = True)
            print("quad_sync_adcs--> Printing synchronization plot for Chip {}".format(i[1]))
            savefig = os.path.join(chip_outpathlabel, "Sync_Plot_External")
            self.plotting.plot_chip(data = data, plot_name = savefig, title_name = "Pulses for synchronization: Gain = 14 mv/fC, Peaking Time = 2 us, Buffer on", length = 1000)
            
        self.low_level.setExternalPulser(enable=False)
        self.low_level.femb_udp.write_reg(int(self.config["REGISTERS"]["REG_MUX_MODE"]), int(self.config["DEFINITIONS"]["MUX_GND_GND"]))
        self.low_level.femb_udp.write_reg(int(self.config["REGISTERS"]["REG_TAGGING"]), int(self.config["DEFINITIONS"]["TAGGING_OFF"]))
        
    def do_analysis(self, ):
        print("SYNCHRONIZATION - ANALYZE")
        
        self.results = self.params["chip_list"]
        print(self.results)
        for num, i in enumerate(len(self.results)):
            if (self.return_results[num] == True):
                self.results[i].append("PASS")
            elif (self.return_results[num] == False):
                self.results[i].append("FAIL")
            else:
                self.results[i].append("NOT TESTED (SPI ERROR)")
                
    def archiveResults(self):
        print("SYNCHRONIZATION - ARCHIVE")
        
        self.jsondict['boardID'] = self.params['boardid']
        self.jsondict['fw_ver'] = self.params['fw_ver']
        self.jsondict['test_category'] = self.params['test_category']
        self.jsondict['test_stand'] = self.params['test_stand']
        self.jsondict['chipver'] = self.params['chipver']
        self.jsondict['sw_version'] = self.params['sw_version']
        self.jsondict['fpgamezz'] = self.params['fpgamezz']
        self.jsondict['executable'] = self.params['executable']
        self.jsondict['datasubdir'] = self.params['datasubdir']
        self.jsondict['power_supply'] = self.params['power_supply']
        self.jsondict['femb_config'] = self.params['femb_config']
        self.jsondict['paramfile'] = self.params['paramfile']
        self.jsondict['outlabel'] = self.params['outlabel']
        
        self.jsondict['baseline'] = self.config["SYNC_SETTINGS"]["SYNC_BASELINE"]
        self.jsondict['buffer'] = self.config["SYNC_SETTINGS"]["SYNC_BUFFER"]
        self.jsondict['gain'] = self.config["SYNC_SETTINGS"]["SYNC_GAIN"]
        self.jsondict['peak'] = self.config["SYNC_SETTINGS"]["SYNC_PEAK"]
        self.jsondict['acdc'] = self.config["SYNC_SETTINGS"]["SYNC_ACDC"]
        self.jsondict['leak'] = self.config["SYNC_SETTINGS"]["SYNC_LEAK"]

        for chip in self.chip_list:
            #result, chip index, chip name, socket name
            jsonFile = os.path.join(self.datadir,chip[1],self.datasubdir,"results.json")
            index = chip[0]
            self.jsondict['chip_index'] = index
            self.jsondict['chip_name'] = chip[1]
            self.jsondict['result'] = self.results[index]
            self.jsondict['socket'] = self.params["socket{}id".format(index)]
            with open(jsonFile,'w') as outfile:
                json.dump(self.jsondict, outfile, indent=4)

def main():
    '''
    sync the ADCs
    '''
    sync_adcs = SYNC_ADCS()
    params = json.loads(open(sys.argv[1]).read())
    params["to_print"] = True
#    params["outputdir"] = True
    sync_adcs.params = params
    
#    for array in params["chip_list"]:
#        params["data_dir_chip{}".format(array[0])] = "{}/{}".format(sync_adcs.datadir, array[1])
#        print(params["data_dir_chip{}".format(array[0])])
#        
#    jsonFile = os.path.join(sync_adcs.datadir,"params.json")
#    with open(jsonFile,'w') as outfile:
#        json.dump(params, outfile, indent=4)
        
    sync_adcs.sync()
    sync_adcs.do_analysis()
    sync_adcs.archiveResults()
    return sync_adcs.results
    

if __name__ == '__main__':
    main()