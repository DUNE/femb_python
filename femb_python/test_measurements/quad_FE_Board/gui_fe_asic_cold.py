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
import json
import getpass

import sys
import os                                 # for statv
import os.path
import time
import git
#import sys

#import the test module
#from femb_python.test_measurements.feAsicTest.doFembTest_simpleMeasurement import FEMB_TEST_SIMPLE
#from femb_python.test_measurements.feAsicTest.doFembTest_gainMeasurement import FEMB_TEST_GAIN

from femb_python import runpolicy
from femb_python.configuration import CONFIG
from femb_python.test_instrument_interface.rigol_dp800 import RigolDP800
from femb_python.test_measurements.OscillatorTesting.code.driverUSBTMC import DriverUSBTMC
from femb_python.test_measurements.sbnd_femb_test.define_tests import main as maintest

class GUI_WINDOW(tk.Frame):

    #GUI window defined entirely in init function
    def __init__(self, master=None,forceQuick=False,forceLong=False):
        self.use_sumatra = True
        repo = git.Repo(__file__, search_parent_directories=True)
        self.sw_version = repo.head.object.hexsha

        #It's calling the constructor of the parent tkinter object, the pack method of the class, which is now a tkinter object
        tk.Frame.__init__(self,master)
        self.pack()

        self.config = CONFIG()
        #update after completing each test
        self.methodMap = {'baseline_test_sequence' : 0,
                          'monitor_data_test_sequence' : 1,
                          'input_alive_power_cycle_sequence' : 2,
                          'baseline_test_sequence_complete' : False,
                          'monitor_data_test_sequence_complete' : False,
                          'input_alive_power_cycle_sequence_complete' : False}
        # fixme: a huge chunk of the following code is now generically
        # available as runpolicy.make_runner().

        #define required variables
        self.params = dict(
            test_category = "feasic_quad_cold",
            sw_version = self.sw_version,
            use_sumatra = self.use_sumatra,
            #TODO make this programmatically expandable for new tests
            asic_pass = [[-1,-1,-1],[-1,-1,-1],[-1,-1,-1],[-1,-1,-1]], #results for each test
            config_list = [0,0,0,0], #update if any sockets fail configuration stage
        )
        
        self.root_dir = self.getDefaultFile()
        file_name = os.path.join(self.root_dir,self.config.default_file_name)
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
        stands = self.config.known_test_stands
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
        boards = self.config.known_quad_boards
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
        chips = self.config.known_chip_versions
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
        fpgas = self.config.known_fpga_mezzanines
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

        self.asic0_entry = tk.Spinbox(self, width=spinner_width, from_=self.config.chip_range[0], to=self.config.chip_range[1])
        self.asic0_entry.insert(tk.END, self.default_settings["asic0id"])
        self.asic0_entry.delete(0)
        self.asic0_entry.grid(sticky=tk.W,row=8,column=columnbase+1)

        # ASIC 1 ID

        self.asic1_entry = tk.Spinbox(self, width=spinner_width, from_=self.config.chip_range[0], to=self.config.chip_range[1])
        self.asic1_entry.insert(tk.END, self.default_settings["asic1id"])
        self.asic1_entry.delete(0)
        self.asic1_entry.grid(sticky=tk.W,row=9,column=columnbase+1)

        # ASIC 2 ID

        self.asic2_entry = tk.Spinbox(self, width=spinner_width, from_=self.config.chip_range[0], to=self.config.chip_range[1])
        self.asic2_entry.insert(tk.END, self.default_settings["asic2id"])
        self.asic2_entry.delete(0)
        self.asic2_entry.grid(sticky=tk.W,row=10,column=columnbase+1)

        # ASIC 3 ID
        self.asic3_entry = tk.Spinbox(self, width=spinner_width, from_=self.config.chip_range[0], to=self.config.chip_range[1])
        self.asic3_entry.insert(tk.END, self.default_settings["asic3id"])
        self.asic3_entry.delete(0)
        self.asic3_entry.grid(sticky=tk.W,row=11,column=columnbase+1)                      
        
        # SOCKET 0 ID

        self.socket0_entry = tk.Spinbox(self, width=spinner_width, from_=self.config.socket_range[0], to=self.config.socket_range[1])
        self.socket0_entry.insert(tk.END, self.default_settings["socket0id"])
        self.socket0_entry.delete(0)
        self.socket0_entry.grid(sticky=tk.W,row=8,column=columnbase+2)

        # SOCKET 1 ID

        self.socket1_entry = tk.Spinbox(self, width=spinner_width, from_=self.config.socket_range[0], to=self.config.socket_range[1])
        self.socket1_entry.insert(tk.END, self.default_settings["socket1id"])
        self.socket1_entry.delete(0)
        self.socket1_entry.grid(sticky=tk.W,row=9,column=columnbase+2)

        # SOCKET 2 ID

        self.socket2_entry = tk.Spinbox(self, width=spinner_width, from_=self.config.socket_range[0], to=self.config.socket_range[1])
        self.socket2_entry.insert(tk.END, self.default_settings["socket2id"])
        self.socket2_entry.delete(0)
        self.socket2_entry.grid(sticky=tk.W,row=10,column=columnbase+2)

        # SOCKET 3 ID

        self.socket3_entry = tk.Spinbox(self, width=spinner_width, from_=self.config.socket_range[0], to=self.config.socket_range[1])
        self.socket3_entry.insert(tk.END, self.default_settings["socket3id"])
        self.socket3_entry.delete(0)
        self.socket3_entry.grid(sticky=tk.W,row=11,column=columnbase+2) 


    def define_general_commands_column(self):
        columnbase=50

        label = tk.Label(self, text="FE ASIC TESTS")
        label.grid(row=0,column=columnbase, columnspan=50)

        self.load_button = tk.Button(self, text="Load ASICs", bg="red", command=self.load_asics,width=25)
        self.load_button.grid(row=1,column=columnbase,columnspan=25)

        self.load_button_result = tk.Label(self, text="Press Load ASICs before loading",width=25)
        self.load_button_result.grid(sticky=tk.W,row=1,column=columnbase+25,columnspan=25)
        
        self.start_button = tk.Button(self, text="Start Tests", command=self.start_measurements,width=25)
        self.start_button.grid(row=2,column=columnbase,columnspan=25)

        self.start_button_result = tk.Label(self, text="NOT STARTED",width=25)
        self.start_button_result.grid(sticky=tk.W,row=2,column=columnbase+25,columnspan=25)

        #Adding the record data button
        #record_data_button = Button(self, text="Record Data", command=self.record_data,width=25)
        #record_data_button.grid(row=2,column=columnbase,columnspan=25)

