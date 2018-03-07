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
from femb_python.configuration import CONFIG
from femb_python.test_measurements.quadFeTestCold.scripts.femb_udp_cmdline import FEMB_UDP
from femb_python.configuration.argument_parser import ArgumentParser #not sure what this does
#from femb_python.test_measurements.exampleTest.exampleProductionTest import main as maintest	#
from femb_python.test_measurements.quadFeTestCold.run_main_cp import main as maintest           # updated

class GUI_WINDOW(Frame):

    #GUI window defined entirely in init function
    def __init__(self, master=None,forceQuick=False,forceLong=False):
        Frame.__init__(self,master)
        self.pack()

        self.config = CONFIG()
        self.femb_udp = FEMB_UDP()

        self.result_labels = []
        self.display_procs = []
        #Define general commands column
        self.define_test_details_column()
        self.reset()

        self.master.protocol("WM_DELETE_WINDOW", self.exit)

    def define_test_details_column(self):
        columnbase=0

        # Adding operator name label and read entry box
        self.operator_label = Label(self,text="Operator Name:",width=25)	#
        self.operator_label.grid(sticky=W,row=1,column=columnbase+0) 	 	#

        self.operator_entry = Entry(self,width=25)			 	#
        self.operator_entry.grid(sticky=W,row=1,column=columnbase+1)	 	#

        # Adding electronics ID and read entry box
        self.boxid_label_1 = Label(self,text="Socket1: Chip ID:",width=25) 	#
        self.boxid_label_1.grid(sticky=W,row=3,column=columnbase+0) 	 	#
        self.boxid_entry_1 = Entry(self,width=25)				#
        self.boxid_entry_1.grid(sticky=W,row=3,column=columnbase+1)	 	#

        self.boxid_label_2 = Label(self,text="Socket2: Chip ID:",width=25) 	#
        self.boxid_label_2.grid(sticky=W,row=4,column=columnbase+0) 	 	#
        self.boxid_entry_2 = Entry(self,width=25)				#
        self.boxid_entry_2.grid(sticky=W,row=4,column=columnbase+1)	 	#
        
        self.boxid_label_3 = Label(self,text="Socket3: Chip ID:",width=25) 	#
        self.boxid_label_3.grid(sticky=W,row=5,column=columnbase+0) 	 	#
        self.boxid_entry_3 = Entry(self,width=25)				#
        self.boxid_entry_3.grid(sticky=W,row=5,column=columnbase+1)	 	#

        self.boxid_label_4 = Label(self,text="Socket4: Chip ID:",width=25) 	#
        self.boxid_label_4.grid(sticky=W,row=6,column=columnbase+0) 	 	#
        self.boxid_entry_4 = Entry(self,width=25)				#
        self.boxid_entry_4.grid(sticky=W,row=6,column=columnbase+1)	 	#

        # Adding electronics ID and read entry box
        self.start_button = Button(self, text="Start Tests", command=self.start_measurements,width=25)	#
        self.start_button.grid(row=22,column=columnbase,columnspan=2,pady=30)				#
        self.reset_button = Button(self, text="Reset", command=self.reset,width=25,bg="#FF8000")	#
        self.reset_button.grid(row=24,column=columnbase,columnspan=2)					#

        self.runid_label = Label(self, text="")
        self.runid_label.grid(row=25,column=columnbase,columnspan=2,pady=20)

        self.status_label = Label(self, text="NOT STARTED",bd=1,relief=SUNKEN,width=50)
        self.status_label.grid(row=100,column=columnbase,columnspan=2)
        self.bkg_color = self.status_label.cget("background")

    def get_options(self,getCurrent=False):
        operator = self.operator_entry.get()
        boxid_1 = self.boxid_entry_1.get()
        boxid_2 = self.boxid_entry_2.get()
        boxid_3 = self.boxid_entry_3.get()
        boxid_4 = self.boxid_entry_4.get()

        variables = [operator,boxid_1,boxid_2,boxid_3,boxid_4]
        for var in variables:
            if var == "" :
                return
        print("Operator Name: '{}'".format(operator))
        print("Fe ASIC ID1: '{}'".format(boxid_1))
        print("Fe ASIC ID2: '{}'".format(boxid_2))
        print("Fe ASIC ID3: '{}'".format(boxid_3))
        print("Fe ASIC ID4: '{}'".format(boxid_4))
        
        inputOptions = {
            "operator": operator,
            "box_id_1": boxid_1,
            "box_id_2": boxid_2,
            "box_id_3": boxid_3,
            "box_id_4": boxid_4,
        }
        #print(inputOptions)
        return inputOptions

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
        self.start_button["state"] = "normal"
        self.operator_label["state"] = "normal"
        self.operator_entry["state"] = "normal"
        self.boxid_label_1["state"] = "normal"
        self.boxid_entry_1["state"] = "normal"
        self.boxid_label_2["state"] = "normal"
        self.boxid_entry_2["state"] = "normal"
        self.boxid_label_3["state"] = "normal"
        self.boxid_entry_3["state"] = "normal"
        self.boxid_label_4["state"] = "normal"
        self.boxid_entry_4["state"] = "normal"

        self.operator_entry.delete(0,END)
        self.boxid_entry_1.delete(0,END)
        self.boxid_entry_2.delete(0,END)
        self.boxid_entry_3.delete(0,END)
        self.boxid_entry_4.delete(0,END)

        self.reset_button["bg"] ="#FF9900"
        self.reset_button["activebackground"] ="#FFCF87"

    def start_measurements(self):
        params = self.get_options()
        if params is None:
            print("ENTER REQUIRED INFO")
            return

        print("BEGIN TESTS")
        self.status_label["text"] = "TESTS IN PROGRESS..."
        self.status_label["fg"] = "#000000"
        self.update_idletasks()
        maintest(self.config, **params)
        self.done_measuring(params)
        
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

    parser = ArgumentParser(description="Example GUI")

    args = parser.parse_args()

    root = Tk()
    root.title("FEMB Test GUI")
    window = GUI_WINDOW(root)
    root.mainloop() 

if __name__ == '__main__':
    main()
