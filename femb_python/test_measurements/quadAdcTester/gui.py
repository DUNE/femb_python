"""
QUAD ADC Test Stand GUI
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
from femb_python.test_measurements.quadAdcTester.quadAdcTest import main as maintest

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

        self.asicsocket0 = IntVar()
        self.asicsocket1 = IntVar()
        self.asicsocket2 = IntVar()
        self.asicsocket3 = IntVar()
        self.asicsocket0_button = Checkbutton(self,text="ADC Socket 0", variable=self.asicsocket0)
        self.asicsocket1_button = Checkbutton(self,text="ADC Socket 1", variable=self.asicsocket1)
        self.asicsocket2_button = Checkbutton(self,text="ADC Socket 2", variable=self.asicsocket2)
        self.asicsocket3_button = Checkbutton(self,text="ADC Socket 3", variable=self.asicsocket3)
        self.asicsocket0_button.grid(sticky=W,row=3,column=columnbase+0)
        self.asicsocket1_button.grid(sticky=W,row=4,column=columnbase+0)
        self.asicsocket2_button.grid(sticky=W,row=5,column=columnbase+0)
        self.asicsocket3_button.grid(sticky=W,row=6,column=columnbase+0)

        self.ct_bool = StringVar()
        self.temp_radio1 = Radiobutton(self, text="Room Temperature", variable=self.ct_bool, value=0)
        self.temp_radio2 = Radiobutton(self, text="Cryo Temperature", variable=self.ct_bool, value=1)
        self.temp_radio1.grid(sticky=W,row=3,column=columnbase+1)
        self.temp_radio2.grid(sticky=W,row=4,column=columnbase+1)

        # Adding electronics ID and read entry box

        #teststand ID
        self.teststandid_label = Label(self,text="Test Stand ID:",width=15)
        self.teststandid_label.grid(sticky=W,row=7,column=columnbase+0)

        self.teststandid_entry = Entry(self,width=15)
        self.teststandid_entry.grid(sticky=W,row=7,column=columnbase+1)

        #board ID
        self.boardid_label = Label(self,text="Board ID:",width=15)
        self.boardid_label.grid(sticky=W,row=8,column=columnbase+0)

        self.boardid_entry = Entry(self,width=15)
        self.boardid_entry.grid(sticky=W,row=8,column=columnbase+1)
        
        #Socket 0
        self.asicid0_label = Label(self,text="ASIC 0 ID:",width=15)
        self.asicid0_label.grid(sticky=W,row=9,column=columnbase+0)

        self.asicid0_entry = Entry(self,width=15)
        self.asicid0_entry.grid(sticky=W,row=9,column=columnbase+1)
           
        #Socket 1
        self.asicid1_label = Label(self,text="ASIC 1 ID:",width=15)
        self.asicid1_label.grid(sticky=W,row=10,column=columnbase+0)

        self.asicid1_entry = Entry(self,width=15)
        self.asicid1_entry.grid(sticky=W,row=10,column=columnbase+1)
        
        #Socket 2
        self.asicid2_label = Label(self,text="ASIC 2 ID:",width=15)
        self.asicid2_label.grid(sticky=W,row=11,column=columnbase+0)

        self.asicid2_entry = Entry(self,width=15)
        self.asicid2_entry.grid(sticky=W,row=11,column=columnbase+1)

        #Socket 3
        self.asicid3_label = Label(self,text="ASIC 3 ID:",width=15)
        self.asicid3_label.grid(sticky=W,row=12,column=columnbase+0)

        self.asicid3_entry = Entry(self,width=15)
        self.asicid3_entry.grid(sticky=W,row=12,column=columnbase+1)
        
        #Start button
        self.start_button = Button(self, text="Start Tests", command=self.start_measurements,width=25)
        self.start_button.grid(row=13,column=columnbase,columnspan=4,pady=30)

        #Reset button
        self.reset_button = Button(self, text="Reset", command=self.reset,width=25,bg="#FF8000")
        self.reset_button.grid(row=14,column=columnbase,columnspan=4)

        self.status_label = Label(self, text="NOT STARTED",bd=1,relief=SUNKEN,width=50)
        self.status_label.grid(row=15,column=columnbase,columnspan=4)
        self.bkg_color = self.status_label.cget("background")

    def get_options(self):
        operator = self.operator_entry.get()
        teststandid = self.teststandid_entry.get()
        boardid = self.boardid_entry.get()
        asicids = [self.asicid0_entry.get(), self.asicid1_entry.get(), self.asicid2_entry.get(), self.asicid3_entry.get()]
        asicsockets_all = [self.asicsocket0.get(), self.asicsocket1.get(), self.asicsocket2.get(), self.asicsocket3.get()]

        asicsockets_filled = [x for x in range(len(asicsockets_all)) if asicsockets_all[x]==1]
        asicids_filled = [x for x in asicids if asicids.index(x) in asicsockets_filled]

        variables = [operator,self.ct_bool,teststandid,boardid,asicsockets_filled, asicids_filled]

        if (self.ct_bool.get() == "1"):
            isCold = True
        else:
            isCold = False
        
        for var in variables:
            if var == "" :
                return
        print("Operator Name: '{}'".format(operator))
        print("Teststand ID: '{}'".format(teststandid))
        print("Board ID: '{}'".format(boardid))
        print("ASIC Sockets Filled: ", asicsockets_filled)

        inputOptions = {
            "operator": operator,
            "teststandid": teststandid,
            "boardid": boardid,
            "asic_ids": asicids_filled,
            "isCold": isCold,
            "asicsockets": asicsockets_filled,
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
        self.teststandid_label["state"] = "normal"
        self.teststandid_entry["state"] = "normal"
        self.boardid_label["state"] = "normal"
        self.boardid_entry["state"] = "normal"
        self.asicid0_label["state"] = "normal"
        self.asicid0_entry["state"] = "normal"
        self.asicid1_label["state"] = "normal"
        self.asicid1_entry["state"] = "normal"
        self.asicid2_label["state"] = "normal"
        self.asicid2_entry["state"] = "normal"
        self.asicid3_label["state"] = "normal"
        self.asicid3_entry["state"] = "normal"
        self.asicid0_entry.delete(0,END)
        self.asicid1_entry.delete(0,END)
        self.asicid2_entry.delete(0,END)
        self.asicid3_entry.delete(0,END)

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
    from femb_python.configuration.argument_parser import ArgumentParser

    parser = ArgumentParser(description="QUADADC Test GUI")

    args = parser.parse_args()

    root = Tk()
    root.title("QUADADC Test GUI")
    window = GUI_WINDOW(root)
    root.mainloop()

if __name__ == '__main__':
    main()
