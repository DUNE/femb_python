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
from ...configuration import CONFIG
from .fembTest import main as maintest

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

        # Adding operator name label and read entry box
        self.operator_label = Label(self,text="Operator Name:",width=25)
        self.operator_label.grid(sticky=W,row=1,column=columnbase+0)

        self.operator_entry = Entry(self,width=25)
        self.operator_entry.grid(sticky=W,row=1,column=columnbase+1)

        # Adding electronics ID and read entry box
        self.boxid_label = Label(self,text="CE Box ID:",width=25)
        self.boxid_label.grid(sticky=W,row=3,column=columnbase+0)

        self.boxid_entry = Entry(self,width=25)
        self.boxid_entry.grid(sticky=W,row=3,column=columnbase+1)

        self.amid_label = Label(self,text="Analog MB ID:",width=25)
        self.amid_label.grid(sticky=W,row=4,column=columnbase+0)

        self.amid_entry = Entry(self,width=25)
        self.amid_entry.grid(sticky=W,row=4,column=columnbase+1)

        self.fmid_label = Label(self,text="FPGA Mezz ID:",width=25)
        self.fmid_label.grid(sticky=W,row=5,column=columnbase+0)

        self.fmid_entry = Entry(self,width=25)
        self.fmid_entry.grid(sticky=W,row=5,column=columnbase+1)

        self.wibslot0 = IntVar()
        self.wibslot1 = IntVar()
        self.wibslot2 = IntVar()
        self.wibslot3 = IntVar()
        self.wibslot0_button = Checkbutton(self,text="WIB Slot 0", variable=self.wibslot0)
        self.wibslot1_button = Checkbutton(self,text="WIB Slot 1", variable=self.wibslot1)
        self.wibslot2_button = Checkbutton(self,text="WIB Slot 2", variable=self.wibslot2)
        self.wibslot3_button = Checkbutton(self,text="WIB Slot 3", variable=self.wibslot3)
        self.wibslot0_button.grid(sticky=W,row=7,column=columnbase)
        self.wibslot1_button.grid(sticky=W,row=8,column=columnbase)
        self.wibslot2_button.grid(sticky=W,row=9,column=columnbase)
        self.wibslot3_button.grid(sticky=W,row=10,column=columnbase)

        self.ct_bool = StringVar()
        self.temp_radio1 = Radiobutton(self, text="Room Temperature", variable=self.ct_bool, value=0)
        self.temp_radio2 = Radiobutton(self, text="Cryo Temperature", variable=self.ct_bool, value=1)
        self.temp_radio1.grid(sticky=W,row=7,column=columnbase+1)
        self.temp_radio2.grid(sticky=W,row=8,column=columnbase+1)
        
        # Adding electronics ID and read entry box
        self.start_button = Button(self, text="Start Tests", command=self.start_measurements,width=25)
        self.start_button.grid(row=22,column=columnbase,columnspan=2,pady=30)
        self.reset_button = Button(self, text="Reset", command=self.reset,width=25,bg="#FF8000")
        self.reset_button.grid(row=24,column=columnbase,columnspan=2)

        self.runid_label = Label(self, text="")
        self.runid_label.grid(row=25,column=columnbase,columnspan=2,pady=20)

        self.status_label = Label(self, text="NOT STARTED",bd=1,relief=SUNKEN,width=50)
        self.status_label.grid(row=100,column=columnbase,columnspan=2)
        self.bkg_color = self.status_label.cget("background")

    def get_options(self):
        operator = self.operator_entry.get()
        boxid = self.boxid_entry.get()
        amid = self.amid_entry.get()
        fmid = self.fmid_entry.get()

        wibslots_all = [self.wibslot0.get(), self.wibslot1.get(), self.wibslot2.get(), self.wibslot3.get()]
        wibslots_filled = [x for x in range(len(wibslots_all)) if wibslots_all[x]==1]
        
        variables = [operator,boxid,amid,fmid,self.ct_bool,wibslots_filled]
        if (self.ct_bool.get() == "1"):
            isRoomTemp = False
        else:
            isRoomTemp = True
        
        for var in variables:
            if var == "" :
                return
        print("Operator Name: '{}'".format(operator))
        print("CE Box ID: '{}'".format(boxid))
        print("Analog MB ID: '{}'".format(amid))
        print("FPGA Mezz ID: '{}'".format(fmid))
        print("Test temperature: '{}'".format(temp))
        print("WIB Slots Filled: ", wibslots_filled)

        inputOptions = {
            "operator": operator,
            "box_id": boxid,
            "fm_id": fmid,
            "am_id": amid,
            "isRoomTemp": temp,
            "wibslots": wibslots_filled
        }
        print(inputOptions)
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
        self.boxid_label["state"] = "normal"
        self.boxid_entry["state"] = "normal"
        self.amid_label["state"] = "normal"
        self.amid_entry["state"] = "normal"
        self.fmid_label["state"] = "normal"
        self.fmid_entry["state"] = "normal"

        self.boxid_entry.delete(0,END)
        self.amid_entry.delete(0,END)
        self.fmid_entry.delete(0,END)
        
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
        maintest(**params)
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
    from ...configuration.argument_parser import ArgumentParser

    parser = ArgumentParser(description="FEMB Test GUI")

    args = parser.parse_args()

    root = Tk()
    root.title("FEMB Test GUI")
    window = GUI_WINDOW(root)
    root.mainloop() 
