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
from time import sleep, time
from datetime import timedelta, datetime
import tkinter as tk
from tkinter import messagebox
import json
from threading import Thread

import sys
import os                                 # for statv
import os.path
import time
import git
import shutil
#import sys

#import the test module
#from femb_python.test_measurements.feAsicTest.doFembTest_simpleMeasurement import FEMB_TEST_SIMPLE
#from femb_python.test_measurements.feAsicTest.doFembTest_gainMeasurement import FEMB_TEST_GAIN
from femb_python.test_measurements.quad_FE_Board.trace_viewer import main_start as startWF
from femb_python.configuration import CONFIG
from femb_python.configuration.config_module_loader import getDefaultDirectory

from femb_python.configuration.config_base import FEMB_CONFIG_BASE
from femb_python.test_instrument_interface.rigol_dp832 import RigolDP832
from femb_python.test_measurements.OscillatorTesting.code.driverUSBTMC import DriverUSBTMC
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
            boardid = "",
            chipver = "",
            fpgamezz= "",
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
        if (args[0] == "test_stand_GUI_variable"):
            if (self.test_stand_selection.get() == "Other"):
                self.test_stand_entry_other.grid(sticky=tk.W,row=2,column=2)
                self.test_stand_other = True
            else:
                self.test_stand_entry_other.grid_forget()
                self.test_stand_other = False
                
        elif (args[0] == "boardid_GUI_variable"):
            if (self.boardid_selection.get() == "Other"):
                self.boardid_entry_other.grid(sticky=tk.W,row=3,column=2)
                self.boardid_other = True
            else:
                self.boardid_entry_other.grid_forget()
                self.boardid_other = False
                
        elif (args[0] == "chipver_GUI_variable"):
            if (self.chipver_selection.get() == "Other"):
                self.chipver_entry_other.grid(sticky=tk.W,row=4,column=2)
                self.chipver_other = True
            else:
                self.chipver_entry_other.grid_forget()
                self.chipver_other = False
                
        elif (args[0] == "fpgamezz_GUI_variable"):
            if (self.fpgamezz_selection.get() == "Other"):
                self.fpgamezz_entry_other.grid(sticky=tk.W,row=5,column=2)
                self.fpgamezz_other = True
            else:
                self.fpgamezz_entry_other.grid_forget()
                self.fpgamezz_other = False

    #For fields with predefined values, it gets those values from the config files
    #There's also a variable to tell if "other" was chosen, so it knows to look at the manual entry field for the value
    def define_test_details_column(self):
        columnbase=0
        entry_width=9
        options_width=5
        spinner_width=8
        label_width=15

        label = tk.Label(self, text="Tests Details")
        label.grid(row=0,column=columnbase, columnspan=50)

        # Adding operator name label and read entry box
        label = tk.Label(self,text="Operator Name:",width=label_width)
        label.grid(sticky=tk.W,row=1,column=columnbase+0)

        self.operator_entry = tk.Entry(self,width=entry_width)
        self.operator_entry.insert(tk.END, self.default_settings["operator_name"])
        self.operator_entry.grid(sticky=tk.W,row=1,column=columnbase+1)

        # Adding test stand ID and read entry box
        label = tk.Label(self,text="Test Stand #:",width=label_width)
        label.grid(sticky=tk.W,row=2,column=columnbase+0)
        
        self.test_stand_selection = tk.StringVar(self.master, name = "test_stand_GUI_variable")
        self.test_stand_selection.set(self.default_settings["test_stand"]) # initial value
        self.test_stand_selection.trace("w", self.gui_callback)
        
        options = list(self.config._sections['KNOWN_TEST_STANDS'].keys())
        stands = []
        for i in range(len(options)):
            stands.append(self.config['KNOWN_TEST_STANDS'][options[i]])
            
        self.test_stand_entry = tk.OptionMenu(self, self.test_stand_selection, *stands)
        self.test_stand_entry.config(width=options_width)
        self.test_stand_entry.grid(sticky=tk.W,row=2,column=columnbase+1)
        self.test_stand_entry_other = tk.Entry(self,width=entry_width)
        if (self.test_stand_selection.get() == "Other"):
            self.test_stand_entry_other.insert(tk.END, self.default_settings["test_stand_other"])
            self.test_stand_entry_other.grid(sticky=tk.W,row=2,column=2)
            self.test_stand_other = True
        else:
            self.test_stand_entry_other.grid_forget()
            self.test_stand_other = False

        # Adding electronics ID and read entry box
        label = tk.Label(self,text="Test Board ID:",width=label_width)
        label.grid(sticky=tk.W,row=3,column=columnbase+0)

        self.boardid_selection = tk.StringVar(self.master, name = "boardid_GUI_variable")
        self.boardid_selection.set(self.default_settings["boardid"]) # initial value
        self.boardid_selection.trace("w", self.gui_callback)
        
        options = list(self.config._sections['KNOWN_QUAD_BOARDS'].keys())
        boards = []
        for i in range(len(options)):
            boards.append(self.config['KNOWN_QUAD_BOARDS'][options[i]])
            
        self.boardid_entry = tk.OptionMenu(self, self.boardid_selection, *boards)
        self.boardid_entry.config(width=options_width)
        self.boardid_entry.grid(sticky=tk.W,row=3,column=columnbase+1)
        self.boardid_entry_other = tk.Entry(self,width=entry_width)
        if (self.boardid_selection.get() == "Other"):
            self.boardid_entry_other.insert(tk.END, self.default_settings["boardid_other"])
            self.boardid_entry_other.grid(sticky=tk.W,row=3,column=2)
            self.boardid_other = True
        else:
            self.boardid_entry_other.grid_forget()
            self.boardid_other = False

        # Adding version number and read entry box
        label = tk.Label(self,text="Chip Version:",width=label_width)
        label.grid(sticky=tk.W,row=4,column=columnbase+0)

        self.chipver_selection = tk.StringVar(self.master, name = "chipver_GUI_variable")
        self.chipver_selection.set(self.default_settings["chipver"]) # initial value
        self.chipver_selection.trace("w", self.gui_callback)
        
        options = list(self.config._sections['KNOWN_CHIP_VERSIONS'].keys())
        chips = []
        for i in range(len(options)):
            chips.append(self.config['KNOWN_CHIP_VERSIONS'][options[i]])
            
        self.chipver_entry = tk.OptionMenu(self, self.chipver_selection, *chips)
        self.chipver_entry.config(width=options_width)
        self.chipver_entry.grid(sticky=tk.W,row=4,column=columnbase+1)
        self.chipver_entry_other = tk.Entry(self,width=entry_width)
        if (self.chipver_selection.get() == "Other"):
            self.chipver_entry_other.insert(tk.END, self.default_settings["chipver_other"])
            self.chipver_entry_other.grid(sticky=tk.W,row=4,column=2)
            self.chipver_other = True
        else:
            self.chipver_entry_other.grid_forget()
            self.chipver_other = False
            
        # Adding FPGA board number and read entry box
        label = tk.Label(self,text="FPGA Board:",width=label_width)
        label.grid(sticky=tk.W,row=5,column=columnbase+0)

        self.fpgamezz_selection = tk.StringVar(self.master, name = "fpgamezz_GUI_variable")
        self.fpgamezz_selection.set(self.default_settings["fpgamezz"]) # initial value
        self.fpgamezz_selection.trace("w", self.gui_callback)
        
        options = list(self.config._sections['KNOWN_FPGA_MEZZANINES'].keys())
        fpgas = []
        for i in range(len(options)):
            fpgas.append(self.config['KNOWN_FPGA_MEZZANINES'][options[i]])
            
        self.fpgamezz_entry = tk.OptionMenu(self, self.fpgamezz_selection, *fpgas)
        self.fpgamezz_entry.config(width=options_width)
        self.fpgamezz_entry.grid(sticky=tk.W,row=5,column=columnbase+1)
        self.fpgamezz_entry_other = tk.Entry(self,width=entry_width)
        if (self.fpgamezz_selection.get() == "Other"):
            self.fpgamezz_entry_other.insert(tk.END, self.default_settings["fpgamezz_other"])
            self.fpgamezz_entry_other.grid(sticky=tk.W,row=5,column=2)
            self.fpgamezz_other = True
        else:
            self.fpgamezz_entry_other.grid_forget()
            self.fpgamezz_other = False

        label = tk.Label(self,text="ASIC 0",width=label_width)
        label.grid(sticky=tk.W,row=8,column=columnbase+0)
        
        label = tk.Label(self,text="ASIC 1",width=label_width)
        label.grid(sticky=tk.W,row=9,column=columnbase+0)
        
        label = tk.Label(self,text="ASIC 2",width=label_width)
        label.grid(sticky=tk.W,row=10,column=columnbase+0)
        
        label = tk.Label(self,text="ASIC 3",width=label_width)
        label.grid(sticky=tk.W,row=11,column=columnbase+0)
        
        label = tk.Label(self,text="Chip ID:",width=entry_width)
        label.grid(sticky=tk.W,row=7,column=columnbase+1)
        
        label = tk.Label(self,text="Socket ID:",width=entry_width)
        label.grid(sticky=tk.W,row=7,column=columnbase+2)
        
        # ASIC 0 ID

        self.asic0_entry = tk.Spinbox(self, width=spinner_width, from_=self.config['GUI_SETTINGS']['CHIP_MIN'], to=self.config['GUI_SETTINGS']['CHIP_MAX'])
        self.asic0_entry.insert(tk.END, self.default_settings["asic0id"])
        self.asic0_entry.delete(0)
        self.asic0_entry.grid(sticky=tk.W,row=8,column=columnbase+1)

        # ASIC 1 ID

        self.asic1_entry = tk.Spinbox(self, width=spinner_width, from_=self.config['GUI_SETTINGS']['CHIP_MIN'], to=self.config['GUI_SETTINGS']['CHIP_MAX'])
        self.asic1_entry.insert(tk.END, self.default_settings["asic1id"])
        self.asic1_entry.delete(0)
        self.asic1_entry.grid(sticky=tk.W,row=9,column=columnbase+1)

        # ASIC 2 ID

        self.asic2_entry = tk.Spinbox(self, width=spinner_width, from_=self.config['GUI_SETTINGS']['CHIP_MIN'], to=self.config['GUI_SETTINGS']['CHIP_MAX'])
        self.asic2_entry.insert(tk.END, self.default_settings["asic2id"])
        self.asic2_entry.delete(0)
        self.asic2_entry.grid(sticky=tk.W,row=10,column=columnbase+1)

        # ASIC 3 ID
        self.asic3_entry = tk.Spinbox(self, width=spinner_width, from_=self.config['GUI_SETTINGS']['CHIP_MIN'], to=self.config['GUI_SETTINGS']['CHIP_MAX'])
        self.asic3_entry.insert(tk.END, self.default_settings["asic3id"])
        self.asic3_entry.delete(0)
        self.asic3_entry.grid(sticky=tk.W,row=11,column=columnbase+1)                      
        
        # SOCKET 0 ID

        self.socket0_entry = tk.Spinbox(self, width=spinner_width, from_=self.config['GUI_SETTINGS']['SOCKET_MIN'], to=self.config['GUI_SETTINGS']['SOCKET_MAX'])
        self.socket0_entry.insert(tk.END, self.default_settings["socket0id"])
        self.socket0_entry.delete(0)
        self.socket0_entry.grid(sticky=tk.W,row=8,column=columnbase+2)

        # SOCKET 1 ID

        self.socket1_entry = tk.Spinbox(self, width=spinner_width, from_=self.config['GUI_SETTINGS']['SOCKET_MIN'], to=self.config['GUI_SETTINGS']['SOCKET_MAX'])
        self.socket1_entry.insert(tk.END, self.default_settings["socket1id"])
        self.socket1_entry.delete(0)
        self.socket1_entry.grid(sticky=tk.W,row=9,column=columnbase+2)

        # SOCKET 2 ID

        self.socket2_entry = tk.Spinbox(self, width=spinner_width, from_=self.config['GUI_SETTINGS']['SOCKET_MIN'], to=self.config['GUI_SETTINGS']['SOCKET_MAX'])
        self.socket2_entry.insert(tk.END, self.default_settings["socket2id"])
        self.socket2_entry.delete(0)
        self.socket2_entry.grid(sticky=tk.W,row=10,column=columnbase+2)

        # SOCKET 3 ID

        self.socket3_entry = tk.Spinbox(self, width=spinner_width, from_=self.config['GUI_SETTINGS']['SOCKET_MIN'], to=self.config['GUI_SETTINGS']['SOCKET_MAX'])
        self.socket3_entry.insert(tk.END, self.default_settings["socket3id"])
        self.socket3_entry.delete(0)
        self.socket3_entry.grid(sticky=tk.W,row=11,column=columnbase+2) 


    def define_general_commands_column(self):
        columnbase=50

        label = tk.Label(self, text="FE ASIC TESTS")
        label.grid(row=0,column=columnbase, columnspan=50)

        self.power_button = tk.Button(self, text="Power On", bg="green", command=self.power_on,width=10)
        self.power_button.grid(row=1,column=columnbase,columnspan=1)
        
        self.power_button = tk.Button(self, text="Power Off", bg="red", command=self.power_off,width=10)
        self.power_button.grid(row=1,column=columnbase+1,columnspan=1)
        
        self.connection_button = tk.Button(self, text="Test Connection", command=self.test_connection,width=10)
        self.connection_button.grid(row=2,column=columnbase+1,columnspan=1)
        
        self.debug_button = tk.Button(self, text="Debug Waveform", command=self.debug,width=10)
        self.debug_button.grid(row=2,column=columnbase+3,columnspan=1)
        
        self.start_button = tk.Button(self, text="Start Tests", command=self.start_measurements,width=10)
        self.start_button.grid(row=2,column=columnbase,columnspan=1)

        self.status_label = tk.Label(self, text="NOT STARTED",width=10)
        self.status_label.grid(sticky=tk.W,row=3,column=columnbase,columnspan=1)
        
        self.baseline_result_label = tk.Label(self, text="BASELINE", width=10)
        self.baseline_result_label.grid(sticky=tk.W, row=7, column=columnbase+1)        
        self.monitor_result_label = tk.Label(self, text="MONITOR", width=10)
        self.monitor_result_label.grid(sticky=tk.W, row=7, column=columnbase+2)        
        self.alive_result_label = tk.Label(self, text="ALIVE", width=10)
        self.alive_result_label.grid(sticky=tk.W, row=7, column=columnbase+3)
        self.final_result_label = tk.Label(self, text="FINAL", width=10)
        self.final_result_label.grid(sticky=tk.W, row=7, column=columnbase+4)
        
        self.asic0_result = tk.Label(self, text="ASIC 0 Results:", width=15)
        self.asic0_result.grid(sticky=tk.W,row=8,column=columnbase+0)        
        self.asic0_baseline_result = tk.Label(self, text="TBD", width=10)
        self.asic0_baseline_result.grid(sticky=tk.W, row=8, column=columnbase+1)        
        self.asic0_monitor_result = tk.Label(self, text="TBD", width=10)
        self.asic0_monitor_result.grid(sticky=tk.W, row=8, column=columnbase+2)        
        self.asic0_alive_result = tk.Label(self, text="TBD", width=10)
        self.asic0_alive_result.grid(sticky=tk.W, row=8, column=columnbase+3)
        self.asic0_final_result = tk.Label(self, text="TBD", width=10)
        self.asic0_final_result.grid(sticky=tk.W, row=8, column=columnbase+4)        
        
        self.asic1_result = tk.Label(self, text="ASIC 1 Results:", width=15)
        self.asic1_result.grid(sticky=tk.W,row=9,column=columnbase+0)        
        self.asic1_baseline_result = tk.Label(self, text="TBD", width=10)
        self.asic1_baseline_result.grid(sticky=tk.W, row=9, column=columnbase+1)        
        self.asic1_monitor_result = tk.Label(self, text="TBD", width=10)
        self.asic1_monitor_result.grid(sticky=tk.W, row=9, column=columnbase+2)        
        self.asic1_alive_result = tk.Label(self, text="TBD", width=10)
        self.asic1_alive_result.grid(sticky=tk.W, row=9, column=columnbase+3)
        self.asic1_final_result = tk.Label(self, text="TBD", width=10)
        self.asic1_final_result.grid(sticky=tk.W, row=9, column=columnbase+4)      

        self.asic2_result = tk.Label(self, text="ASIC 2 Results:", width=15)
        self.asic2_result.grid(sticky=tk.W,row=10,column=columnbase+0)        
        self.asic2_baseline_result = tk.Label(self, text="TBD", width=10)
        self.asic2_baseline_result.grid(sticky=tk.W, row=10, column=columnbase+1)        
        self.asic2_monitor_result = tk.Label(self, text="TBD", width=10)
        self.asic2_monitor_result.grid(sticky=tk.W, row=10, column=columnbase+2)        
        self.asic2_alive_result = tk.Label(self, text="TBD", width=10)
        self.asic2_alive_result.grid(sticky=tk.W, row=10, column=columnbase+3)
        self.asic2_final_result = tk.Label(self, text="TBD", width=10)
        self.asic2_final_result.grid(sticky=tk.W, row=10, column=columnbase+4)      

        self.asic3_result = tk.Label(self, text="ASIC 3 Results:", width=15)
        self.asic3_result.grid(sticky=tk.W,row=11,column=columnbase+0)        
        self.asic3_baseline_result = tk.Label(self, text="TBD", width=10)
        self.asic3_baseline_result.grid(sticky=tk.W, row=11, column=columnbase+1)        
        self.asic3_monitor_result = tk.Label(self, text="TBD", width=10)
        self.asic3_monitor_result.grid(sticky=tk.W, row=11, column=columnbase+2)        
        self.asic3_alive_result = tk.Label(self, text="TBD", width=10)
        self.asic3_alive_result.grid(sticky=tk.W, row=11, column=columnbase+3)
        self.asic3_final_result = tk.Label(self, text="TBD", width=10)
        self.asic3_final_result.grid(sticky=tk.W, row=11, column=columnbase+4)      

        #Finish/reset button
        finish_button = tk.Button(self, text="Reset and Power Down",command=self.reset_gui,width=25)
        finish_button.grid(row=12,column=columnbase,columnspan=25)

        """
        #Adding the record data button
        analyze_data_button = Button(self, text="Analyze Data", command=self.analyze_data,width=25)
        analyze_data_button.grid(row=3,column=columnbase,columnspan=25)

        self.analyze_data_result = Label(self, text="",width=25)
        self.analyze_data_result.grid(sticky=W,row=3,column=columnbase+25,columnspan=25)

        #Adding the archive results button
        archive_results_button = Button(self, text="Archive Results", command=self.archive_results,width=25)
        archive_results_button.grid(row=4,column=columnbase,columnspan=25)

        self.archive_results_result = Label(self, text="",width=25)
        self.archive_results_result.grid(sticky=W,row=4,column=columnbase+25,columnspan=25)
        """
    def write_default_file(self):
        self.params['operator_name'] = self.operator_entry.get()
        
        if (self.test_stand_other == True):
            self.params['test_stand'] = self.test_stand_entry_other.get()
        else:
            self.params['test_stand'] = self.test_stand_selection.get()
            
        if (self.boardid_other == True):
            self.params['boardid'] = self.boardid_entry_other.get()
        else:
            self.params['boardid'] = self.boardid_selection.get()
            
        if (self.chipver_other == True):
            self.params['chipver'] = self.chipver_entry_other.get()
        else:
            self.params['chipver'] = self.chipver_selection.get()
            
        if (self.fpgamezz_other == True):
            self.params['fpgamezz'] = self.fpgamezz_entry_other.get()
        else:
            self.params['fpgamezz'] = self.fpgamezz_selection.get()
            
        self.params['asic0id'] = self.asic0_entry.get()
        self.params['asic1id'] = self.asic1_entry.get()
        self.params['asic2id'] = self.asic2_entry.get()
        self.params['asic3id'] = self.asic3_entry.get()
        
        self.params['socket0id'] = self.socket0_entry.get()
        self.params['socket1id'] = self.socket1_entry.get()
        self.params['socket2id'] = self.socket2_entry.get()
        self.params['socket3id'] = self.socket3_entry.get()
        
        #Create that default file
        
        self.defaultjson = dict(
            operator_name = self.operator_entry.get(),
            test_stand = self.test_stand_selection.get(),
            test_stand_other = self.test_stand_entry_other.get(),
            boardid = self.boardid_selection.get(),
            boardid_other = self.boardid_entry_other.get(),
            chipver = self.chipver_selection.get(),
            chipver_other = self.chipver_entry_other.get(),
            fpgamezz = self.fpgamezz_selection.get(),
            fpgamezz_other = self.fpgamezz_entry_other.get(),
            asic0id = self.asic0_entry.get(),
            asic1id = self.asic1_entry.get(),
            asic2id = self.asic2_entry.get(),
            asic3id = self.asic3_entry.get(),
            socket0id = self.socket0_entry.get(),
            socket1id = self.socket1_entry.get(),
            socket2id = self.socket2_entry.get(),
            socket3id = self.socket3_entry.get()
        )
        
        jsonFile = os.path.join(self.root_dir,self.config["FILENAMES"]["DEFAULT_GUI_FILE_NAME"])
        with open(jsonFile,'w') as outfile:
            json.dump(self.defaultjson, outfile, indent=4)
            
    def start_measurements(self):
        self.write_default_file()
        self.power_on()
        fw_ver = self.functions.get_fw_version()
        self.params['fw_ver'] = hex(fw_ver)
        
        if (fw_ver < int(self.config["DEFAULT"]["LATEST_FW"], 16)):
            messagebox.showinfo("Warning!", "The FPGA is running firmware version {} when the latest firmware is version {}.  Please let an expert know!".format(hex(fw_ver), hex(int(self.config["DEFAULT"]["LATEST_FW"], 16))))
            
        self.functions.turnOnAsics()
        self.functions.resetBoard()
        self.params['working_chips'] = self.functions.initBoard()
        
        print("""\
                    Operator Name: {operator_name}
                    Test Stand # : {test_stand}
                    Test Board ID: {boardid}
                    FPGA Board ID: {fpgamezz}
                    Chip Version: {chipver}
                    ASIC 0 ID: {asic0id}
                    ASIC 1 ID: {asic1id}
                    ASIC 2 ID: {asic2id}
                    ASIC 3 ID: {asic3id}
                    ASIC 0 SOCKET: {socket0id}
                    ASIC 1 SOCKET: {socket1id}
                    ASIC 2 SOCKET: {socket2id}
                    ASIC 3 SOCKET: {socket3id}
        """.format(**self.params))
        
        
        #Make sure everything was entered ok, that nothing was screwed up
        gui_check = self.config["GUI_SETTINGS"]
        for i in ["asic0id","asic1id","asic2id","asic3id"]:
            j = self.params[i]
            if ((int(j) < int(gui_check['CHIP_MIN'])) or (int(j) > int(gui_check['CHIP_MAX']))):
                print("{}({}) is out of range ({} to {})!".format(i, j, int(gui_check['CHIP_MIN']), int(gui_check['CHIP_MAX'])))
                self.start_button_result["text"] = "ENTER REQUIRED INFO"
                self.update_idletasks()
                return
                
        for i in ["socket0id","socket1id","socket2id","socket3id"]:
            j = self.params[i]
            if ((int(j) < int(gui_check['SOCKET_MIN'])) or (int(j) > int(gui_check['SOCKET_MAX']))):
                print("{}({}) is out of range ({} to {})!".format(i, j, int(gui_check['SOCKET_MIN']), int(gui_check['SOCKET_MAX'])))
                self.start_button_result["text"] = "ENTER REQUIRED INFO"
                self.update_idletasks()
                return
            
        if not (self.params['operator_name'] and self.params['test_stand'] and self.params['boardid'] and self.params['fpgamezz'] and self.params['chipver']):
            print("ENTER REQUIRED INFO")
            self.start_button_result["text"] = "ENTER REQUIRED INFO"
            self.update_idletasks()
            return

        start_time = time.time()
        self.now = time.strftime("%Y%m%dT%H%M%S", time.localtime(time.time()))
        self.chiplist = [[0,self.params['asic0id']],[1,self.params['asic1id']],[2,self.params['asic2id']],[3,self.params['asic3id']]]

        print("BEGIN TESTS")
        self.params.update(chip_list = self.chiplist)
        self.update_idletasks()
        
        #Calls the new generic tester/runner.  Note that this is done in a for loop and the generic tester passes values back by using "Yield"
        #This is the only way I figured out how to get feedback back to the GUI mid-test without changing too much
        for i in (maintest(**self.params)):
            self.postResults(i)

        self.start_button_result["text"] = "DONE "+self.params["session_start_time"]
                              
        self.postResults()          
        
        self.update_idletasks()      
        
        end_time = time.time()
        run_time = end_time-start_time
        print("Total run time: {}".format(int(run_time)))
        print(self.GetTimeString(int(run_time)))

    #Show a live trace to make sure everything is connected correctly
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
            self.PowerSupply.measure_params(channel = 1)
    #       Measure initial volatage and current
            self.PowerSupply.powerSupplyDevice.write(":MEAS:VOLT?")
            initialVoltage = float(self.PowerSupply.powerSupplyDevice.read().strip().decode())
            self.PowerSupply.powerSupplyDevice.write(":MEAS:CURR?")
            initialCurrent = float(self.PowerSupply.powerSupplyDevice.read().lstrip().decode())

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
                
        chiplist = [[0,],[1,],[2,],[3,]]
        chiplist[0].append(self.asic0_entry.get())
        chiplist[1].append(self.asic1_entry.get())
        chiplist[2].append(self.asic2_entry.get())
        chiplist[3].append(self.asic3_entry.get())
        
        self.functions.syncADC(datadir = temp_sync_folder, working_chips = SPI_response, chip_list = chiplist, to_print = True)
        
        self.WF_GUI = tk.Tk()
        self.WF_GUI.protocol("WM_DELETE_WINDOW", self.on_child_closing)
        startWF(self.WF_GUI)
        
    def debug(self):
        self.WF_GUI = tk.Tk()
        self.WF_GUI.protocol("WM_DELETE_WINDOW", self.on_child_closing)
        startWF(self.WF_GUI)

    def reset_gui(self):
        self.on_child_closing()
        #Power down all 4 chips:
        self.runner(executable="femb_control_power", argstr="OFF")

        #Reset GUI:
