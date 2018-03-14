"""
FEMB Test Stand GUI
Copied and modified from J.Hugon ADC gui by ETW
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
from time import sleep
from tkinter import *
import subprocess

#import the test module
import femb_python
from femb_python.configuration import CONFIG # adc_clock_test
from femb_python.configuration.argument_parser import ArgumentParser
from femb_python.test_measurements.adc_clock_test.run_main import main as run_main
from femb_python.test_measurements.adc_clock_test.user_settings import user_editable_settings
settings = user_editable_settings()

class GUI_WINDOW(Frame):

    #GUI window defined entirely in init function
    def __init__(self, master=None,forceQuick=False,forceLong=False):
        Frame.__init__(self,master)
        self.pack()

        self.config = CONFIG()

        self.result_labels = []
        self.display_procs = []
        #Define general commands column
        self.define_test_details_column()
        self.reset()

        self.master.protocol("WM_DELETE_WINDOW", self.exit)

    def define_test_details_column(self):
        columnbase=0
        """
        # Adding operator name label and read entry box
        self.operator_label = Label(self,text="Operator Name:",width=25)
        self.operator_label.grid(sticky=W,row=1,column=columnbase+0)

        self.operator_entry = Entry(self,width=25)
        self.operator_entry.grid(sticky=W,row=1,column=columnbase+1)

        # Adding electronics ID and read entry box
        self.boxid_label = Label(self,text="Electronics ID:",width=25)
        self.boxid_label.grid(sticky=W,row=3,column=columnbase+0)

        self.boxid_entry = Entry(self,width=25)
        self.boxid_entry.grid(sticky=W,row=3,column=columnbase+1)
        """
        # Adding electronics ID and read entry box
        self.sync_button = Button(self, text="Sync ADC", command=self.adc_sync,width=25)
        self.sync_button.grid(row=22,column=columnbase,columnspan=2,pady=30)

        #
        self.reset_button = Button(self, text="Reset", command=self.reset,width=25,bg="#FF8000")
        self.reset_button.grid(row=24,column=columnbase,columnspan=2)

        self.runid_label = Label(self, text="")
        self.runid_label.grid(row=25,column=columnbase,columnspan=2,pady=20)

        self.status_label = Label(self, text="NOT STARTED",bd=1,relief=SUNKEN,width=50)
        self.status_label.grid(row=100,column=columnbase,columnspan=2)
        self.bkg_color = self.status_label.cget("background")
    """
    def get_options(self,getCurrent=False):
        operator = self.operator_entry.get()
        boxid = self.boxid_entry.get()

        variables = [operator,boxid]
        for var in variables:
            if var == "" :
                return
        print("Operator Name: '{}'".format(operator))
        print("CE Box ID: '{}'".format(boxid))

        inputOptions = {
            "operator": operator,
            "box_id": boxid,
        }
        print(inputOptions)
        return inputOptions
    """
    def reset(self):
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
        self.sync_button["state"] = "normal"
        #self.operator_label["state"] = "normal"
        #self.operator_entry["state"] = "normal"
        #self.boxid_label["state"] = "normal"
        #self.boxid_entry["state"] = "normal"

        #self.boxid_entry.delete(0,END)
        
        self.reset_button["bg"] ="#FF9900"
        self.reset_button["activebackground"] ="#FFCF87"

    def adc_sync(self):
        #operator_name = self.operator_entry.get()
        #test_stand = self.test_stand_entry.get()
        #boardid = self.boardid_entry.get()
        #traveller = self.traveller_entry.get()
        #print("Operator Name: " + str( operator_name ) )
        #print("Test Stand # : " + str( test_stand ) )
        #print("Board/Chip ID: " + str( boardid ) )
        #print("Traveller #  : " + str( traveller ) )
      
        self.config.femb.init_ports(hostIP = settings.PC_IP, destIP = settings.FPGA_IP)
        self.config.resetFEMBBoard()
        self.config.initBoard()   
        self.config.syncADC()
        #self.config.initFunctionGenerator()
        """
        if self.femb_test.status_check_setup == 0:
            self.check_setup_result["text"] = "TERRIBLE FAILURE"
        else:
            self.check_setup_result["text"] = "SUCCESS"
        """
    """
    def start_measurements(self):
        params = self.get_options()
        if params is None:
            print("ENTER REQUIRED INFO")
            return

        print("BEGIN TESTS")
        self.status_label["text"] = "TESTS IN PROGRESS..."
        self.status_label["fg"] = "#000000"
        self.update_idletasks()
        run_main(self.config,**params)
        self.done_measuring(params)
    """        
    def done_measuring(self,params):
        print("TESTS COMPLETE")
        self.status_label["text"] = "Tests done"
        self.reset_button["bg"] ="#00CC00"
        self.reset_button["activebackground"] = "#A3CCA3"
        titles_made = False
        testNames = None
        columnbase = 0
        rowbase = 50

    def exit(self,*args, **kargs):
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

    parser = ArgumentParser(description="ADC CLOCK GUI")

    args = parser.parse_args()

    root = Tk()
    root.title("ADC GUI")
    window = GUI_WINDOW(root)
    root.mainloop() 

if __name__ == '__main__':
    main()
