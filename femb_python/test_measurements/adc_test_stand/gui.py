"""
ADC Test Stand GUI
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
from time import sleep
from tkinter import *

#import the test module
from ...configuration import CONFIG
from .run import runTests

class GUI_WINDOW(Frame):

    #GUI window defined entirely in init function
    def __init__(self, master=None):
        Frame.__init__(self,master)
        self.pack()

        self.config = CONFIG()

        #Define general commands column
        self.define_test_details_column()
        self.reset()

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

        self.prepare_button = Button(self, text="Power-up Board", command=self.prepare_board,width=25)
        self.prepare_button.grid(row=20,column=columnbase,columnspan=25)

        # Adding electronics ID and read entry box
        self.current_label = Label(self,text="CH2 Current [A]:",width=25,state="disabled")
        self.current_label.grid(sticky=W,row=21,column=columnbase+0)

        self.current_entry = Entry(self,width=25,state="disabled")
        self.current_entry.grid(sticky=W,row=21,column=columnbase+1)

        self.start_button = Button(self, text="Start Tests", command=self.start_measurements,width=25)
        self.start_button.grid(row=22,column=columnbase,columnspan=25)
        self.reset_button = Button(self, text="Reset & Power-off", command=self.reset,width=25,bg="#FF8000")
        self.reset_button.grid(row=24,column=columnbase,columnspan=25)

        self.status_text = Label(self, text="NOT STARTED",bd=1,relief=SUNKEN,width=50)
        self.status_text.grid(row=26,column=columnbase,columnspan=2)

    def get_options(self,getCurrent=False):
        operator = self.operator_entry.get()
        boardid = self.boardid_entry.get()
        current = None
        if getCurrent:
            current = self.current_entry.get()
        # ASIC IDs
        asic_ids = []
        for i in range(self.config.NASICS):
            asic_ids.append(self.asic_entries[i].get())

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
        timestamp = datetime.datetime.now().replace(microsecond=0).isoformat()
        hostname = socket.gethostname() 
        inputOptions = {
            "operator": operator,
            "boardid": boardid,
            "asic_ids":asic_ids,
            "timestamp": timestamp,
            "hostname": hostname,
        }
        if getCurrent:
            inputOptions["current"] = current
        print(inputOptions)
        return inputOptions

    def reset(self):
        self.power_down()
        self.status_text["text"] = "NOT STARTED"
        self.status_text["fg"] = "#000000"
        self.prepare_button["state"] = "normal"
        self.start_button["state"] = "disabled"
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
        for i in range(self.config.NASICS):
            self.asic_labels[i]["state"] = "normal"
            self.asic_entries[i]["state"] = "normal"
            self.asic_entries[i].delete(0,END)
        self.reset_button["bg"] ="#FF9900"
        self.reset_button["activebackground"] ="#FFCF87"

    def prepare_board(self):
        inputOptions = self.get_options()
        if inputOptions is None:
            print("ENTER REQUIRED INFO")
            self.status_text["text"] = "ENTER REQUIRED INFO"
            self.status_text["fg"] = "#FF0000"
            return
        print("BEGIN PREPARE")
        self.status_text["text"] = "POWERING UP BOARD..."
        self.status_text["fg"] = "#000000"

        sleep(1)
        self.done_preparing_board()

    def start_measurements(self):
        inputOptions = self.get_options(getCurrent=True)
        if inputOptions is None:
            print("ENTER REQUIRED INFO")
            self.status_text["text"] = "ENTER FLOAT FOR CURRENT"
            self.status_text["fg"] = "#FF0000"
            return
        self.current_label["state"] = "disabled"
        self.current_entry["state"] = "disabled"
        self.start_button["state"] = "disabled"

        print("BEGIN TESTS")
        self.status_text["text"] = "TESTS IN PROGRESS..."
        self.status_text["fg"] = "#000000"

        sleep(1)
        self.done_measuring()

    def done_preparing_board(self):
        ## once prepared....
        print("BOARD POWERED UP & INITIALIZED")
        self.current_label["state"] = "normal"
        self.current_entry["state"] = "normal"
        self.status_text["text"] = "Power up success, enter CH2 Current"
        self.status_text["fg"] = "#000000"
        self.prepare_button["state"] = "disabled"
        self.start_button["state"] = "normal"
        self.operator_label["state"] = "disabled"
        self.operator_entry["state"] = "disabled"
        self.boardid_label["state"] = "disabled"
        self.boardid_entry["state"] = "disabled"
        for i in range(self.config.NASICS):
            self.asic_labels[i]["state"] = "disabled"
            self.asic_entries[i]["state"] = "disabled"

    def done_measuring(self):
        print("TESTS COMPLETE")
        self.status_text["text"] = "Tests done"
        self.reset_button["bg"] ="#00CC00"
        self.reset_button["activebackground"] = "#A3CCA3"

    def power_down(self):
        print("POWER DOWN")

def main():
    root = Tk()
    root.title("ADC Test GUI")
    window = GUI_WINDOW(root)
    root.mainloop() 
