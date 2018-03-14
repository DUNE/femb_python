"""
ADC Test Stand GUI for Cold Tests
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
import datetime
import socket
import os
import os.path
import pwd
import sys
import glob
import json
import pprint
from time import sleep
from tkinter import *
import subprocess
import traceback

#import the test module
import femb_python
from ...configuration import CONFIG
from ...runpolicy import DirectRunner, SumatraRunner
from ...trace_fft_window import TRACE_FFT_WINDOW
from ...trace_allchan_window import TRACE_ALLCHAN_WINDOW
from ...helper_scripts.show_trace_root import TRACE_ROOT_WINDOW, FFT_ROOT_WINDOW

GUITESTMODE=False

class GUI_WINDOW(Frame):

    #GUI window defined entirely in init function
    def __init__(self, master=None,forceLong=False):
        Frame.__init__(self,master)
        self.pack()

        self.config = CONFIG()

        self.forceLong = forceLong

        self.timestamp = None
        self.iTry_david_adams = 1
        self.iTry_configure = 1
        self.waveform_window = None # for live waveform
        self.waveform_root_windows = [] # for ROOT files
        self.waveform_root_viewers = [] # for ROOT files
        self.result_labels = []
        self.display_procs = []
        #Define general commands column
        self.define_test_details_column()
        self.reset()

        self.master.protocol("WM_DELETE_WINDOW", self.exit)

        self.data_base_dir = "/dsk/1/data"
        try:
            self.data_base_dir = os.environ["FEMB_DATA_DIR"]
        except KeyError:
            pass

    def define_test_details_column(self):
        columnbase=0

        # Adding operator name label and read entry box
        self.operator_label = Label(self,text="Operator Name:",width=25)
        self.operator_label.grid(sticky=W,row=1,column=columnbase+0)

        self.operator_entry = Entry(self,width=25)
        self.operator_entry.grid(sticky=W,row=1,column=columnbase+1)

        # Adding electronics ID and read entry box
        self.boardid_label = Label(self,text="Test Board ID:",width=25)
        self.boardid_label.grid(sticky=W,row=3,column=columnbase+0)

        self.boardid_entry = Entry(self,width=25)
        self.boardid_entry.grid(sticky=W,row=3,column=columnbase+1)

        # ASIC IDs
        self.asic_entries = []
        self.asic_labels = []
        for i in range(self.config.NASICS):
            label = Label(self,text="ASIC {} ID:".format(i),width=25)
            label.grid(sticky=W,row=6+i,column=columnbase+0)

            asic_entry = Entry(self,width=25)
            asic_entry.grid(sticky=W,row=6+i,column=columnbase+1)

            self.asic_labels.append(label)
            self.asic_entries.append(asic_entry)

        self.beforeprepare_label = Label(self,text="",width=30)
        self.beforeprepare_label.grid(row=21,column=columnbase,columnspan=2)

        self.prepare_button_text = "Power-up & Setup Board"
        self.prepare_button = Button(self, text=self.prepare_button_text, command=self.prepare_board,width=25)
        self.prepare_button.grid(row=22,column=columnbase,columnspan=2)
        self.activebkg_color = self.prepare_button.cget("activebackground")

        self.coolboard_label = Label(self,text="",width=30,fg="#0000FF")
        self.coolboard_label.grid(row=230,column=columnbase,columnspan=2)

        self.reconfigure_button = Button(self, text="Re-Setup Board\n(Keeps Timestamp)", command=self.reconfigure_board,width=25,state="disabled")
        self.reconfigure_button.grid(row=240,column=columnbase,columnspan=2)

        self.resetwaveform_button = Button(self, text="Restart Waveform Viewer", command=self.reset_waveform_viewer,width=25,state="disabled")
        self.resetwaveform_button.grid(row=250,column=columnbase,columnspan=2,pady=30)

        # Adding ASIC/channel select

        self.selectSocket_label = Label(self,text="View Socket:",state="disabled")
        self.selectSocket_label.grid(sticky=E,row=260,column=columnbase+0)
        self.selectSocket_entry = Spinbox(self,from_=0,to=self.config.NASICS-1,insertwidth=1,width=4,state="disabled")
        self.selectSocket_entry.grid(sticky=W,row=260,column=columnbase+1)
        if self.config.NASICS == 1:
            self.selectSocket_label.grid_forget()
            self.selectSocket_entry.grid_forget()

        self.selectChannel_label = Label(self,text="View Channel:",state="disabled")
        self.selectChannel_label.grid(sticky=E,row=280,column=columnbase+0)
        self.selectChannel_label.grid_forget()

        self.selectChannel_entry = Spinbox(self,from_=0,to=15,insertwidth=3,width=4,state="disabled")
        self.selectChannel_entry.grid(sticky=W,row=280,column=columnbase+1)
        self.selectChannel_entry.grid_forget()

        self.selectChannel_button = Button(self, text="Select Socket to View", command=self.call_selectChannel,width=25,state="disabled")
        self.selectChannel_button.grid(row=300,column=columnbase,columnspan=2)

        self.selectChannel_result = Label(self, text="")
        self.selectChannel_result.grid(sticky=W,row=320,column=columnbase)

        # DC Current box
        self.current_label = Label(self,text="CH2 Current [A]:",width=25,state="disabled")
        self.current_label.grid(sticky=W,row=340,column=columnbase+0)

        self.current_entry = Entry(self,width=25,state="disabled")
        self.current_entry.grid(sticky=W,row=340,column=columnbase+1)

        self.start_david_adams_button = Button(self, text="Collect David Adams Data", command=self.start_david_adams,width=25)
        self.start_david_adams_button.grid(row=360,column=columnbase,columnspan=2,pady=30)

        self.retry_david_adams_label = Label(self,text="",width=30,fg="#0000FF")
        self.retry_david_adams_label.grid(row=370,column=columnbase,columnspan=2)

        self.start_button = Button(self, text="Start Tests", command=self.start_measurements,width=25)
        self.start_button.grid(row=380,column=columnbase,columnspan=2,pady=30)

        self.reset_button = Button(self, text="Reset & Power-off", command=self.reset,width=25,bg="#FF8000")
        self.reset_button.grid(row=400,column=columnbase,columnspan=2)

        self.runid_label = Label(self, text="")
        self.runid_label.grid(row=440,column=columnbase,columnspan=2,pady=20)

        self.status_label = Label(self, text="NOT STARTED",bd=1,relief=SUNKEN,width=50)
        self.status_label.grid(row=1000,column=columnbase,columnspan=2)
        self.bkg_color = self.status_label.cget("background")

    def get_options(self,getCurrent=False):
        operator = self.operator_entry.get()
        boardid = self.boardid_entry.get()
        current = None
        if getCurrent:
            current = self.current_entry.get()
        # ASIC IDs
        asic_ids = []
        for i in range(self.config.NASICS):
            serial = self.asic_entries[i].get()
            asic_ids.append(serial)

        variables = [operator,boardid]+asic_ids
        for var in variables:
            if var == "" :
                return
        if getCurrent:
            if current == "":
                return
            try:
                current = float(current)
            except:
                return

        print("Operator Name: '{}'".format(operator))
        print("Test Board ID: '{}'".format(boardid))
        for i in range(self.config.NASICS):
            print("ASIC {} ID: '{}'".format(i,asic_ids[i]))

        # need serialnumber list, operator, board_id, timestamp, hostname
        timestamp = self.timestamp
        if timestamp is None:
            timestamp = datetime.datetime.now().replace(microsecond=0).isoformat().replace(":","").replace("-","")
        self.timestamp = timestamp
        hostname = socket.gethostname() 
        chipidstr = ""
        for i in asic_ids:
            chipidstr += str(i) + ","
        chipidstr = chipidstr[:-1]
        runid = "{} {} chip: {}".format(hostname,timestamp, chipidstr)
        print("runid: '{}'".format(runid))
        femb_config_name = os.environ["FEMB_CONFIG"]
        linux_username = pwd.getpwuid(os.getuid()).pw_name
        femb_python_location = os.path.dirname(femb_python.__file__)
        firmware_1MHz = None
        firmware_2MHz = None
        try:
            firmware_1MHz = self.config.FIRMWAREPATH1MHZ
        except AttributeError:
            pass
        try:
            firmware_2MHz = self.config.FIRMWAREPATH2MHZ
        except AttributeError:
            pass
        cold = True
        quick = True
        if self.forceLong:
            quick = False

        inputOptions = {
            "operator": operator,
            "board_id": boardid,
            "serials": asic_ids,
            "timestamp": timestamp,
            "hostname": hostname,
            "runid": runid,
            "femb_config_name": femb_config_name,
            "linux_username": linux_username,
            "femb_python_location": femb_python_location,
            "firmware_1MHz": firmware_1MHz,
            "firmware_2MHz": firmware_2MHz,
            "cold": cold,
            "quick": quick,
        }
        if getCurrent:
            inputOptions["current"] = current
        pghost = os.environ.get("PGHOST")
        if pghost:
            print ("Using PostgreSQL database at %s" % pghost)
            inputOptions.update(
                smtstore="postgres://{pguser}@{pghost}/{pgdatabase}",
                pguser = os.environ['PGUSER'],
                pghost = os.environ['PGHOST'],
                pgdatabase = os.environ['PGDATABASE'],
            )
        else:
            print ("Using Sqlite3 database in rundir")
        print(inputOptions)
        return inputOptions

    def reset(self):
        print("POWER DOWN")
        if not GUITESTMODE:
            self.config.POWERSUPPLYINTER.off()
            self.config.FUNCGENINTER.stop()
        if self.waveform_window:
            self.waveform_window.destroy()
        for iWin in reversed(range(len(self.waveform_root_windows))):
            win = self.waveform_root_windows.pop(iWin)
            win.destroy()
        self.waveform_root_viewers = []
        self.timestamp = None
        self.iTry_david_adams = 1
        self.iTry_configure = 1
        for i in reversed(range(len(self.display_procs))):
            tmp = self.display_procs.pop(i)
            tmp.terminate()
            try:
                tmp.wait(2)
            except subprocess.TimeoutExpired:
                tmp.kill()
            del tmp
        for i in reversed(range(len(self.result_labels))):
            tmp = self.result_labels.pop(i)
            tmp.destroy()
        self.status_label["text"] = "NOT STARTED"
        self.status_label["fg"] = "#000000"
        self.status_label["bg"] = self.bkg_color
        self.runid_label["text"] = ""
        self.prepare_button["state"] = "normal"
        self.prepare_button["text"] = self.prepare_button_text
        self.prepare_button["bg"] = self.bkg_color
        self.prepare_button["activebackground"] = self.activebkg_color
        self.coolboard_label["text"] = ""
        self.reconfigure_button["state"] = "disabled"
        self.retry_david_adams_label["text"] = ""
        self.start_button["state"] = "disabled"
        self.start_david_adams_button["state"] = "disabled"
        self.operator_label["state"] = "normal"
        self.operator_entry["state"] = "normal"
        self.boardid_label["state"] = "normal"
        self.boardid_entry["state"] = "normal"
        self.current_label["state"] = "disabled"
        self.current_entry["state"] = "normal"
        self.current_entry.delete(0,END)
        self.current_entry["state"] = "disabled"
        #self.operator_entry.delete(0,END)
        #self.boardid_entry.delete(0,END)
        self.resetwaveform_button["state"] = "disabled"
        self.selectSocket_label["state"] = "disabled"
        self.selectSocket_entry["state"] = "disabled"
        self.selectChannel_label["state"] = "disabled"
        self.selectChannel_entry["state"] = "disabled"
        self.selectChannel_button["state"] = "disabled"
        self.selectChannel_result["text"] = ""
        for i in range(self.config.NASICS):
            self.asic_labels[i]["state"] = "normal"
            self.asic_entries[i]["state"] = "normal"
            #self.asic_entries[i].delete(0,END)
        self.reset_button["bg"] ="#FF9900"
        self.reset_button["activebackground"] ="#FFCF87"

    def prepare_board(self,power_cycle=True):
        power_on = False
        power_off = False
        if power_cycle:
            self.timestamp = None # get new timestamp for each prepare board
            self.iTry_configure = 1
            self.iTry_david_adams = 1
            power_on = True
        if self.waveform_window:
          self.waveform_window.destroy()
        for iWin in reversed(range(len(self.waveform_root_windows))):
            win = self.waveform_root_windows.pop(iWin)
            win.destroy()
        self.waveform_root_viewers = []
        for i in reversed(range(len(self.result_labels))):
            tmp = self.result_labels.pop(i)
            tmp.destroy()
        inputOptions = self.get_options()
        if inputOptions is None:
            print("ENTER REQUIRED INFO")
            self.status_label["text"] = "ENTER REQUIRED INFO"
            self.status_label["fg"] = "#FF0000"
            self.status_label["bg"] = self.bkg_color
            return
        print("BEGIN PREPARE")
        self.resetwaveform_button["state"] = "disabled"
        self.selectSocket_label["state"] = "disabled"
        self.selectSocket_entry["state"] = "disabled"
        self.selectChannel_label["state"] = "disabled"
        self.selectChannel_entry["state"] = "disabled"
        self.selectChannel_button["state"] = "disabled"
        self.selectChannel_result["text"] = ""
        self.retry_david_adams_label["text"] = ""
        self.start_button["state"] = "disabled"
        self.start_david_adams_button["state"] = "disabled"
        self.status_label["text"] = "POWERING UP BOARD..."
        self.status_label["fg"] = "#000000"
        self.status_label["bg"] = self.bkg_color
        self.runid_label["text"] = "Run ID: "+ inputOptions["runid"]

        self.update_idletasks()
        runnerSetup = {
                                "executable": "femb_adc_setup_board",
                                "argstr": "-j {paramfile}",
                                "basedir": self.data_base_dir,
                                "rundir": "/home/{linux_username}/run",
                                "datadir": "{basedir}/{linux_username}/adcasic/{femb_config_name}/{timestamp}",
                                "paramfile": "{datadir}/setup_params_try{iTry}.json",
                                "outfilename": "{datadir}/adcSetup_{timestamp}_try{iTry}.json",
                                "smtname": "adc",
                                "smttag": "{hostname}",
                                "power_on": power_on,
                                "power_off": power_off,
                                "iTry": self.iTry_configure,
                            }
        self.iTry_configure += 1
        #runner = DirectRunner(**runnerSetup)
        runner = SumatraRunner(**runnerSetup)
        try:
            if GUITESTMODE:
                params = runner.resolve(**inputOptions) # use to test GUI w/o running test
            else:
                params = runner(**inputOptions)
        except RuntimeError:
            self.status_label["text"] = "Error setting up board/ADC. Try again."
            self.status_label["fg"] = "#FFFFFF"
            self.status_label["bg"] = "#FF0000"
            return
        else:
            self.done_preparing_board(params)
            
    def reconfigure_board(self):
        self.prepare_board(power_cycle=False)

    def start_david_adams(self):
        inputOptions = self.get_options(getCurrent=True)
        if inputOptions is None:
            print("ENTER REQUIRED INFO")
            self.status_label["text"] = "ENTER FLOAT FOR CURRENT"
            self.status_label["fg"] = "#FF0000"
            self.status_label["bg"] = self.bkg_color
            return
        if self.waveform_window:
            self.waveform_window.destroy()
        for iWin in reversed(range(len(self.waveform_root_windows))):
            win = self.waveform_root_windows.pop(iWin)
            win.destroy()
        self.waveform_root_viewers = []
        if not GUITESTMODE:
            self.config.FUNCGENINTER.stop()
        self.current_label["state"] = "disabled"
        self.current_entry["state"] = "disabled"
        self.start_button["state"] = "disabled"
        self.start_david_adams_button["state"] = "disabled"
        self.prepare_button["state"] = "disabled"
        self.prepare_button["bg"] = self.bkg_color
        self.prepare_button["activebackground"] = self.activebkg_color
        self.reconfigure_button["state"] = "disabled"
        self.coolboard_label["text"] = ""
        self.retry_david_adams_label["text"] = ""
        self.resetwaveform_button["state"] = "disabled"
        self.selectSocket_label["state"] = "disabled"
        self.selectSocket_entry["state"] = "disabled"
        self.selectChannel_label["state"] = "disabled"
        self.selectChannel_entry["state"] = "disabled"
        self.selectChannel_button["state"] = "disabled"
        self.selectChannel_result["text"] = ""

        print("BEGIN DAVID ADAMS")
        self.status_label["text"] = "COLLECT DAVID ADAMS IN PROGRESS..."
        self.status_label["fg"] = "#000000"
        self.status_label["bg"] = self.bkg_color
        self.update_idletasks()

        runnerSetup = {
                                "executable": "femb_adc_run_david_adams_only",
                                "argstr": "-j {paramfile}",
                                "basedir": self.data_base_dir,
                                "rundir": "/home/{linux_username}/run",
                                "datadir": "{basedir}/{linux_username}/adcasic/{femb_config_name}/{timestamp}",
                                "paramfile": "{datadir}/david_adams_only_params_try{iTry}.json",
                                "smtname": "adc",
                                "smttag": "{hostname}",
                                "iTry": self.iTry_david_adams,
                            }
        self.iTry_david_adams += 1
        runner = SumatraRunner(**runnerSetup)
        try:
            if GUITESTMODE:
                params = runner.resolve(**inputOptions) # use to test GUI w/o running test
            else:
                params = runner(**inputOptions)
        except RuntimeError:
            self.status_label["text"] = "Error in david adams only program. Try again"
            self.status_label["fg"] = "#FFFFFF"
            self.status_label["bg"] = "#FF0000"
            return
        else:
            self.done_david_adams(params)

    def start_measurements(self):
        inputOptions = self.get_options(getCurrent=True)
        if inputOptions is None:
            print("ENTER REQUIRED INFO")
            self.status_label["text"] = "ENTER FLOAT FOR CURRENT"
            self.status_label["fg"] = "#FF0000"
            self.status_label["bg"] = self.bkg_color
            return
        if self.waveform_window:
            self.waveform_window.destroy()
        for iWin in reversed(range(len(self.waveform_root_windows))):
            win = self.waveform_root_windows.pop(iWin)
            win.destroy()
        self.waveform_root_viewers = []
        if not GUITESTMODE:
            self.config.FUNCGENINTER.stop()
        self.current_label["state"] = "disabled"
        self.current_entry["state"] = "disabled"
        self.start_button["state"] = "disabled"
        self.start_david_adams_button["state"] = "disabled"
        self.prepare_button["state"] = "disabled"
        self.prepare_button["bg"] = self.bkg_color
        self.prepare_button["activebackground"] = self.activebkg_color
        self.reconfigure_button["state"] = "disabled"
        self.coolboard_label["text"] = ""
        self.retry_david_adams_label["text"] = ""
        self.resetwaveform_button["state"] = "disabled"
        self.selectSocket_label["state"] = "disabled"
        self.selectSocket_entry["state"] = "disabled"
        self.selectChannel_label["state"] = "disabled"
        self.selectChannel_entry["state"] = "disabled"
        self.selectChannel_button["state"] = "disabled"
        self.selectChannel_result["text"] = ""
        
        print("BEGIN TESTS")
        self.status_label["text"] = "TESTS IN PROGRESS..."
        self.status_label["fg"] = "#000000"
        self.status_label["bg"] = self.bkg_color
        self.update_idletasks()

        runnerSetup = {
                                "executable": "femb_adc_run",
                                "argstr": "-j {paramfile}",
                                "basedir": self.data_base_dir,
                                "rundir": "/home/{linux_username}/run",
                                "datadir": "{basedir}/{linux_username}/adcasic/{femb_config_name}/{timestamp}",
                                "paramfile": "{datadir}/params.json",
                                "smtname": "adc",
                                "smttag": "{hostname}",
                                "nTries_david_adams_only": self.iTry_david_adams-1,
                                "nTries_configure": self.iTry_configure-1,
                            }
        #runner = DirectRunner(**runnerSetup)
        runner = SumatraRunner(**runnerSetup)
        try:
            if GUITESTMODE:
                params = runner.resolve(**inputOptions) # use to test GUI w/o running test
            else:
                params = runner(**inputOptions)
        except RuntimeError:
            self.status_label["text"] = "Error in test program. Copy output to elog"
            self.status_label["fg"] = "#FFFFFF"
            self.status_label["bg"] = "#FF0000"
            if not GUITESTMODE:
                self.config.POWERSUPPLYINTER.off()
            return
        else:
            if not GUITESTMODE:
                self.config.POWERSUPPLYINTER.off()
            self.done_measuring(params)

    def done_preparing_board(self,params):
        ## once prepared....
        print("BOARD POWERED UP & INITIALIZED")
        datadir = params["datadir"]
        timestamp = params["timestamp"]
        iTry = params["iTry"]
        outfilename = "adcSetup_{}_try{}.json".format(timestamp,iTry)
        outfilename = os.path.join(datadir,outfilename)
        print(outfilename)
        resultdict = None
        try:
            with open(outfilename) as outfile:
                resultdict = json.load(outfile)
        except FileNotFoundError:
            if not GUITESTMODE:
                self.status_label["text"] = "Error: Board setup output not found. Copy output to elog"
                self.status_label["fg"] = "#FFFFFF"
                self.status_label["bg"] = "#FF0000"
                #self.config.POWERSUPPLYINTER.off()
                return
            else:
                resultdict = {"pass":True}
                #resultdict = {"pass":False}
        print("done_preparing_board result:")
        pprint.pprint(resultdict)
        titles_made = False
        testNames = None
        columnbase = 0
        rowbase = 150
        for iSocket in range(self.config.NASICS):
            serial = resultdict["serials"][iSocket]
            theseTestNames = ["configADC","configFE","sync","havetofindsync"]
            if titles_made:
                assert(theseTestNames == testNames)
            else:
                testNames = theseTestNames
                label = Label(self, text="Setup Step",anchor=W)
                label.grid(row=rowbase,column=columnbase)
                self.result_labels.append(label)
            label = Label(self, text=serial)
            label.grid(row=rowbase,column=columnbase+2+iSocket)
            self.result_labels.append(label)
            # overall pass fail
            if resultdict["pass"][iSocket]:
                label = Label(self, text="PASS",bg="#00CC00")
                label.grid(row=rowbase+2,column=columnbase+2+iSocket)
                self.result_labels.append(label)
            else:
                label = Label(self, text="FAIL",bg="#FF0000")
                label.grid(row=rowbase+2,column=columnbase+2+iSocket)
                self.result_labels.append(label)
            label = Label(self, text="") # just to put a blank space
            label.grid(row=rowbase+3,column=columnbase+2+iSocket)
            self.result_labels.append(label)
            # board test:
            if iSocket == 0:
                for iTest, test in enumerate(["readReg","init"]):
                    label = Label(self, text="Board")
                    label.grid(row=rowbase,column=columnbase+1)
                    self.result_labels.append(label)
                    if not titles_made:
                        label = Label(self, text=test,anchor=E,justify=LEFT)
                        label.grid(row=rowbase+iTest+5,column=columnbase)
                        self.result_labels.append(label)
                    color = "#FF0000"
                    text = "FAIL"
                    if resultdict[test] is None:
                        color = self.bkg_color
                        text = "NULL"
                    elif resultdict[test]:
                        color = "#00CC00"
                        text = "OK"
                    label = Label(self, text=text,width=4,bg=color)
                    label.grid(row=rowbase+iTest+5,column=columnbase+1)
                    self.result_labels.append(label)
            # individual ASIC tests:
            for iTest, test in enumerate(testNames):
                testPassed = resultdict[test][iSocket]
                if test == "havetofindsync":
                    test = "Had to resync"
                if not titles_made:
                    label = Label(self, text=test,anchor=E,justify=LEFT)
                    label.grid(row=rowbase+iTest+15,column=columnbase)
                    self.result_labels.append(label)
                color = "#FF0000"
                text = "FAIL"
                if testPassed is None:
                    color = self.bkg_color
                    text = "NULL"
                elif testPassed:
                    color = "#00CC00"
                    text = "OK"
                if test == "Had to resync":
                    if testPassed is None:
                        pass
                    elif testPassed:
                        color = "#FF9900"
                        text = "Yes"
                    else:
                        color = "#00CC00"
                        text = "No"
                label = Label(self, text=text,width=4,bg=color)
                label.grid(row=rowbase+iTest+15,column=columnbase+2+iSocket)
                self.result_labels.append(label)
            titles_made = True

        anyPass = False
        for chipPass in resultdict["pass"]:
            if chipPass:
                anyPass = True
                break
        if anyPass:
            self.current_label["state"] = "normal"
            self.current_entry["state"] = "normal"
            self.status_label["text"] = "Power up success, enter CH2 Current"
            self.status_label["fg"] = "#000000"
            self.status_label["bg"] = self.bkg_color
            self.prepare_button["state"] = "normal"
            self.prepare_button["text"] = "Re-"+self.prepare_button_text+"\n(Creates New Timestamp)"
            self.prepare_button["bg"] ="#FF9900"
            self.prepare_button["activebackground"] ="#FFCF87"
            self.reconfigure_button["state"] = "normal"
            self.coolboard_label["text"] = "If waveform looks okay, \nbegin cooling board \n(see shifter instructions)"
            self.retry_david_adams_label["text"] = ""
            self.start_button["state"] = "normal"
            self.start_david_adams_button["state"] = "normal"
            self.operator_label["state"] = "disabled"
            self.operator_entry["state"] = "disabled"
            self.boardid_label["state"] = "disabled"
            self.boardid_entry["state"] = "disabled"
            self.reset_button["bg"] ="#FF9900"
            self.reset_button["activebackground"] ="#FFCF87"
            self.resetwaveform_button["state"] = "normal"
            self.selectSocket_label["state"] = "normal"
            self.selectSocket_entry["state"] = "normal"
            self.selectChannel_label["state"] = "normal"
            self.selectChannel_entry["state"] = "normal"
            self.selectChannel_button["state"] = "normal"
            self.selectChannel_result["text"] = ""
            for i in range(self.config.NASICS):
                self.asic_labels[i]["state"] = "disabled"
                self.asic_entries[i]["state"] = "disabled"
            if not GUITESTMODE:
                self.config.FUNCGENINTER.startSin(1000,0.6,0.7)
            self.reset_waveform_viewer()
        else:
            columnbase = 0
            rowbase = 500
            label = Label(self, text="FAIL to setup board",bg="#FF0000")
            label.grid(row=rowbase+2,column=columnbase,columnspan=2)
            self.result_labels.append(label)
            label = Label(self, text="Try re-setup board",bg="#FF0000")
            label.grid(row=rowbase+3,column=columnbase,columnspan=2)
            self.result_labels.append(label)
            self.prepare_button["state"] = "normal"
            self.prepare_button["text"] = "Re-"+self.prepare_button_text+"\n(Creates New Timestamp)"
            self.prepare_button["bg"] ="#00CC00"
            self.prepare_button["activebackground"] = "#A3CCA3"
            self.reconfigure_button["state"] = "normal"
            self.reset_button["bg"] ="#FF9900"
            self.reset_button["activebackground"] ="#FFCF87"
            
    def done_david_adams(self,params):
        print("David Adams COMPLETE")
        self.status_label["text"] = "Collect David Adams data done"
        self.status_label["fg"] = "#000000"
        self.status_label["bg"] = self.bkg_color
        datadir = params["datadir"]
        timestamp = params["timestamp"]
        iTry = params["iTry"]
        outfilenames = []
        if GUITESTMODE:
            outfilenames = ["/home/jhugon/dune/coldelectronics/femb_python/test0.root"]
        else:
            outfileglob = "adcDavidAdamsOnlyData_{}_*_try{}.root".format(timestamp,iTry)
            outfileglob = os.path.join(datadir,outfileglob)
            print(outfileglob)
            outfilenames = glob.glob(outfileglob)
        print(outfilenames)
        if len(outfilenames) != self.config.NASICS:
            self.status_label["text"] = "Error: Test output not found.\nTry again and/or reconfiguring"
            self.status_label["fg"] = "#FFFFFF"
            self.status_label["bg"] = "#FF0000"

            self.prepare_button["state"] = "normal"
            self.prepare_button["text"] = "Re-"+self.prepare_button_text+"\n(Creates New Timestamp)"
            self.prepare_button["bg"] ="#FF9900"
            self.prepare_button["activebackground"] ="#FFCF87"
            self.reconfigure_button["state"] = "normal"
            self.start_button["state"] = "normal"
            self.start_david_adams_button["state"] = "normal"
        else: # good
            self.prepare_button["state"] = "normal"
            self.prepare_button["text"] = "Re-"+self.prepare_button_text+"\n(Creates New Timestamp)"
            self.prepare_button["bg"] ="#FF9900"
            self.prepare_button["activebackground"] ="#FFCF87"
            self.reconfigure_button["state"] = "normal"
            self.start_button["state"] = "normal"
            self.start_david_adams_button["state"] = "normal"
            self.retry_david_adams_label["text"] = 'If displayed waveform looks like\n5-8 pretty good ramps up\nand down, press "Start Tests", else\ntry to collect David Adams data again'
            for iWin in reversed(range(len(self.waveform_root_windows))):
                win = self.waveform_root_windows.pop(iWin)
                win.destroy()
            self.waveform_root_viewers = []
            for outfilename in outfilenames:
                win = Toplevel(self)
                win.title("David Adams Data Window")
                try:
                    viewer = TRACE_ROOT_WINDOW(outfilename,master=win,fullADCRange=True)
                except Exception as e:
                    win.destroy()
                    self.status_label["text"] = "Error while displaying David Adams only data.\nTry again and/or reconfiguring"
                    self.status_label["fg"] = "#FFFFFF"
                    self.status_label["bg"] = "#FF0000"

                    self.prepare_button["state"] = "normal"
                    self.prepare_button["text"] = "Re-"+self.prepare_button_text+"\n(Creates New Timestamp)"
                    self.prepare_button["bg"] ="#FF9900"
                    self.prepare_button["activebackground"] ="#FFCF87"
                    self.reconfigure_button["state"] = "normal"
                    self.start_button["state"] = "normal"
                    self.start_david_adams_button["state"] = "normal"
                    print("GUI Error: uncaught exception while displaying David Adams only file. There may be something wrong with the David Adams only data.")
                    print("Uncaught exception in GUI: Error: {} {}\n".format(type(e),e))
                    traceback.print_tb(e.__traceback__)
                else:
                    self.waveform_root_windows.append(win)
                    self.waveform_root_viewers.append(viewer)

    def done_measuring(self,params):
        print("TESTS COMPLETE")
        self.status_label["text"] = "Tests done"
        self.status_label["fg"] = "#000000"
        self.status_label["bg"] = self.bkg_color
        self.reset_button["bg"] ="#00CC00"
        self.reset_button["activebackground"] = "#A3CCA3"
        datadir = params["datadir"]
        timestamp = params["timestamp"]
        #datadir = "/home/jhugon/data/adc/hothdaq4/olddata/2017-06-02T14:24:54"
        #timestamp = "2017-06-02T14:24:54"
        #datadir = "/home/jhugon/data/adc/hothdaq3/Data/2017-06-08T13:04:41"
        #timestamp = "2017-06-08T13:04:41"
        outfileglob = "adcTest_{}_*.json".format(timestamp)
        outfileglob = os.path.join(datadir,outfileglob)
        #print(outfileglob)
        outfilenames = glob.glob(outfileglob)
        print(outfilenames)
        if len(outfilenames) != self.config.NASICS:
            self.status_label["text"] = "Error: Test output not found. Copy output to elog"
            self.status_label["fg"] = "#FFFFFF"
            self.status_label["bg"] = "#FF0000"
            return
        titles_made = False
        testNames = None
        columnbase = 0
        rowbase = 500
        for iCol,outfilename in enumerate(sorted(outfilenames)):
            data = None
            with open(outfilename) as outfile:
                data = json.load(outfile)
            results = data["testResults"]
            serial = data["serial"]
            theseTestNames = sorted(list(results.keys()))
            theseTestNames.pop(theseTestNames.index("pass")) # don't want in list
            if titles_made:
                assert(theseTestNames == testNames)
            else:
                testNames = theseTestNames
                label = Label(self, text="Test",anchor=W)
                label.grid(row=rowbase,column=columnbase)
                self.result_labels.append(label)
            label = Label(self, text=serial)
            label.grid(row=rowbase,column=columnbase+1+iCol)
            self.result_labels.append(label)
            # overall pass fail
            if results["pass"]:
                label = Label(self, text="PASS",bg="#00CC00")
                label.grid(row=rowbase+2,column=columnbase+1+iCol)
                self.result_labels.append(label)
            else:
                label = Label(self, text="FAIL",bg="#FF0000")
                label.grid(row=rowbase+2,column=columnbase+1+iCol)
                self.result_labels.append(label)
            label = Label(self, text="") # just to put a blank space
            label.grid(row=rowbase+3,column=columnbase+1+iCol)
            self.result_labels.append(label)
            # individual tests:
            for iTest, test in enumerate(testNames):
                if not titles_made:
                    label = Label(self, text=test,anchor=E,justify=LEFT)
                    label.grid(row=rowbase+iTest+5,column=columnbase)
                    self.result_labels.append(label)
                color = "#FF0000"
                text = "FAIL"
                if results[test]:
                    color = "#00CC00"
                    text = "OK"
                label = Label(self, text=text,width=4,bg=color)
                label.grid(row=rowbase+iTest+5,column=columnbase+1+iCol)
                self.result_labels.append(label)
            titles_made = True
        imgfileglob = "adcTest_{}_*.png".format(timestamp)
        imgfileglob = os.path.join(datadir,imgfileglob)
        print(imgfileglob)
        imgfilenames = glob.glob(imgfileglob)
        print(imgfilenames)
        for imgfilename in imgfilenames:
            self.display_procs.append(subprocess.Popen(["eog",imgfilename]))

    def reset_waveform_viewer(self):
        self.select_all_channels()
        if self.waveform_window:
          self.waveform_window.destroy()
        self.waveform_window = Toplevel(self)
        self.waveform_window.title("Trace All Channel Window")
        self.waveform_viewer = TRACE_ALLCHAN_WINDOW(self.waveform_window)

    def call_selectChannel(self):
        asic = None
        chan = None
        if self.config.NASICS == 1:
            asic = 0
        else:
            try:
              asic = int(self.selectSocket_entry.get())
            except ValueError:
              self.selectChannel_result["text"] = "Error asic must be an int"
              return
        try:
          chan = int(self.selectChannel_entry.get())
        except ValueError:
          self.selectChannel_result["text"] = "Error channel must be an int"
          return
        message = ""
        if asic < 0 or asic >= self.config.NASICS:
          self.selectChannel_result["text"] = "Error asic only from 0 to {}".format(self.config.NASICS - 1)
          return
        if chan < 0 or chan >= 16:
          self.selectChannel_result["text"] = "Error channel only from 0 to 15"
          return
        self.config.selectChannel(asic,chan)
        self.selectChannel_result["text"] = ""
        
    def select_all_channels(self):
        asic = None
        if self.config.NASICS == 1:
            asic = 0
        else:
            try:
                asic = int(self.selectSocket_entry.get())
            except ValueError:
                self.selectChannel_result["text"] = "Error asic must be an int"
                return
        self.config.selectChannel(asic,0,0)

    def exit(self,*args, **kargs):
        if not GUITESTMODE:
            self.config.POWERSUPPLYINTER.off()
        for i in reversed(range(len(self.display_procs))):
            tmp = self.display_procs.pop(i)
            tmp.terminate()
            try:
                tmp.wait(4)
            except subprocess.TimeoutExpired:
                tmp.kill()
            del tmp
        self.destroy()
        self.master.destroy()

def main():
    from ...configuration.argument_parser import ArgumentParser

    parser = ArgumentParser(description="ADC cold test GUI")
    parser.add_argument("-l","--forceLong",help="Force to run over all ADC offset current settings (normally doesn't)",action="store_true")
    args = parser.parse_args()

    print("Using femb_python:",os.path.dirname(femb_python.__file__))

    root = Tk()
    root.title("ADC Cold Test GUI")
    window = GUI_WINDOW(root,forceLong=args.forceLong)
    root.mainloop() 