#        self.check_setup_result = Label(self, text="CHECK SETUP - NOT STARTED",width=50)
#        self.check_setup_result.grid(sticky=W,row=3,column=columnbase,columnspan=50)

        self.sync_adcs_sequence_result = tk.Label(self, text="SYNCHRONIZING ADCS - NOT STARTED",width=50)
        self.sync_adcs_sequence_result.grid(sticky=tk.W,row=3,column=columnbase,columnspan=50)

        self.baseline_test_sequence_result = tk.Label(self, text="BASELINE TEST - NOT STARTED",width=50)
        self.baseline_test_sequence_result.grid(sticky=tk.W,row=4,column=columnbase,columnspan=50)

        self.monitor_data_test_sequence_result = tk.Label(self, text="MONITOR DATA TEST - NOT STARTED",width=50)
        self.monitor_data_test_sequence_result.grid(sticky=tk.W,row=5,column=columnbase,columnspan=50)

        self.input_alive_power_cycle_sequence_result = tk.Label(self, text="INPUT ALIVE POWER CYCLE TEST - NOT STARTED",width=50)
        self.input_alive_power_cycle_sequence_result.grid(sticky=tk.W,row=6,column=columnbase,columnspan=50)
        
        self.result_label = tk.Label(self, text="", width=25)
        self.result_label.grid(sticky=tk.W,row=8,column=columnbase+2)        
        self.baseline_result_label = tk.Label(self, text="BASELINE", width=10)
        self.baseline_result_label.grid(sticky=tk.W, row=7, column=columnbase+3)        
        self.monitor_result_label = tk.Label(self, text="MONITOR", width=10)
        self.monitor_result_label.grid(sticky=tk.W, row=7, column=columnbase+4)        
        self.alive_result_label = tk.Label(self, text="ALIVE", width=10)
        self.alive_result_label.grid(sticky=tk.W, row=7, column=columnbase+5)
        self.final_result_label = tk.Label(self, text="FINAL", width=10)
        self.final_result_label.grid(sticky=tk.W, row=7, column=columnbase+6)
        
        self.asic0_result = tk.Label(self, text="ASIC 0 Results:", width=25)
        self.asic0_result.grid(sticky=tk.W,row=8,column=columnbase+2)        
        self.asic0_baseline_result = tk.Label(self, text="TBD", width=10)
        self.asic0_baseline_result.grid(sticky=tk.W, row=8, column=columnbase+3)        
        self.asic0_monitor_result = tk.Label(self, text="TBD", width=10)
        self.asic0_monitor_result.grid(sticky=tk.W, row=8, column=columnbase+4)        
        self.asic0_alive_result = tk.Label(self, text="TBD", width=10)
        self.asic0_alive_result.grid(sticky=tk.W, row=8, column=columnbase+5)
        self.asic0_final_result = tk.Label(self, text="TBD", width=10)
        self.asic0_final_result.grid(sticky=tk.W, row=8, column=columnbase+6)        
        
        self.asic1_result = tk.Label(self, text="ASIC 1 Results:", width=25)
        self.asic1_result.grid(sticky=tk.W,row=9,column=columnbase+2)        
        self.asic1_baseline_result = tk.Label(self, text="TBD", width=10)
        self.asic1_baseline_result.grid(sticky=tk.W, row=9, column=columnbase+3)        
        self.asic1_monitor_result = tk.Label(self, text="TBD", width=10)
        self.asic1_monitor_result.grid(sticky=tk.W, row=9, column=columnbase+4)        
        self.asic1_alive_result = tk.Label(self, text="TBD", width=10)
        self.asic1_alive_result.grid(sticky=tk.W, row=9, column=columnbase+5)
        self.asic1_final_result = tk.Label(self, text="TBD", width=10)
        self.asic1_final_result.grid(sticky=tk.W, row=9, column=columnbase+6)

        self.asic2_result = tk.Label(self, text="ASIC 2 Results:", width=25)
        self.asic2_result.grid(sticky=tk.W,row=10,column=columnbase+2)        
        self.asic2_baseline_result = tk.Label(self, text="TBD", width=10)
        self.asic2_baseline_result.grid(sticky=tk.W, row=10, column=columnbase+3)        
        self.asic2_monitor_result = tk.Label(self, text="TBD", width=10)
        self.asic2_monitor_result.grid(sticky=tk.W, row=10, column=columnbase+4)        
        self.asic2_alive_result = tk.Label(self, text="TBD", width=10)
        self.asic2_alive_result.grid(sticky=tk.W, row=10, column=columnbase+5)
        self.asic2_final_result = tk.Label(self, text="TBD", width=10)
        self.asic2_final_result.grid(sticky=tk.W, row=10, column=columnbase+6)

        self.asic3_result = tk.Label(self, text="ASIC 3 Results:", width=25)
        self.asic3_result.grid(sticky=tk.W,row=11,column=columnbase+2)        
        self.asic3_baseline_result = tk.Label(self, text="TBD", width=10)
        self.asic3_baseline_result.grid(sticky=tk.W, row=11, column=columnbase+3)        
        self.asic3_monitor_result = tk.Label(self, text="TBD", width=10)
        self.asic3_monitor_result.grid(sticky=tk.W, row=11, column=columnbase+4)        
        self.asic3_alive_result = tk.Label(self, text="TBD", width=10)
        self.asic3_alive_result.grid(sticky=tk.W, row=11, column=columnbase+5)
        self.asic3_final_result = tk.Label(self, text="TBD", width=10)
        self.asic3_final_result.grid(sticky=tk.W, row=11, column=columnbase+6)

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

    def start_measurements(self):
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
        

        #dump results 
        jsonFile = os.path.join(self.root_dir,self.config.default_file_name)
        with open(jsonFile,'w') as outfile:
            json.dump(self.defaultjson, outfile, indent=4)

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
        
        for i in ["asic0id","asic1id","asic2id","asic3id"]:
            j = self.params[i]
            if ((int(j) < self.config.chip_range[0]) or (int(j) > self.config.chip_range[1])):
                print("{}({}) is out of range ({} to {})!".format(i, j, self.config.chip_range[0], self.config.chip_range[1]))
                self.start_button_result["text"] = "ENTER REQUIRED INFO"
                self.update_idletasks()
                return
                
        for i in ["socket0id","socket1id","socket2id","socket3id"]:
            j = self.params[i]
            if ((int(j) < self.config.socket_range[0]) or (int(j) > self.config.socket_range[1])):
                print("{}({}) is out of range ({} to {})!".format(i, j, self.config.socket_range[0], self.config.socket_range[1]))
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
        self.start_button_result["text"] = "IN PROGRESS"
        self.load_button_result["text"] = "Testing - do not remove"
        self.params.update(chip_list = self.chiplist)
        self.update_idletasks()
        
        for i in (maintest(**self.params)):
            print ("Wow {}".format(i))
            
        sys.exit("think we're done here")

        for method in ["sync_adcs_sequence",
                       "baseline_test_sequence",
                       "monitor_data_test_sequence",
                       "input_alive_power_cycle_sequence"]:
#        for method in ["sync_adcs_sequence",
#                       "baseline_test_sequence"]:
            LOUD = method.replace("_"," ").upper()
            methname = "do_" + method
            meth = getattr(self, methname)

            getattr(self, method+"_result")["text"] = LOUD + " - IN PROGRESS"
            self.update_idletasks()

            #Come on kids...
            try:
                meth()
            except RuntimeError as err:
                print("failed: %s\n%s" % (LOUD, err)) 
                self.start_button_result["text"] = LOUD + " - FAILED "
                getattr(self, method + "_result")["text"] = LOUD + " - FAILED"
                # anything else?
                return
            
            getattr(self, method + "_result")["text"] = LOUD + " - DONE"
            continue

        self.start_button_result["text"] = "DONE "+self.params["session_start_time"]
        
        #this powers off the ASICs and writes final results to the params file
        self.generic_sequence("", "femb_control_power",
                              #range(4), range(4), range(2), 0 , 1 , 1 , 0 , #warm test
                              [2] , [2] , [0] , 0 , 0 , 1 , 0 , #expedited cold test
                              #[2] , [2] , [0] , 0 , 0 , 1 , 0 , #test
                              argstr="OFF", handler=None)
                              
        self.postResults()          
        
        self.update_idletasks()      
        
        end_time = time.time()
        run_time = end_time-start_time
        print("Total run time: {}".format(int(run_time)))
        print(self.GetTimeString(int(run_time)))

    def load_asics(self):
        #Power down all 4 chips:
        self.powerSupplyDevice = None
        dirList = os.listdir("/dev/bus/usb/")
        print("dirList is {}".format(dirList))
        for fName in dirList:
            print("fName is {}".format(fName))
            dirList2 = os.listdir("/dev/bus/usb/{}/".format(fName))
            print("dirList2 is {}".format(dirList2))
            for fName2 in dirList2:
                print("/dev/bus/usb/{}/{}".format(fName,fName2))
                try:
                    device = DriverUSBTMC("/dev/bus/usb/{}/{}".format(fName,fName2))
                    print("device is {}".format(device))
                    deviceID = device.getID()
                    print(deviceID)
                    if(deviceID.startswith(b"RIGOL TECHNOLOGIES,DP832")):
                        print("DC Power Supply found with identification %s" %(deviceID.decode()))
                        self.powerSupplyDevice = device
                except PermissionError:
                    print("Permission Error")
                    pass
                    
        if self.powerSupplyDevice is None:
            print("Power supply of our interest not found!\nExiting!\n")
            sys.exit(1)

        #Turn channels 1 off
        self.powerSupplyDevice.write(":OUTP CH1, OFF")
        time.sleep(1)

        #Choose channel 1
        self.powerSupplyDevice.write(":INST CH1")

        #Set voltage to 5.0 V
        self.powerSupplyDevice.write(":VOLT 5.0")
        self.powerSupplyDevice.write(":OUTP CH1, ON")
        time.sleep(5)
        
        
        
        
        RigolDP800.on(self)
        self.runner(executable="femb_control_power", argstr="ON")
        self.load_button_result["text"] = "Ok to load new ASICs"
        self.update_idletasks()
        self.load_button["bg"]="green"

    def reset_gui(self):
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
        self.params['asic_pass'] = [[-1,-1,-1],[-1,-1,-1],[-1,-1,-1],[-1,-1,-1]]
        
        self.load_button_result["text"] = "Press Load ASICs before loading"
        self.start_button_result["text"] = "NOT STARTED"
