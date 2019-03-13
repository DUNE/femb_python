"""
Module containes an example GUI. The main window configures the FEMB 
while trace_fft_window provides a second window with live trace and FFT.
"""

from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import
from builtins import int
from builtins import str
from builtins import hex
from future import standard_library
standard_library.install_aliases()
from datetime import timedelta, datetime
import tkinter as tk
from tkinter import messagebox
import json
import os                                 # for statv
import os.path
import subprocess
import git
import shutil
import time

#import the test module
#from femb_python.test_measurements.feAsicTest.doFembTest_simpleMeasurement import FEMB_TEST_SIMPLE
#from femb_python.test_measurements.feAsicTest.doFembTest_gainMeasurement import FEMB_TEST_GAIN
from femb_python.test_measurements.quad_FE_Board.trace_viewer import main_start as startWF
from femb_python.configuration import CONFIG
from femb_python.configuration.config_module_loader import getDefaultDirectory

from femb_python.configuration.config_base import FEMB_CONFIG_BASE
from femb_python.test_instrument_interface.rigol_dp832 import RigolDP832
from femb_python.test_measurements.quad_FE_Board.define_tests import main as maintest


class GUI_WINDOW(tk.Frame):

    #GUI window defined entirely in init function
    def __init__(self, master=None,forceQuick=False,forceLong=False):
        self.use_sumatra = True
        
        #Useful to have if we ever want to look back and see what version of femb_python we were using
        repo = git.Repo(__file__, search_parent_directories=True)
        self.sw_version = repo.head.object.hexsha

        #It's calling the constructor of the parent tkinter object, the pack method of the class, which is now a tkinter object
        tk.Frame.__init__(self,master)
        self.pack()
        self.config = CONFIG
        self.functions = FEMB_CONFIG_BASE(self.config)
        
        self.master.title("Quad FE ASIC Test GUI")
        self.master.protocol("WM_DELETE_WINDOW", lambda arg=self.master: self.on_closing(arg))
        self.WF_GUI = None
        self.analysis = "basic"

        #Variables that I want to save in the JSON but aren't included in the generic runner
        self.params = dict(
            test_category = "feasic_quad_cold",
            sw_version = self.sw_version,
            use_sumatra = self.use_sumatra
        )
        
        #Look in the root folder for the test name and see if there was a JSON file created with the previous settings
        #This is used to pre-fill in the fields, much more preferable than putting in the sockets and all that from scratch
        self.root_dir = getDefaultDirectory()
        file_name = os.path.join(self.root_dir,self.config["FILENAMES"]["DEFAULT_GUI_FILE_NAME"])
        if os.path.isfile(file_name):
            self.default_settings = dict()
            with open(file_name, 'r') as f:
                jsondata = json.load(f)
                for i in jsondata:
                    self.default_settings[i] = jsondata[i]
        else:
            self.default_settings = dict(
            operator_name = "",
            test_stand = "",
            test_stand_other = "",
            boardid = "",
            boardid_other = "",
            chipver = "",
            chipver_other = "",
            fpgamezz= "",
            fpgamezz_other = "",
            asic0id = "",
            asic1id = "",
            asic2id = "",
            asic3id = "",
            socket0id = "",
            socket1id = "",
            socket2id = "",
            socket3id = ""
        )
        
        #Define general commands column
        self.define_test_details_column()

        #Define general commands column
        self.define_general_commands_column()
        return
        
    #For GUI options where there are predefined but have the option for "other" (in case we're testing a new version of something)
    #Every time a change is made to those fields, this is called to see if "other" was chosen.  If it was, it creates a text field to manually write the value
    #If it's not, it hides that text field
    def gui_callback(self,*args,**kwargs):
        #TODO use dictionary map to get this quicker
        if (args[0] == "test_stand_GUI_variable"):
            index = 0
        elif (args[0] == "boardid_GUI_variable"):
            index = 1
        elif (args[0] == "chipver_GUI_variable"):
            index = 2
        elif (args[0] == "fpgamezz_GUI_variable"):
            index = 3
                
        if (self.selections[index].get() == "Other"):
                self.other_entries[index].grid(sticky=tk.W,row=index+2,column=2)
                self.others[index] = True
        else:
            self.other_entries[index].grid_forget()
            self.others[index] = False

    #For fields with predefined values, it gets those values from the config files
    #There's also a variable to tell if "other" was chosen, so it knows to look at the manual entry field for the value
    def define_test_details_column(self):
        columnbase=1
        entry_width=9
        options_width=5
        spinner_width=8
        label_width=15

        self.details_label = tk.Label(self, text="Tests Details")
        self.details_label.grid(row=0,column=columnbase, columnspan=3)

        # Adding operator name label and read entry box
        label = tk.Label(self,text="Operator Name:",width=label_width)
        label.grid(sticky=tk.W,row=1,column=columnbase+0)

        self.operator_entry = tk.Entry(self,width=entry_width)
        self.operator_entry.insert(tk.END, self.default_settings["operator_name"])
        self.operator_entry.grid(sticky=tk.W,row=1,column=columnbase+1)
        
        test_stand = ["Test Stand #:", "test_stand_GUI_variable", "test_stand", 'KNOWN_TEST_STANDS', self.default_settings["test_stand_other"]]
        board_id = ["Test Board ID:", "boardid_GUI_variable", "boardid", 'KNOWN_QUAD_BOARDS', self.default_settings["boardid_other"]]
        chip_ver = ["Chip Version:", "chipver_GUI_variable", "chipver", 'KNOWN_CHIP_VERSIONS', self.default_settings["chipver_other"]]
        fpgamezz = ["FPGA Board:", "fpgamezz_GUI_variable", "fpgamezz", 'KNOWN_FPGA_MEZZANINES', self.default_settings["fpgamezz_other"]]
        
        self.option_rows = [test_stand, board_id, chip_ver, fpgamezz]
        self.selections = []
        self.entries = []
        self.other_entries = []
        self.others = []
        
        for num, i in enumerate(self.option_rows):

            # Adding test stand ID and read entry box
            label = tk.Label(self,text=i[0],width=label_width)
            label.grid(sticky=tk.W,row=2+num,column=columnbase+0)
            
            selection = tk.StringVar(self.master, name = i[1])
            selection.set(self.default_settings[i[2]]) # initial value
            selection.trace("w", self.gui_callback)
            self.selections.append(selection)
            
            options = list(self.config._sections[i[3]].keys())
            possible_options = []
            for j in range(len(options)):
                possible_options.append(self.config[i[3]][options[j]])
                
            entry = tk.OptionMenu(self, selection, *possible_options)
            entry.config(width=options_width)
            self.entries.append(entry)
            entry.grid(sticky=tk.W,row=2+num,column=columnbase+1)
            
            entry_other = tk.Entry(self,width=entry_width)
            self.other_entries.append(entry_other)
            if (selection.get() == "Other"):
                entry_other.insert(tk.END, i[4])
                entry_other.grid(sticky=tk.W,row=2+num,column=2)
                other = True
            else:
                entry_other.grid_forget()
                other = False
            self.others.append(other)

        label = tk.Label(self,text="Chip ID:",width=entry_width)
        label.grid(sticky=tk.W,row=7,column=columnbase+1)
        
        label = tk.Label(self,text="Socket ID:",width=entry_width)
        label.grid(sticky=tk.W,row=7,column=columnbase+2)
        
        
        self.asic_entries = []
        self.socket_entries = []
        self.asic_enables = []
        for i, chip in enumerate(range(int(self.config["DEFAULT"]["NASIC_MIN"]), int(self.config["DEFAULT"]["NASIC_MAX"]) + 1, 1)):
            var = tk.BooleanVar(value=True)
            self.asic_enables.append(var)
            button = tk.Checkbutton(self, variable=var)
            button.grid(row=8+i,column=columnbase-1)
            
            
            label = tk.Label(self,text="ASIC {}".format(chip),width=label_width)
            label.grid(sticky=tk.W,row=8+i,column=columnbase+0)
        
            spinbox = tk.Spinbox(self, width=spinner_width, from_=self.config['GUI_SETTINGS']['CHIP_MIN'], to=self.config['GUI_SETTINGS']['CHIP_MAX'])
            self.asic_entries.append(spinbox)
            spinbox.insert(tk.END, self.default_settings["asic{}id".format(chip)])
            spinbox.delete(0)
            spinbox.grid(sticky=tk.W,row=8+i,column=columnbase+1)                  
        
            spinbox = tk.Spinbox(self, width=spinner_width, from_=self.config['GUI_SETTINGS']['SOCKET_MIN'], to=self.config['GUI_SETTINGS']['SOCKET_MAX'])
            self.socket_entries.append(spinbox)
            spinbox.insert(tk.END, self.default_settings["socket{}id".format(chip)])
            spinbox.delete(0)
            spinbox.grid(sticky=tk.W,row=8+i,column=columnbase+2)


    def define_general_commands_column(self):
        self.midcolumnbase=4

        self.status_label = tk.Label(self, text="FE ASIC TESTS", width = 20)
        self.status_label.grid(row=0,column=self.midcolumnbase, columnspan=50)
        
        
        #Set up buttons
        power_on = ["Power On", self.power_on, "green"]
        power_off = ["Power Off", self.power_off, "red"]
        test_connection = ["Test Connection", self.test_connection]
        debug = ["Debug Waveform", self.debug]
        start = ["Start Tests", self.start_measurements]
        
        buttons = [power_on, power_off, test_connection, debug, start]

        for num,i in enumerate(buttons):
            try:
                button_i = tk.Button(self, text = i[0], bg = i[2], command = i[1], width = 10)
            except IndexError:
                button_i = tk.Button(self, text = i[0], command = i[1], width = 10)
            button_i.grid(row = 1 + num, column = self.midcolumnbase)
            
        advanced = tk.Button(self, text = "Advanced", command = self.change_analysis_level)
        advanced.grid(row = 3, column = self.midcolumnbase+1)
        
        #Name as appears on GUI, basic or advanced, executible, and name of folder
        sync_test = ["Sync", "basic", "feasic_quad_sync", "Sync"]
        baseline_test = ["Baseline", "basic", "feasic_quad_baseline", "Baseline"]
        monitor_test = ["Monitor", "basic","feasic_quad_monitor", "Monitor"]
        alive_test = ["Alive", "basic", "feasic_quad_alive", "Alive"]
        dac_test = ["DAC", "advanced", "feasic_quad_dac", "Internal DAC"]
        gain_test = ["Pulse", "advanced", "feasic_quad_pulse", "Pulse"]
        ledge_test = ["Ledge", "advanced", "feasic_quad_ledge", "Ledge"]
        final_test = ["Final", "basic"]
        self.all_tests = [sync_test, baseline_test, monitor_test, alive_test, dac_test, gain_test, ledge_test, final_test]
        for num, i in enumerate(self.all_tests):
            label = tk.Label(self, text = i[0], width = 10)
            i.append(label)
            
            var = tk.BooleanVar(value=True)
            i.append(var)
            button = tk.Checkbutton(self, variable=var)
            i.append(button)
            if (i[1] == "basic"):
                label.grid(sticky=tk.W, row = 7, column = self.midcolumnbase+num+1)
                if (i[0]!="Final" and i[0]!="Sync"):
                    button.grid(row=6,column=self.midcolumnbase+num+1)
                    
        self.connected_power_supply = ["Connected Power Supply"]
        self.temperature_cold = ["Cold Test"]
        self.online_analysis = ["Concurrent Analysis"]
        self.advanced_options = [self.connected_power_supply, self.temperature_cold, self.online_analysis]
        for i in self.advanced_options:
            label = tk.Label(self, text = i[0], width = 20, anchor="w")
            i.append(label)
            var = tk.BooleanVar(value=True)
            i.append(var)
            button = tk.Checkbutton(self, variable=var)
            i.append(button)
                
        self.results_array = []
        for num, i in enumerate(self.all_tests):
            test_specific = []
            for chips in range(int(self.config["DEFAULT"]["NASIC_MIN"]), int(self.config["DEFAULT"]["NASIC_MAX"]) + 1, 1):
                label = tk.Label(self, text="----", width=10)
                if (i[1] == "basic"):
                    label.grid(stick=tk.W, row = 8 + chips, column = self.midcolumnbase+num+1)
                test_specific.append(label)
                
            self.results_array.append(test_specific)
        
        #Set up static labels
        for num, chips in enumerate(range(int(self.config["DEFAULT"]["NASIC_MIN"]), int(self.config["DEFAULT"]["NASIC_MAX"]) + 1, 1)):
            label = tk.Label(self, text="ASIC {} Results:".format(chips), width=15)
            label.grid(sticky=tk.W,row=8+num,column=self.midcolumnbase+0)

        
    def write_default_file(self):
        self.params['operator_name'] = self.operator_entry.get()
        for num, i in enumerate(self.option_rows):
            using_other = self.others[num]
            if (using_other == True):
                self.params[i[2]] = self.other_entries[num].get()
            else:
                self.params[i[2]] = self.selections[num].get()
                
        #Create that default file
        self.defaultjson = dict(
            operator_name = self.operator_entry.get(),
            test_stand = self.selections[0].get(),
            test_stand_other = self.other_entries[0].get(),
            boardid = self.selections[1].get(),
            boardid_other = self.other_entries[1].get(),
            chipver = self.selections[2].get(),
            chipver_other = self.other_entries[2].get(),
            fpgamezz = self.selections[3].get(),
            fpgamezz_other = self.other_entries[3].get()
        )
        
        for i, chip in enumerate(range(int(self.config["DEFAULT"]["NASIC_MIN"]), int(self.config["DEFAULT"]["NASIC_MAX"]) + 1, 1)):
            self.params['asic{}id'.format(chip)] = self.asic_entries[i].get()
            self.params['socket{}id'.format(chip)] = self.socket_entries[i].get()
            self.defaultjson['asic{}id'.format(chip)] = self.asic_entries[i].get()
            self.defaultjson['socket{}id'.format(chip)] = self.socket_entries[i].get()
        
        jsonFile = os.path.join(self.root_dir,self.config["FILENAMES"]["DEFAULT_GUI_FILE_NAME"])
        with open(jsonFile,'w') as outfile:
            json.dump(self.defaultjson, outfile, indent=4)
            
    def start_measurements(self):
        self.write_default_file()
        
        #Make sure everything was entered ok, that nothing was screwed up
        gui_check = self.config["GUI_SETTINGS"]
        asic_tup = []
        sock_tup = []
        for i, chip in enumerate(range(int(self.config["DEFAULT"]["NASIC_MIN"]), int(self.config["DEFAULT"]["NASIC_MAX"]) + 1, 1)):
            asic_tup.append("asic{}id".format(chip))
            sock_tup.append("socket{}id".format(chip))
                
        for i in asic_tup:
            j = self.params[i]
            if ((int(j) < int(gui_check['CHIP_MIN'])) or (int(j) > int(gui_check['CHIP_MAX']))):
                print("{}({}) is out of range ({} to {})!".format(i, j, int(gui_check['CHIP_MIN']), int(gui_check['CHIP_MAX'])))
                self.status_label["text"] = "ENTER REQUIRED INFO"
                self.update_idletasks()
                return
                
        for i in sock_tup:
            j = self.params[i]
            if ((int(j) < int(gui_check['SOCKET_MIN'])) or (int(j) > int(gui_check['SOCKET_MAX']))):
                print("{}({}) is out of range ({} to {})!".format(i, j, int(gui_check['SOCKET_MIN']), int(gui_check['SOCKET_MAX'])))
                self.status_label["text"] = "ENTER REQUIRED INFO"
                self.update_idletasks()
                return
            
        if not (self.params['operator_name'] and self.params['test_stand'] and self.params['boardid'] and self.params['fpgamezz'] and self.params['chipver']):
            print("ENTER REQUIRED INFO")
            self.status_label["text"] = "ENTER REQUIRED INFO"
            self.update_idletasks()
            return
            
        self.power_on()
        fw_ver = self.functions.get_fw_version()
        self.params['fw_ver'] = hex(fw_ver)
        
        if (fw_ver < int(self.config["DEFAULT"]["LATEST_FW"], 16)):
            messagebox.showinfo("Warning!", "The FPGA is running firmware version {} when the latest firmware is version {}.  Please let an expert know!".format(hex(fw_ver), hex(int(self.config["DEFAULT"]["LATEST_FW"], 16))))
            
        self.functions.turnOnAsics()
        self.functions.resetBoard()
        self.functions.turnOnAsics()
        
        responding_chips = self.functions.initBoard()
        self.chiplist = []
        working_chips = []
        for i, chip in enumerate(range(int(self.config["DEFAULT"]["NASIC_MIN"]), int(self.config["DEFAULT"]["NASIC_MAX"]) + 1, 1)):
            tup = [i, self.params["asic{}id".format(chip)]]
            self.chiplist.append(tup)
            if (self.asic_enables[i].get() == True):
                if chip in (responding_chips):
                    working_chips.append(chip)
                    
        self.params['working_chips'] = working_chips
        print ("Working chips are {}".format(working_chips))
        print ("Because enabled chips are {}".format(self.asic_enables))
        
        tests_to_do = []
        for i in self.all_tests:
            if (i[0]!="Final"):
                if ((i[1] == "basic") and (i[5].get() == True)):
                    tests_to_do.append([i[2],i[3]])
                    
                elif (self.analysis == "advanced" and i[1] == "advanced" and i[5].get() == True):
                    tests_to_do.append([i[2],i[3]])
                
        self.params['tests_to_do'] = tests_to_do

        start_time = time.time()
        self.now = time.strftime("%Y%m%dT%H%M%S", time.localtime(time.time()))
        
        print("BEGIN TESTS")
        self.params.update(chip_list = self.chiplist)
        self.update_idletasks()
        
        #Calls the new generic tester/runner.  Note that this is done in a for loop and the generic tester passes values back by using "Yield"
        #This is the only way I figured out how to get feedback back to the GUI mid-test without changing too much
        for i in (maintest(**self.params)):
            self.postResults(i)
            self.update_idletasks()

        end_time = time.time()
        self.status_label = "DONE " 
        self.update_idletasks()
        response = CustomDialog(self).show()
        
        for i in self.working_chips:
            chip_name = self.chip_list[i][1]
            results_file = os.path.join(self.datadir, chip_name, "results.json")
            with open(results_file,'r') as f:
                results = json.load(f)
                
            ver = {'verified':response[i]}
            
            with open(results_file,'w') as outfile:
                results.update(ver)
                json.dump(results, outfile, indent=4)
                
        
        
        run_time = end_time-start_time
        print("Total run time: {}".format(int(run_time)))
        #TODO turn off chips power
        print(self.GetTimeString(int(run_time)))

    def change_analysis_level(self):
        if (self.analysis == "basic"):
            self.analysis = "advanced"
            for num, i in enumerate(self.all_tests):
                if (i[1] == "advanced"):
                    label = i[4]
                    label.grid(sticky=tk.W, row = 7, column = self.midcolumnbase+num+1)
                    button = i[6]
                    button.grid(row=6,column=self.midcolumnbase+num+1)

                    for chips in range(int(self.config["DEFAULT"]["NASIC_MIN"]), int(self.config["DEFAULT"]["NASIC_MAX"]) + 1, 1):
                        label = self.results_array[num][chips]
                        label.grid(stick=tk.W, row = 8 + chips, column = self.midcolumnbase+num+1)
                        
            for num, i in enumerate(self.advanced_options):
                button = i[3]
                button.grid(row = 1 + num, column = self.midcolumnbase + 2)
                label= i[1]
                label.grid(row = 1 + num, column = self.midcolumnbase + 3, columnspan = 3)
                        
            
                
        elif (self.analysis == "advanced"):
            self.analysis = "basic"
            for num, i in enumerate(self.all_tests):
                if (i[1] == "advanced"):
                    label = i[4]
                    label.grid_forget()
                    button = i[6]
                    button.grid_forget()
                    
                    for chips in range(int(self.config["DEFAULT"]["NASIC_MIN"]), int(self.config["DEFAULT"]["NASIC_MAX"]) + 1, 1):
                        label = self.results_array[num][chips]
                        label.grid_forget()
                        
                for num, i in enumerate(self.advanced_options):
                    button = i[3]
                    button.grid_forget()
                    label = i[1]
                    label.grid_forget()
        else:
            print("GUI_ERROR --> Analysis level should only ever be 'basic' or 'advanced', it was {}".format(self.analysis))
            
    def power_on(self):
        self.on_child_closing()
        self.PowerSupply = RigolDP832()
        if (self.PowerSupply.powerSupplyDevice != None):
            self.using_power_supply = True
            self.params['power_supply'] = True
        else:
            self.using_power_supply = False
            self.params['power_supply'] = False
            messagebox.showinfo("Warning!", "No power supply device was detected!  Plug in the power supply and try again!  " +
                                "If you want to run the test without the power suply connected, make sure to turn the power " +
                                "on when testing at room temperature, off while cooling down, and on again when doing the cold test.")
                                
        if (self.using_power_supply):
    #        TODO check if channels are already on or not
            pwr = self.config["POWER_SUPPLY"]
            self.PowerSupply.set_channel(channel = pwr["PS_HEATING_CHN"], voltage = float(pwr["PS_HEATING_V"]), v_limit = float(pwr["PS_HEATING_V_LIMIT"]),
                                         c_limit = float(pwr["PS_HEATING_I_LIMIT"]), vp = pwr["PS_HEATING_V_PROTECTION"], cp = pwr["PS_HEATING_I_PROTECTION"])
            self.PowerSupply.set_channel(channel = pwr["PS_QUAD_CHN"], voltage = float(pwr["PS_QUAD_V"]), v_limit = float(pwr["PS_QUAD_V_LIMIT"]),
                                         c_limit = float(pwr["PS_QUAD_I_LIMIT"]), vp = pwr["PS_QUAD_V_PROTECTION"], cp = pwr["PS_QUAD_I_PROTECTION"])
            self.PowerSupply.set_channel(channel = pwr["PS_FPGA_CHN"], voltage = float(pwr["PS_FPGA_V"]), v_limit = float(pwr["PS_FPGA_V_LIMIT"]),
                                         c_limit = float(pwr["PS_FPGA_I_LIMIT"]), vp = pwr["PS_FPGA_V_PROTECTION"], cp = pwr["PS_FPGA_I_PROTECTION"])
            self.PowerSupply.on(channels = [1,2,3])
            results = self.PowerSupply.measure_params(channel = 1)
            print(results)
            results = self.PowerSupply.measure_params(channel = 2)
            print(results)
            results = self.PowerSupply.measure_params(channel = 3)
            print(results)
    #       Measure initial volatage and current
            self.PowerSupply.powerSupplyDevice.write(":MEAS:VOLT?")
            initialVoltage = float(self.PowerSupply.powerSupplyDevice.read().strip().decode())
            self.PowerSupply.powerSupplyDevice.write(":MEAS:CURR?")
            initialCurrent = float(self.PowerSupply.powerSupplyDevice.read().lstrip().decode())
            print(initialVoltage)
            print(initialCurrent)
            
        self.update_idletasks()
        time.sleep(5)
