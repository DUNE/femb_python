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
        self.operator_label = Label(self,text="Operator Name:",width=15)
        self.operator_label.grid(sticky=W,row=1,column=columnbase+0)

        self.operator_entry = Entry(self,width=25)
        self.operator_entry.grid(sticky=W,row=1,column=columnbase+1,columnspan=2)

        self.wibslot0 = IntVar()
        self.wibslot1 = IntVar()
        self.wibslot2 = IntVar()
        self.wibslot3 = IntVar()
        self.wibslot0_button = Checkbutton(self,text="WIB Slot 0", variable=self.wibslot0)
        self.wibslot1_button = Checkbutton(self,text="WIB Slot 1", variable=self.wibslot1)
        self.wibslot2_button = Checkbutton(self,text="WIB Slot 2", variable=self.wibslot2)
        self.wibslot3_button = Checkbutton(self,text="WIB Slot 3", variable=self.wibslot3)
        self.wibslot0_button.grid(sticky=W,row=3,column=columnbase+0)
        self.wibslot1_button.grid(sticky=W,row=4,column=columnbase+0)
        self.wibslot2_button.grid(sticky=W,row=5,column=columnbase+0)
        self.wibslot3_button.grid(sticky=W,row=6,column=columnbase+0)

        self.ct_bool = StringVar()
        self.temp_radio1 = Radiobutton(self, text="Room Temperature", variable=self.ct_bool, value=0)
        self.temp_radio2 = Radiobutton(self, text="Cryo Temperature", variable=self.ct_bool, value=1)
        self.temp_radio1.grid(sticky=W,row=3,column=columnbase+1)
        self.temp_radio2.grid(sticky=W,row=4,column=columnbase+1)

        # Adding electronics ID and read entry box

        
        #Slot 0
        self.slotlabel0 = Label(self,text="WIB Slot 0:")
        self.slotlabel0.grid(sticky=W,row=8,column=columnbase+0,pady=10)

        self.boxid0_label = Label(self,text="CE Box 0 ID:",width=15)
        self.boxid0_label.grid(sticky=W,row=9,column=columnbase+0)

        self.boxid0_entry = Entry(self,width=15)
        self.boxid0_entry.grid(sticky=W,row=9,column=columnbase+1)

        self.amid0_label = Label(self,text="Analog MB 0 ID:",width=15)
        self.amid0_label.grid(sticky=W,row=10,column=columnbase+0)

        self.amid0_entry = Entry(self,width=15)
        self.amid0_entry.grid(sticky=W,row=10,column=columnbase+1)

        self.fmid0_label = Label(self,text="FPGA Mezz 0 ID:",width=15)
        self.fmid0_label.grid(sticky=W,row=11,column=columnbase+0)

        self.fmid0_entry = Entry(self,width=15)
        self.fmid0_entry.grid(sticky=W,row=11,column=columnbase+1)

        #Slot 1
        self.slotlabel1 = Label(self,text="WIB Slot 1:")
        self.slotlabel1.grid(sticky=W,row=12,column=columnbase+0,pady=10)
        
        self.boxid1_label = Label(self,text="CE Box 1 ID:",width=15)
        self.boxid1_label.grid(sticky=W,row=13,column=columnbase+0)

        self.boxid1_entry = Entry(self,width=15)
        self.boxid1_entry.grid(sticky=W,row=13,column=columnbase+1)

        self.amid1_label = Label(self,text="Analog MB 1 ID:",width=15)
        self.amid1_label.grid(sticky=W,row=14,column=columnbase+0)

        self.amid1_entry = Entry(self,width=15)
        self.amid1_entry.grid(sticky=W,row=14,column=columnbase+1)

        self.fmid1_label = Label(self,text="FPGA Mezz 1 ID:",width=15)
        self.fmid1_label.grid(sticky=W,row=15,column=columnbase+0)

        self.fmid1_entry = Entry(self,width=15)
        self.fmid1_entry.grid(sticky=W,row=15,column=columnbase+1)

        #Slot 2
        self.slotlabel2 = Label(self,text="WIB Slot 2:")
        self.slotlabel2.grid(sticky=W,row=16,column=columnbase+0,pady=10)
        
        self.boxid2_label = Label(self,text="CE Box 2 ID:",width=15)
        self.boxid2_label.grid(sticky=W,row=17,column=columnbase+0)

        self.boxid2_entry = Entry(self,width=15)
        self.boxid2_entry.grid(sticky=W,row=17,column=columnbase+1)

        self.amid2_label = Label(self,text="Analog MB 2 ID:",width=15)
        self.amid2_label.grid(sticky=W,row=18,column=columnbase+0)

        self.amid2_entry = Entry(self,width=15)
        self.amid2_entry.grid(sticky=W,row=18,column=columnbase+1)

        self.fmid2_label = Label(self,text="FPGA Mezz 2 ID:",width=15)
        self.fmid2_label.grid(sticky=W,row=19,column=columnbase+0)

        self.fmid2_entry = Entry(self,width=15)
        self.fmid2_entry.grid(sticky=W,row=19,column=columnbase+1)

        #Slot 3
        self.slotlabel3 = Label(self,text="WIB Slot 3:")
        self.slotlabel3.grid(sticky=W,row=20,column=columnbase+0,pady=10)

        self.boxid3_label = Label(self,text="CE Box 3 ID:",width=15)
        self.boxid3_label.grid(sticky=W,row=21,column=columnbase+0)

        self.boxid3_entry = Entry(self,width=15)
        self.boxid3_entry.grid(sticky=W,row=21,column=columnbase+1)

        self.amid3_label = Label(self,text="Analog MB 3 ID:",width=15)
        self.amid3_label.grid(sticky=W,row=22,column=columnbase+0)

        self.amid3_entry = Entry(self,width=15)
        self.amid3_entry.grid(sticky=W,row=22,column=columnbase+1)

        self.fmid3_label = Label(self,text="FPGA Mezz 3 ID:",width=15)
        self.fmid3_label.grid(sticky=W,row=23,column=columnbase+0)

        self.fmid3_entry = Entry(self,width=15)
        self.fmid3_entry.grid(sticky=W,row=23,column=columnbase+1)
        
        # Start button
        self.start_button = Button(self, text="Start Tests", command=self.start_measurements,width=25)
        self.start_button.grid(row=24,column=columnbase,columnspan=2,pady=30)
        self.reset_button = Button(self, text="Reset", command=self.reset,width=25,bg="#FF8000")
        self.reset_button.grid(row=26,column=columnbase,columnspan=2)

        self.status_label = Label(self, text="NOT STARTED",bd=1,relief=SUNKEN,width=50)
        self.status_label.grid(row=100,column=columnbase,columnspan=2)
        self.bkg_color = self.status_label.cget("background")

    def get_options(self):
        operator = self.operator_entry.get()
        boxids = [self.boxid0_entry.get(), self.boxid1_entry.get(), self.boxid2_entry.get(), self.boxid3_entry.get()]
        amids = [self.amid0_entry.get(), self.amid1_entry.get(), self.amid2_entry.get(), self.amid3_entry.get()]
        fmids = [self.fmid0_entry.get(), self.fmid1_entry.get(), self.fmid2_entry.get(), self.fmid3_entry.get()]

        wibslots_all = [self.wibslot0.get(), self.wibslot1.get(), self.wibslot2.get(), self.wibslot3.get()]
        wibslots_filled = [x for x in range(len(wibslots_all)) if wibslots_all[x]==1]

        boxids_filled = [x for x in boxids if boxids.index(x) in wibslots_filled]
        amids_filled = [x for x in amids if amids.index(x) in wibslots_filled]
        fmids_filled = [x for x in fmids if fmids.index(x) in wibslots_filled]

        variables = [operator,self.ct_bool,wibslots_filled]

        if (self.ct_bool.get() == "1"):
            isRoomTemp = False
        else:
            isRoomTemp = True
        
        for var in variables:
            if var == "" :
                return
        print("Operator Name: '{}'".format(operator))
        print("WIB Slots Filled: ", wibslots_filled)

        inputOptions = {
            "operator": operator,
            "box_ids": boxids_filled,
            "fm_ids": fmids_filled,
            "am_ids": amids_filled,
            "isRoomTemp": isRoomTemp,
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
        self.start_button["state"] = "normal"
        self.operator_label["state"] = "normal"
        self.operator_entry["state"] = "normal"
        self.boxid0_label["state"] = "normal"
        self.boxid0_entry["state"] = "normal"
        self.amid0_label["state"] = "normal"
        self.amid0_entry["state"] = "normal"
        self.fmid0_label["state"] = "normal"
        self.fmid0_entry["state"] = "normal"
        self.boxid1_label["state"] = "normal"
        self.boxid1_entry["state"] = "normal"
        self.amid1_label["state"] = "normal"
        self.amid1_entry["state"] = "normal"
        self.fmid1_label["state"] = "normal"
        self.fmid1_entry["state"] = "normal"
        self.boxid2_label["state"] = "normal"
        self.boxid2_entry["state"] = "normal"
        self.amid2_label["state"] = "normal"
        self.amid2_entry["state"] = "normal"
        self.fmid2_label["state"] = "normal"
        self.fmid2_entry["state"] = "normal"
        self.boxid3_label["state"] = "normal"
        self.boxid3_entry["state"] = "normal"
        self.amid3_label["state"] = "normal"
        self.amid3_entry["state"] = "normal"
        self.fmid3_label["state"] = "normal"
        self.fmid3_entry["state"] = "normal"

        self.boxid0_entry.delete(0,END)
        self.amid0_entry.delete(0,END)
        self.fmid0_entry.delete(0,END)
        self.boxid1_entry.delete(0,END)
        self.amid1_entry.delete(0,END)
        self.fmid1_entry.delete(0,END)
        self.boxid2_entry.delete(0,END)
        self.amid2_entry.delete(0,END)
        self.fmid2_entry.delete(0,END)
        self.boxid3_entry.delete(0,END)
        self.amid3_entry.delete(0,END)
        self.fmid3_entry.delete(0,END)
        
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