#        self.check_setup_result["text"] = "CHECK SETUP - NOT STARTED"
        self.sync_adcs_sequence_result["text"] = "SYNCHRONIZING ADCS - NOT STARTED"
        self.baseline_test_sequence_result["text"] = "BASELINE TEST - NOT STARTED"
        self.monitor_data_test_sequence_result["text"] = "MONITOR DATA TEST - NOT STARTED"
        self.input_alive_power_cycle_sequence_result["text"] = "INPUT ALIVE POWER CYCLE TEST - NOT STARTED"       
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
        
        self.methodMap['baseline_test_sequence_complete'] = False
        self.methodMap['monitor_data_test_sequence_complete'] = False
        self.methodMap['input_alive_power_cycle_sequence_complete'] = False
        
        now = time.time()
        self.params["session_start_time"] = time.strftime("%Y%m%dT%H%M%S", time.localtime(now))
        self.params["session_start_unix"] = now

        self.update_idletasks()

        print("FINISHED TEST - GUI RESET")    

    def do_sync_adcs_sequence(self):
        '''
        synchronize the ADCs
        '''
        print("SYNCHRONIZING ADCS")
        self.sync_adcs_sequence_result["text"] = "SYNCHRONIZING ADCS - IN PROGRESS"
        self.update_idletasks()
        self.test_result = 0
        
        
        
        resolved = self.runner(**self.params)     
                    
        #look to see if any chips failed the configuration and skip over them for the future tests
        for chip_name in self.chiplist:
            file_name = os.path.join(resolved['datadir'],chip_name[1],"sync_adcs","results.json")
            print("file_name for sync results check: {}".format(file_name))
            if os.path.isfile(file_name):
                with open(file_name, 'r') as f:
                    jsondata = json.load(f)
                    self.params['config_list'] = jsondata['config_list']

    def generic_sequence_handler(self, **params):
        '''Generically handle results after an executable runs.  The params
        are the resolved input parameters'''
        button = getattr(self, self.params['method']+"_result")
        button["text"] = title + " - DONE"
        self.update_idletasks()

    def generic_sequence(self, method, executable, gains, shapes, bases,leakage,leakagex10,buff,acdc, argstr="{paramfile}", handler=None):

        '''
        Generically, run an executable through a sequence of gains/shape/bases
        '''

        datasubdir="{method}-g{gain_ind}s{shape_ind}b{base_ind}"
        outlabel="{datasubdir}-{test_start_time}"
        exec_now = time.strftime("%H:%M:%S", time.localtime(time.time()))