#        self.power_button["bg"]="green"
        
    def power_off(self):
        self.on_child_closing()
        self.PowerSupply = RigolDP832()
        if (self.PowerSupply.powerSupplyDevice != None):
            self.using_power_supply = True
            self.params['power_supply'] = True
        else:
            self.using_power_supply = False
            self.params['power_supply'] = False
            messagebox.showinfo("Warning!", "No power supply device was detected!  Plug in the power supply and try again!  " +
                                "If you want to run the test without the power suply connected, make sure to turn the power " +
                                "on when testing at room temperature, off while cooling down, and on again when doing the cold test.")
                                
        if (self.using_power_supply):
            self.PowerSupply.off()
        self.update_idletasks()
#        self.power_button["bg"]="green"
        
    def test_connection(self):
        #TODO if not on already, turn on and wait
        self.on_child_closing()
        self.write_default_file()
        self.power_on()
        fw_ver = self.functions.get_fw_version()
        self.params['fw_ver'] = hex(fw_ver)
        
        if (fw_ver < int(self.config["DEFAULT"]["LATEST_FW"], 16)):
            messagebox.showinfo("Warning!", "The FPGA is running firmware version {} when the latest firmware is version {}.  Please let an expert know!".format(hex(fw_ver), hex(int(self.config["DEFAULT"]["LATEST_FW"], 16))))
            
        self.functions.turnOnAsics()
        self.functions.resetBoard()
        SPI_response = self.functions.initBoard()
                
        temp_sync_folder = os.path.join(self.root_dir,"temp_sync_files")
        if not os.path.exists(temp_sync_folder):
            os.makedirs(temp_sync_folder)
            
        for thing in os.listdir(temp_sync_folder):
            file_path = os.path.join(temp_sync_folder, thing)
            try:
                if (os.path.isfile(file_path)):
                    os.unlink(file_path)
                if (os.path.isdir(file_path)):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(e)
                
        chiplist = []
        for i, chip in enumerate(range(int(self.config["DEFAULT"]["NASIC_MIN"]), int(self.config["DEFAULT"]["NASIC_MAX"]) + 1, 1)):
            tup = [i, self.params["asic{}id".format(chip)]]
            chiplist.append(tup)
        
        self.functions.syncADC(datadir = temp_sync_folder, working_chips = SPI_response, chip_list = chiplist, to_print = True)
        
        self.WF_GUI = tk.Tk()
        self.WF_GUI.protocol("WM_DELETE_WINDOW", self.on_child_closing)
        startWF(self.WF_GUI)
        
    def debug(self):
        self.WF_GUI = tk.Tk()
        self.WF_GUI.protocol("WM_DELETE_WINDOW", self.on_child_closing)
        startWF(self.WF_GUI)

    def postResults(self, params):
        self.datadir = params['datadir']
        self.working_chips = params['working_chips']
        self.chip_list = params['chip_list']
        print("CHECKING CHIPS")
        for i in self.working_chips:
            chip_name = self.chip_list[i][1]
            results_path = os.path.join(self.datadir, chip_name)
            jsonFile = os.path.join(results_path, self.config["FILENAMES"]["RESULTS"])
            #Now that we know what the timestamped directory is, we can have a button on the GUI open it directly
            self.details_label.bind("<Button-1>",lambda event, arg=self.datadir: self.open_directory(arg))
            
            with open(jsonFile,'r') as f:
                test_list = json.load(f)
                
            if "sync_outlabel" in test_list:
                outlabel = test_list["sync_outlabel"]
                jsonFile = os.path.join(results_path, outlabel, self.config["FILENAMES"]["RESULTS"])
                with open(jsonFile,'r') as f:
                    results = json.load(f)
                label = self.results_array[0][i]
                result = results['sync_result']
                self.update_label(label, result)
                linked_folder = os.path.join(results_path, outlabel)
                linked_file1 = self.config["FILENAMES"]["SYNC_LINK"]
                linked_file2 = self.config["FILENAMES"]["SYNC_LINK_MONITOR"]
                linked_file_path1 = os.path.join(linked_folder, linked_file1)
                linked_file_path2 = os.path.join(linked_folder, linked_file2)
                label.bind("<Button-1>",lambda event, arg=linked_file_path1: self.link_label(arg))
                label.bind("<Button-3>",lambda event, arg=linked_file_path2: self.link_label(arg))
                
            if "baseline_outlabel" in test_list:
                outlabel = test_list["baseline_outlabel"]
                jsonFile = os.path.join(results_path, outlabel, self.config["FILENAMES"]["RESULTS"])
                with open(jsonFile,'r') as f:
                    results = json.load(f)
                label = self.results_array[1][i]
                result = results['baseline_result']
                self.update_label(label, result)
                linked_folder = os.path.join(results_path, outlabel)
                linked_file = self.config["FILENAMES"]["BASELINE_LINK"].format(chip_name)
                linked_file_path = os.path.join(linked_folder, linked_file)
                label.bind("<Button-1>",lambda event, arg=linked_file_path: self.link_label(arg))
                
            if "monitor_outlabel" in test_list:
                outlabel = test_list["monitor_outlabel"]
                jsonFile = os.path.join(results_path, outlabel, self.config["FILENAMES"]["RESULTS"])
                with open(jsonFile,'r') as f:
                    results = json.load(f)
                label = self.results_array[2][i]
                result = results['monitor_result']
                self.update_label(label, result)
                linked_folder = os.path.join(results_path, outlabel)
                linked_file = self.config["FILENAMES"]["MONITOR_LINK"].format(chip_name)
                linked_file_path = os.path.join(linked_folder, linked_file)
                label.bind("<Button-1>",lambda event, arg=linked_file_path: self.link_label(arg))
                
            if "alive_outlabel" in test_list:
                outlabel = test_list["alive_outlabel"]
                jsonFile = os.path.join(results_path, outlabel, self.config["FILENAMES"]["RESULTS"])
                with open(jsonFile,'r') as f:
                    results = json.load(f)
                label = self.results_array[3][i]
                result = results['alive_result']
                self.update_label(label, result)
                linked_folder = os.path.join(results_path, outlabel)
                linked_file = self.config["FILENAMES"]["ALIVE_LINK"].format(chip_name)
                linked_file_path = os.path.join(linked_folder, linked_file)
                label.bind("<Button-1>",lambda event, arg=linked_file_path: self.link_label(arg))
                    
    def update_label(self, label, result):
        if (result == "PASS"):
            label["text"] = "Pass"
            label["fg"] = "green"
        elif (result == "FAIL"):
            label["text"] = "Fail"
            label["fg"] = "red"
        else:
            print("Top_Level_GUI--> Incorrect result, must 'PASS' or 'FAIL', was {}".format(result))
            
    def link_label(self, file):
        #eog is so it opens in the superior Image Viewer without all the junk in Image Magick
        subprocess.check_call(["eog", file])
        
    def open_directory(self, directory):
        #xdg-open is so it opens the directory as is
        subprocess.check_call(["xdg-open", directory])
    
    # Can add additional testing sequences like as above with a method name
    # like "do_<semantic_label>".
    def GetTimeString(self, t):
        sec = timedelta(seconds=t)
        d = datetime(1,1,1) + sec    
        time_str = "{}:{}:{}".format(d.hour, d.minute, d.second)
        return time_str
        
    def on_closing(self, window):
        self.on_child_closing()
        window.destroy()
        window.quit()
        
    def on_child_closing(self):
        if (self.WF_GUI != None):
            self.WF_GUI.destroy()
            #self.WF_GUI.quit()
            self.WF_GUI = None
            
class CustomDialog(tk.Toplevel):
    def __init__(self, parent):
        tk.Toplevel.__init__(self, parent)
        self.config = CONFIG
        
        self.labels = []
        self.entries = []
        self.values= []
        for i, chip in enumerate(range(int(self.config["DEFAULT"]["NASIC_MIN"]), int(self.config["DEFAULT"]["NASIC_MAX"]) + 1, 1)):
            label = tk.Label(self, text="Chip {}".format(chip))
            self.labels.append(label)
            label.grid(row=0,column=i)
            var = tk.BooleanVar(value=True)
            self.values.append(var)
            button = tk.Checkbutton(self, text="Genuine Test?", variable=var)
            self.entries.append(button)
            button.grid(row=1,column=i)
            
        self.ok_button = tk.Button(self, text="OK", command=self.on_ok)
        self.ok_button.grid(row=2,column=0)

    def on_ok(self, event=None):
        self.destroy()

    def show(self):
        self.wm_deiconify()
        self.focus_force()
        self.wait_window()
        response = []
        for i in range(len(self.entries)):
            response.append(self.values[i].get())
        return response

def main():
    root = tk.Tk()
    GUI_WINDOW(root)
    root.mainloop() 
    
if __name__ == '__main__':
    main()
