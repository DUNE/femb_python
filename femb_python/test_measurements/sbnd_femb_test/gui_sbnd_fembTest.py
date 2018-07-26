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
from tkinter import *
import json

import os                                 # for statv
import os.path
import time
import getpass                            # for getuser

#import the test module
#from femb_python.test_measurements.feAsicTest.doFembTest_simpleMeasurement import FEMB_TEST_SIMPLE
#from femb_python.test_measurements.feAsicTest.doFembTest_gainMeasurement import FEMB_TEST_GAIN

import femb_python
from femb_python import runpolicy

class GUI_WINDOW(Frame):

    # defaults
    use_sumatra = True
    datadisks = ["/dsk/1", "/dsk/2"]
    femb_config = "sbnd_quadFeAsic_cold"               # aka FEMB_CONFIG env var

    #GUI window defined entirely in init function
    def __init__(self, master=None):

        femb_config = os.environ['FEMB_CONFIG']

        Frame.__init__(self,master)
        self.pack()

        #Define general commands column
        self.define_test_details_column()

        #Define general commands column
        self.define_general_commands_column()
        #list of board IDs with known phase settings in config file
        self.knownBoardIDs = ['1v0','2v0','3v0']
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
            operator_name = "",
            test_stand = "",
            boardid = "",
            asic0id = "",
            asic1id = "",
            asic2id = "",
            asic3id = "",
            test_category = "sbnd_feasic",
            test_version = "1",
            femb_config = femb_config,
            asic_pass = [[-1,-1,-1],[-1,-1,-1],[-1,-1,-1],[-1,-1,-1]], #results for each test
            config_list = [0,1,0,0], #update if any sockets fail configuration stage
            power_ready = 0
        )
        self.save_sync_results = True
        # Check out the data disk situation and find the most available disk
        freedisks = list()
        for dd in self.datadisks:
            stat = os.statvfs(dd)
            MB = stat.f_bavail * stat.f_frsize >> 20
            freedisks.append((MB, dd))
        freedisks.sort()
        self.params["lo_disk"] = freedisks[0][1]
        self.params["hi_disk"] = freedisks[-1][1]

        now = time.time()
        self.params["session_start_time"] = time.strftime("%Y%m%dT%H%M%S", time.localtime(now))
        self.params["session_start_unix"] = now

        # some hothdaq disk policy, only "oper" gets to write to /dsk/N/data/
        username = getpass.getuser()
        if username == "oper":
            datadisk = "{lo_disk}/data"
        else:
            datadisk = "{lo_disk}/tmp"

        cold = None
        try:
            cold = self.config.COLD
        except AttributeError:
            cold = None
        # these are needed for runpolicy Runner
        self.params.update(

            user = username,
            hostname = os.uname()[1],
            datadisk = datadisk,

            # The rundir is where each individual job starts and should be
            # shared by all jobs.  For Sumatra controlled running this
            # directory houses the .smt/ subdirectory
            rundir = "/home/{user}/run",
            
            # The data dir is where the output of each job should go.  This
            # should be made unique every job.
            datadir = "{datadisk}/{user}/{test_category}/{femb_config}/{session_start_time}",
            root_path = "{datadisk}/{user}/{test_category}/{femb_config}",
            # This is the file where all these parameters get written
            # after variables are resovled.  This file is made
            # available to the measurement script.  It's a JSON file.
            paramfile = "{datadir}/params.json",

            # This is some "project" name needed by Sumatra
            smtname = "{test_category}",

            smttag = "{hostname},{datadisk}",

            # We can get the femb_python version out of this
            femb_python_location = os.path.dirname(femb_python.__file__),
            # Is this a cold test?
            cold = cold,
            );


        # make a runner to enforce consistent run policy for each time an
        # actual measurement scripts is executed.  Prime with parameters as
        # they are known up to know.  They will be overridden and augmented
        # when the runner is called.
        if self.use_sumatra:
            print ("Using Sumatra")
            pghost = os.environ.get("PGHOST")
            if pghost:
                print (" with PostgreSQL database at %s" % pghost)
                self.params.update(
                    smtstore="postgres://{pguser}@{pghost}/{pgdatabase}",
                    pguser = os.environ['PGUSER'],
                    pghost = os.environ['PGHOST'],
                    pgdatabase = os.environ['PGDATABASE'],
                )
            else:
                print (" with Sqlite3 database in rundir")

            self.runner = runpolicy.SumatraRunner(**self.params)

        else:
            self.runner = runpolicy.DirectRunner(**self.params)
            
        
        return

    def define_test_details_column(self):
        columnbase=0

        label = Label(self, text="Tests Details")
        label.grid(row=0,column=columnbase, columnspan=50)

        # Adding operator name label and read entry box
        label = Label(self,text="Operator Name:",width=25)
        label.grid(sticky=W,row=1,column=columnbase+0)

        self.operator_entry = Entry(self,width=25)
        self.operator_entry.grid(sticky=W,row=1,column=columnbase+1)

        # Adding test stand ID and read entry box
        label = Label(self,text="Test Stand #:",width=25)
        label.grid(sticky=W,row=2,column=columnbase+0)

        self.test_stand_entry = Entry(self,width=25)
        self.test_stand_entry.grid(sticky=W,row=2,column=columnbase+1)

        # Adding electronics ID and read entry box
        label = Label(self,text="Test Board ID:",width=25)
        label.grid(sticky=W,row=3,column=columnbase+0)

        self.boardid_entry = Entry(self,width=25)
        self.boardid_entry.grid(sticky=W,row=3,column=columnbase+1)

        # ASIC 0 ID
        label = Label(self,text="ASIC 0 ID:",width=25)
        label.grid(sticky=W,row=7,column=columnbase+0)

        self.asic0_entry = Entry(self, width=25)
        self.asic0_entry.grid(sticky=W,row=7,column=columnbase+1)

        # ASIC 1 ID
        label = Label(self,text="ASIC 1 ID:",width=25)
        label.grid(sticky=W,row=8,column=columnbase+0)

        self.asic1_entry = Entry(self,width=25)
        self.asic1_entry.grid(sticky=W,row=8,column=columnbase+1)

        # ASIC 2 ID
        label = Label(self,text="ASIC 2 ID:",width=25)
        label.grid(sticky=W,row=9,column=columnbase+0)

        self.asic2_entry = Entry(self,width=25)
        self.asic2_entry.grid(sticky=W,row=9,column=columnbase+1)

        # ASIC 3 ID
        label = Label(self,text="ASIC 3 ID:",width=25)
        label.grid(sticky=W,row=10,column=columnbase+0)

        self.asic3_entry = Entry(self,width=25)
        self.asic3_entry.grid(sticky=W,row=10,column=columnbase+1)                      


    def define_general_commands_column(self):
        columnbase=50

        label = Label(self, text="FE ASIC TESTS")
        label.grid(row=0,column=columnbase, columnspan=50)

        self.load_button = Button(self, text="Load ASICs", bg="red", command=self.load_asics,width=25)
        self.load_button.grid(row=1,column=columnbase,columnspan=25)

        self.load_button_result = Label(self, text="Press Load ASICs before loading",width=25)
        self.load_button_result.grid(sticky=W,row=1,column=columnbase+25,columnspan=25)
        
        self.start_button = Button(self, text="Start Tests", command=self.start_measurements,width=25)
        self.start_button.grid(row=2,column=columnbase,columnspan=25)

        self.start_button_result = Label(self, text="NOT STARTED",width=25)
        self.start_button_result.grid(sticky=W,row=2,column=columnbase+25,columnspan=25)
        
        self.save_results_button = Button(self, text="Save Sync Results", bg="green", command=self.save_sync_results_function ,width=25)
        self.save_results_button.grid(row=5,column=columnbase+9,columnspan=25)

        #Adding the record data button
        #record_data_button = Button(self, text="Record Data", command=self.record_data,width=25)
        #record_data_button.grid(row=2,column=columnbase,columnspan=25)