#        print("passing instructions to runner at {}".format(exec_now))
        

        title = method.upper().replace("_", " ")
        print (title)
        if argstr == "{paramfile}": #do this for the tests, not the final power off
            button = getattr(self, method+"_result")
            button["text"] = title + " - IN PROGRESS"
        self.update_idletasks()        
        for gain in gains:
            for shape in shapes:
                for base in bases:
                    # this raises RuntimeError if measurement script fails
                    resolved = self.runner(**self.params,
                                           datasubdir="{method}-g{gain_ind}s{shape_ind}b{base_ind}-{leakage_ind}{leakagex10_ind}{buffer_ind}{acdc_ind}",
                                           outlabel = outlabel,
                                           test_start_time = self.now,
                                           execute_start_time = exec_now,
                                           executable=executable,
                                           method=method,
                                           argstr="{paramfile}",  #change back to {paramfile} 
                                           gain_ind = gain, 
                                           shape_ind = shape, 
                                           base_ind = base,
                                           leakage_ind = leakage,
                                           leakagex10_ind = leakagex10,
                                           buffer_ind = buff,
                                           acdc_ind = acdc,
                                           chip_list = self.chiplist)
                    if handler:
                        self.methodMap[method+'_complete'] = True
                        handler(**resolved)
                    else:
                        continue
                        self.generic_sequence_handler(**resolved)