#        self.operator_entry.delete(0,1000)
#        self.test_stand_entry.delete(0,1000)
#        self.boardid_entry.delete(0,1000)
#        self.asic0_entry.insert(tk.END, "")
#        self.asic1_entry.insert(tk.END, "")
#        self.asic2_entry.insert(tk.END, "")
#        self.asic3_entry.insert(tk.END, "")
        
        self.status_label["text"] = "Nothing started" 
        self.asic0_baseline_result["text"] = "TBD"
        self.asic0_monitor_result["text"] = "TBD"
        self.asic0_alive_result["text"] = "TBD"
        self.asic0_final_result["text"] = "TBD"
        self.asic1_baseline_result["text"] = "TBD"
        self.asic1_monitor_result["text"] = "TBD"
        self.asic1_alive_result["text"] = "TBD" 
        self.asic1_final_result["text"] = "TBD"
        self.asic2_baseline_result["text"] = "TBD"
        self.asic2_monitor_result["text"] = "TBD"
        self.asic2_alive_result["text"] = "TBD"
        self.asic2_final_result["text"] = "TBD"
        self.asic3_baseline_result["text"] = "TBD"
        self.asic3_monitor_result["text"] = "TBD"
        self.asic3_alive_result["text"] = "TBD"
        self.asic3_final_result["text"] = "TBD"
        self.asic0_baseline_result["fg"] = "black"
        self.asic0_monitor_result["fg"] = "black"
        self.asic0_alive_result["fg"] = "black"
        self.asic0_final_result["fg"] = "black"        
        self.asic1_baseline_result["fg"] = "black"
        self.asic1_monitor_result["fg"] = "black"
        self.asic1_alive_result["fg"] = "black"
        self.asic1_final_result["fg"] = "black"        
        self.asic2_baseline_result["fg"] = "black"
        self.asic2_monitor_result["fg"] = "black"
        self.asic2_alive_result["fg"] = "black"
        self.asic2_final_result["fg"] = "black"        
        self.asic3_baseline_result["fg"] = "black"
        self.asic3_monitor_result["fg"] = "black"
        self.asic3_alive_result["fg"] = "black"
        self.asic3_final_result["fg"] = "black"
        self.load_button["bg"]="red"
        
        now = time.time()
        self.params["session_start_time"] = time.strftime("%Y%m%dT%H%M%S", time.localtime(now))
        self.params["session_start_unix"] = now

        self.update_idletasks()

        print("FINISHED TEST - GUI RESET")

    def postResults(self, params):
        datadir = params['datadir']
        working_chips = params['working_chips']
        chip_list = params['chip_list']
        print(datadir)
        print(working_chips)
        print(chip_list)
        for i in range(int(self.config["DEFAULT"]["NASIC_MIN"]), int(self.config["DEFAULT"]["NASIC_MAX"]) + 1, 1):
            if i in working_chips:
                chip_name = chip_list[i][1]
                results_path = os.path.join(datadir, chip_name)
                jsonFile = os.path.join(chip_name, results_path, self.config["FILENAMES"]["RESULTS"])
                with open(jsonFile,'r') as f:
                    results = json.load(f)
                #baseline results
                print(results)
                if "sync_result" in results:
                if self.methodMap['baseline_test_sequence_complete']:
                    if (self.params['asic_pass'][0][0] == -1):
                        self.asic0_baseline_result["text"] = "????"
                        self.asic0_baseline_result["fg"] = "yellow"
                    elif (not self.params['asic_pass'][0][0]):
                        self.asic0_baseline_result["text"] = "Fail"
                        self.asic0_baseline_result["fg"] = "red"
                    else:
                        self.asic0_baseline_result["text"] = "Pass"
                        self.asic0_baseline_result["fg"] = "green"
                    if (self.params['asic_pass'][1][0] == -1):
                        self.asic1_baseline_result["text"] = "????"
                        self.asic1_baseline_result["fg"] = "yellow"
                    elif (not self.params['asic_pass'][1][0]):
                        self.asic1_baseline_result["text"] = "Fail"
                        self.asic1_baseline_result["fg"] = "red"
                    else:
                        self.asic1_baseline_result["text"] = "Pass"
                        self.asic1_baseline_result["fg"] = "green"
                    if (self.params['asic_pass'][2][0] == -1):
                        self.asic2_baseline_result["text"] = "????"
                        self.asic2_baseline_result["fg"] = "yellow"
                    elif (not self.params['asic_pass'][2][0]):
                        self.asic2_baseline_result["text"] = "Fail"
                        self.asic2_baseline_result["fg"] = "red"
                    else: 
                        self.asic2_baseline_result["text"] = "Pass"
                        self.asic2_baseline_result["fg"] = "green"
                    if (self.params['asic_pass'][3][0] == -1):
                        self.asic3_baseline_result["text"] = "????"
                        self.asic3_baseline_result["fg"] = "yellow"
                    elif (not self.params['asic_pass'][3][0]):
                        self.asic3_baseline_result["text"] = "Fail"
                        self.asic3_baseline_result["fg"] = "red"
                    else:
                        self.asic3_baseline_result["text"] = "Pass"
                        self.asic3_baseline_result["fg"] = "green"
                
    def failed(self,label):
        pass
    
    def passed(self,label):
        pass
    
    def skipped(self,label):
        pass
    
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

def main():
    root = tk.Tk()
    GUI_WINDOW(root)
    root.mainloop() 
    
if __name__ == '__main__':
    main()