#        self.check_setup_result = Label(self, text="CHECK SETUP - NOT STARTED",width=50)
#        self.check_setup_result.grid(sticky=W,row=3,column=columnbase,columnspan=50)

        self.sync_adcs_sequence_result = Label(self, text="SYNCHRONIZING ADCS - NOT STARTED",width=50)
        self.sync_adcs_sequence_result.grid(sticky=W,row=3,column=columnbase,columnspan=50)

        self.baseline_test_sequence_result = Label(self, text="BASELINE TEST - NOT STARTED",width=50)
        self.baseline_test_sequence_result.grid(sticky=W,row=4,column=columnbase,columnspan=50)

        self.monitor_data_test_sequence_result = Label(self, text="MONITOR DATA TEST - NOT STARTED",width=50)
        self.monitor_data_test_sequence_result.grid(sticky=W,row=5,column=columnbase,columnspan=50)

        self.input_alive_power_cycle_sequence_result = Label(self, text="INPUT ALIVE POWER CYCLE TEST - NOT STARTED",width=50)
        self.input_alive_power_cycle_sequence_result.grid(sticky=W,row=6,column=columnbase,columnspan=50)
        
        self.result_label = Label(self, text="", width=25)
        self.result_label.grid(sticky=W,row=8,column=columnbase+2)        
        self.baseline_result_label = Label(self, text="BASELINE", width=10)
        self.baseline_result_label.grid(sticky=W, row=7, column=columnbase+3)        
        self.monitor_result_label = Label(self, text="MONITOR", width=10)
        self.monitor_result_label.grid(sticky=W, row=7, column=columnbase+4)        
        self.alive_result_label = Label(self, text="ALIVE", width=10)
        self.alive_result_label.grid(sticky=W, row=7, column=columnbase+5)
        self.final_result_label = Label(self, text="FINAL", width=10)
        self.final_result_label.grid(sticky=W, row=7, column=columnbase+6)
        
        self.asic0_result = Label(self, text="ASIC 0 Results:", width=25)
        self.asic0_result.grid(sticky=W,row=8,column=columnbase+2)        
        self.asic0_baseline_result = Label(self, text="TBD", width=10)
        self.asic0_baseline_result.grid(sticky=W, row=8, column=columnbase+3)        
        self.asic0_monitor_result = Label(self, text="TBD", width=10)
        self.asic0_monitor_result.grid(sticky=W, row=8, column=columnbase+4)        
        self.asic0_alive_result = Label(self, text="TBD", width=10)
        self.asic0_alive_result.grid(sticky=W, row=8, column=columnbase+5)
        self.asic0_final_result = Label(self, text="TBD", width=10)
        self.asic0_final_result.grid(sticky=W, row=8, column=columnbase+6)        
        
        self.asic1_result = Label(self, text="ASIC 1 Results:", width=25)
        self.asic1_result.grid(sticky=W,row=9,column=columnbase+2)        
        self.asic1_baseline_result = Label(self, text="TBD", width=10)
        self.asic1_baseline_result.grid(sticky=W, row=9, column=columnbase+3)        
        self.asic1_monitor_result = Label(self, text="TBD", width=10)
        self.asic1_monitor_result.grid(sticky=W, row=9, column=columnbase+4)        
        self.asic1_alive_result = Label(self, text="TBD", width=10)
        self.asic1_alive_result.grid(sticky=W, row=9, column=columnbase+5)
        self.asic1_final_result = Label(self, text="TBD", width=10)
        self.asic1_final_result.grid(sticky=W, row=9, column=columnbase+6)

        self.asic2_result = Label(self, text="ASIC 2 Results:", width=25)
        self.asic2_result.grid(sticky=W,row=10,column=columnbase+2)        
        self.asic2_baseline_result = Label(self, text="TBD", width=10)
        self.asic2_baseline_result.grid(sticky=W, row=10, column=columnbase+3)        
        self.asic2_monitor_result = Label(self, text="TBD", width=10)
        self.asic2_monitor_result.grid(sticky=W, row=10, column=columnbase+4)        
        self.asic2_alive_result = Label(self, text="TBD", width=10)
        self.asic2_alive_result.grid(sticky=W, row=10, column=columnbase+5)
        self.asic2_final_result = Label(self, text="TBD", width=10)
        self.asic2_final_result.grid(sticky=W, row=10, column=columnbase+6)

        self.asic3_result = Label(self, text="ASIC 3 Results:", width=25)
        self.asic3_result.grid(sticky=W,row=11,column=columnbase+2)        
        self.asic3_baseline_result = Label(self, text="TBD", width=10)
        self.asic3_baseline_result.grid(sticky=W, row=11, column=columnbase+3)        
        self.asic3_monitor_result = Label(self, text="TBD", width=10)
        self.asic3_monitor_result.grid(sticky=W, row=11, column=columnbase+4)        
        self.asic3_alive_result = Label(self, text="TBD", width=10)
        self.asic3_alive_result.grid(sticky=W, row=11, column=columnbase+5)
        self.asic3_final_result = Label(self, text="TBD", width=10)
        self.asic3_final_result.grid(sticky=W, row=11, column=columnbase+6)

        #Finish/reset button
        finish_button = Button(self, text="Reset and Power Down",command=self.reset_gui,width=25)
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
        self.params['test_stand'] = self.test_stand_entry.get()
        self.params['boardid'] = self.boardid_entry.get().lower()
        self.params['asic0id'] = self.asic0_entry.get()
        self.params['asic1id'] = self.asic1_entry.get()
        self.params['asic2id'] = self.asic2_entry.get()
        self.params['asic3id'] = self.asic3_entry.get()

        print("""\
Operator Name: {operator_name}
Test Stand # : {test_stand}
Test Board ID: {boardid}
ASIC 0 ID: {asic0id}
ASIC 1 ID: {asic1id}
ASIC 2 ID: {asic2id}
ASIC 3 ID: {asic3id}
        """.format(**self.params))
        
        start_time = time.time()
        self.now = time.strftime("%Y%m%dT%H%M%S", time.localtime(time.time()))
        self.chiplist = [[0,self.params['asic0id']],[1,self.params['asic1id']],[2,self.params['asic2id']],[3,self.params['asic3id']]]

        if (not self.params['power_ready']==1):
            print("PRESS LOAD ASICS FIRST!")
            self.start_button_result["text"] = "PRESS LOAD ASICS FIRST!"
            self.update_idletasks()
            return
        
        if not self.params['operator_name']:
            print("ENTER REQUIRED INFO")
            self.start_button_result["text"] = "ENTER REQUIRED INFO"
            self.update_idletasks()
            return

        print("BEGIN TESTS")
        self.start_button_result["text"] = "IN PROGRESS "+self.params["session_start_time"]
        self.load_button_result["text"] = "Testing - do not remove"
        self.update_idletasks()

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

            try:
                meth()
            except RuntimeError as err:
                print("failed: %s\n%s" % (LOUD, err)) 
                self.start_button_result["text"] = LOUD + " - FAILED "+self.params["session_start_time"]
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
        self.runner(datasubdir="power",executable="femb_control_power", argstr="OFF")
        self.load_button_result["text"] = "Ok to load new ASICs"
        self.update_idletasks()
        self.params['power_ready'] = 1
        self.load_button["bg"]="green"
        
    def save_sync_results_function(self):
        if not self.save_sync_results:
            self.save_sync_results = True       
            self.save_results_button["bg"]="green"
        else:
            self.save_sync_results = False
            self.save_results_button["bg"]="red"

    def reset_gui(self):
        #Power down all 4 chips:
#        self.runner(datasubdir="power",executable="femb_control_power", argstr="OFF")
                              
        self.params['power_ready'] = 0

        #Reset GUI:
#        self.operator_entry.delete(0,1000)
#        self.test_stand_entry.delete(0,1000)
#        self.boardid_entry.delete(0,1000)
        self.asic0_entry.delete(0,1000)
        self.asic1_entry.delete(0,1000)
        self.asic2_entry.delete(0,1000)
        self.asic3_entry.delete(0,1000)
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
        self.save_results_button["bg"] = "green"
        self.load_button["bg"]="red"
        
        self.methodMap['baseline_test_sequence_complete'] = False
        self.methodMap['monitor_data_test_sequence_complete'] = False
        self.methodMap['input_alive_power_cycle_sequence_complete'] = False
        self.save_sync_results = True
        
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
        
        now = time.strftime("%Y%m%dT%H%M%S", time.localtime(time.time()))
        start_time = time.time()
        
        resolved = self.runner(**self.params, 
                    datasubdir="sync_adcs",
                    executable="femb_sync_adcs",
                    test_start_time = self.now,
                    outlabel = "{datasubdir}-{test_start_time}",
                    chip_list = self.chiplist,
                    argstr="{paramfile}",
                    save_results = self.save_sync_results)     
                    
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
                              [2] , [2] , [0,1] , 0 , 0 , 1 , 0 , #expedited cold test
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

def main():
    root = Tk()
    root.title("Quad FE ASIC Test GUI")
    window = GUI_WINDOW(root)
    root.mainloop() 

if __name__ == '__main__':
    main()