#                        

        
        
    def handle_result(self, **params):
        """
        Check pass/fail for each test
        """
        for num,chip_name in self.chiplist:
            file_name = os.path.join(params['datadir'],chip_name,params['datasubdir'],"results.json")
            if os.path.isfile(file_name):
                with open(file_name, 'r') as f:
                    jsondata = json.load(f)
                    result = jsondata['result']  
                    if self.params['asic_pass'][num][self.methodMap[params['method']]] == 0:
                        continue
                    elif result == "Pass":
                        self.params['asic_pass'][num][self.methodMap[params['method']]] = 1
                    else:
                        self.params['asic_pass'][num][self.methodMap[params['method']]] = 0
                    self.params['config_list'] = jsondata['config_list']
        return
    
    def do_baseline_test_sequence(self):
        '''
        collect then analyze the baseline and RMS data
        '''
        print("DOING TEST OF BASELINE + RMS")           

        start_time = time.time()
         
        self.generic_sequence("baseline_test_sequence", "femb_feasic_sbnd_baseline_test",
                              #range(4), range(4), range(2), 0 , 1 , 1 , 0 , #warm test
                              [2] , [2] , [0] , 0 , 0 , 1 , 0 , #expedited cold test
                              #[2] , [2] , [0] , 0 , 0 , 1 , 0 , #test
                              handler=self.handle_result)
                              
        end_time = time.time()
        run_time = end_time-start_time
        print("Total run time for baseline test sequence: {}\n\n".format(int(run_time)))
        self.postResults()

        return

    def do_monitor_data_test_sequence(self):
        print("DOING TEST OF MONITOR DATA")
        
        start_time = time.time()
        
        #required that baseline_test_squence have had already run over at least the same parameters
        self.generic_sequence("monitor_data_test_sequence", "femb_feasic_sbnd_monitor_test",
                              #range(4), [1], [0] , 0 , 1 , 1 , 0 , #warm test
                              [2] , [2] , [0] , 0 , 0 , 1 , 0 , #expedited cold test
                              #[2] , [2] , [0] , 0 , 0 , 1 , 0 , #test
                              handler=self.handle_result)
                             
        self.postResults()
        return 

    def do_input_alive_power_cycle_sequence(self):
        print("DOING TEST FOR INPUT POWER ALIVE AND POWER CYCLE SEQUENCE")
        
        start_time = time.time()
        
        self.generic_sequence("input_alive_power_cycle_sequence", "femb_feasic_sbnd_alive_test",
                              #range(4), [1], [0] , 0 , 1 , 1 , 0 , #warm test
                              [2] , [2] , [0] , 0 , 0 , 1 , 0 , #expedited cold test
                              #[2] , [2] , [0] , 0 , 0 , 1 , 0 , #test
                              handler=self.handle_result)
                            
        self.postResults()
        return


    def postResults(self):      
        #baseline results
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
        if self.methodMap['monitor_data_test_sequence_complete']:
            #monitor results
            if (self.params['asic_pass'][0][1] == -1):
                self.asic0_monitor_result["text"] = "????"
                self.asic0_monitor_result["fg"] = "yellow"
            elif (not self.params['asic_pass'][0][1]):
                self.asic0_monitor_result["text"] = "Fail"
                self.asic0_monitor_result["fg"] = "red"
            else:
                self.asic0_monitor_result["text"] = "Pass"
                self.asic0_monitor_result["fg"] = "green"
            if (self.params['asic_pass'][1][1] == -1):
                self.asic1_monitor_result["text"] = "????"
                self.asic1_monitor_result["fg"] = "yellow"
            elif (not self.params['asic_pass'][1][1]):
                self.asic1_monitor_result["text"] = "Fail"
                self.asic1_monitor_result["fg"] = "red"
            else:
                self.asic1_monitor_result["text"] = "Pass"
                self.asic1_monitor_result["fg"] = "green"
            if (self.params['asic_pass'][2][1] == -1):
                self.asic2_monitor_result["text"] = "????"
                self.asic2_monitor_result["fg"] = "yellow"
            elif (not self.params['asic_pass'][2][1]):
                self.asic2_monitor_result["text"] = "Fail"
                self.asic2_monitor_result["fg"] = "red"
            else:
                self.asic2_monitor_result["text"] = "Pass"
                self.asic2_monitor_result["fg"] = "green"
            if (self.params['asic_pass'][3][1] == -1):
                self.asic3_monitor_result["text"] = "????"
                self.asic3_monitor_result["fg"] = "yellow"
            elif (not self.params['asic_pass'][3][1]):
                self.asic3_monitor_result["text"] = "Fail"
                self.asic3_monitor_result["fg"] = "red"
            else:
                self.asic3_monitor_result["text"] = "Pass"
                self.asic3_monitor_result["fg"] = "green"
        if self.methodMap['input_alive_power_cycle_sequence_complete']:
            #alive results
            if (self.params['asic_pass'][0][2] == -1):
                self.asic0_alive_result["text"] = "????"
                self.asic0_alive_result["fg"] = "yellow"
            elif (not self.params['asic_pass'][0][2]):
                self.asic0_alive_result["text"] = "Fail"
                self.asic0_alive_result["fg"] = "red"
            else:
                self.asic0_alive_result["text"] = "Pass"
                self.asic0_alive_result["fg"] = "green"
            if (self.params['asic_pass'][1][2] == -1):
                self.asic1_alive_result["text"] = "????"
                self.asic1_alive_result["fg"] = "yellow"
            elif (not self.params['asic_pass'][1][2]):
                self.asic1_alive_result["text"] = "Fail"
                self.asic1_alive_result["fg"] = "red"
            else:
                self.asic1_alive_result["text"] = "Pass"
                self.asic1_alive_result["fg"] = "green"
            if (self.params['asic_pass'][2][2] == -1):
                self.asic2_alive_result["text"] = "????"
                self.asic2_alive_result["fg"] = "yellow"
            elif (not self.params['asic_pass'][2][2]):
                self.asic2_alive_result["text"] = "Fail"
                self.asic2_alive_result["fg"] = "red"
            else:
                self.asic2_alive_result["text"] = "Pass"
                self.asic2_alive_result["fg"] = "green"
            if (self.params['asic_pass'][3][2] == -1):
                self.asic3_alive_result["text"] = "????"
                self.asic3_alive_result["fg"] = "yellow"
            elif (not self.params['asic_pass'][3][2]):
                self.asic3_alive_result["text"] = "Fail"
                self.asic3_alive_result["fg"] = "red"
            else:
                self.asic3_alive_result["text"] = "Pass"
                self.asic3_alive_result["fg"] = "green"
                
        if ((self.methodMap['baseline_test_sequence_complete']) and (self.methodMap['monitor_data_test_sequence_complete']) and (self.methodMap['input_alive_power_cycle_sequence_complete'])):
            #final result
            if (self.params['asic_pass'][0] == [1,1,1]):
                self.asic0_final_result["text"] = "Pass"
                self.asic0_final_result["fg"] = "green" 
            else:
                self.asic0_final_result["text"] = "Fail"
                self.asic0_final_result["fg"] = "red"
            if (self.params['asic_pass'][1] == [1,1,1]):
                self.asic1_final_result["text"] = "Pass"
                self.asic1_final_result["fg"] = "green" 
            else:
                self.asic1_final_result["text"] = "Fail"
                self.asic1_final_result["fg"] = "red"
            if (self.params['asic_pass'][2] == [1,1,1]):
                self.asic2_final_result["text"] = "Pass"
                self.asic2_final_result["fg"] = "green" 
            else:
                self.asic2_final_result["text"] = "Fail"
                self.asic2_final_result["fg"] = "red"
            if (self.params['asic_pass'][3] == [1,1,1]):
                self.asic3_final_result["text"] = "Pass"
                self.asic3_final_result["fg"] = "green" 
            else:
                self.asic3_final_result["text"] = "Fail"
                self.asic3_final_result["fg"] = "red"
    # Can add additional testing sequences like as above with a method name
    # like "do_<semantic_label>".
    def GetTimeString(self, t):
        sec = timedelta(seconds=t)
        d = datetime(1,1,1) + sec    
        time_str = "{}:{}:{}".format(d.hour, d.minute, d.second)
        return time_str
        
    def resolveParams(self, **params):
        params = self.params.copy()
        params.update(self.params)

        while True:             # warning: cycles will loop 
            newparams = dict()
            changes = 0
            for var, val in sorted(params.items()):
                if type(val) != str:
                    newparams[var] = val
                    continue
                newval = val.format(**params)
                if val != newval:
                    changes += 1
                newparams[var] = newval
            if not changes:
                return newparams
            params = newparams  # around again

        return params
        
    def getDefaultFile(self):
        try:
            femb_config = os.environ["FEMB_CONFIG"]  # required
        except KeyError:
            print( "ERROR RUNPOLICY - Please set the environment variable FEMB_CONFIG" )
            return None

        # Check out the data disk situation and find the most available disk
        freedisks = list()
        datadisks=["/tmp"]
        hostname = os.uname()[1]
        if (hostname.startswith("hoth") or hostname.startswith("hunk")):
            datadisks = ["/dsk/1", "/dsk/2"]
        for dd in datadisks:
            stat = os.statvfs(dd)
            MB = stat.f_bavail * stat.f_frsize >> 20
            freedisks.append((MB, dd))
        freedisks.sort()
        lo_disk = freedisks[0][1]

        user = getpass.getuser()
        if ("user" == "oper"):
            datadisk = "{}/data".format(lo_disk)
        else:
            datadisk = "{}/tmp".format(lo_disk)
            
        root_testdir = "{}/{}/{}/{}".format(datadisk,user,self.params["test_category"],femb_config)
        step1 = "{}/{}/{}/".format(datadisk,user,self.params["test_category"])
        step2 = "{}/{}/".format(datadisk,user)
        
        for i in [step1,step2,root_testdir]:
            if not os.path.exists(i):
                os.makedirs(i)
        
        return root_testdir


def main():
    root = tk.Tk()
    root.title("Quad FE ASIC Test GUI")
    window = GUI_WINDOW(root)
    root.mainloop() 

if __name__ == '__main__':
    main()
