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
from time import sleep
from tkinter import *

#import the test module
from femb_python.test_measurements.example_femb_test.doFembTest_test import FEMB_TEST

class GUI_WINDOW(Frame):

    #GUI window defined entirely in init function
    def __init__(self, master=None):
        Frame.__init__(self,master)
        self.pack()

        #define test object
        self.femb_test = FEMB_TEST()

        #Define general commands column
        self.define_test_details_column()

        #Define general commands column
        self.define_general_commands_column()

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
        label = Label(self,text="Chip/Board ID:",width=25)
        label.grid(sticky=W,row=3,column=columnbase+0)

        self.boardid_entry = Entry(self,width=25)
        self.boardid_entry.grid(sticky=W,row=3,column=columnbase+1)

        # Adding traveller # and read entry box
        label = Label(self,text="Traveller #:",width=25)
        label.grid(sticky=W,row=4,column=columnbase+0)

        self.traveller_entry = Entry(self,width=25)
        self.traveller_entry.grid(sticky=W,row=4,column=columnbase+1)


    def define_general_commands_column(self):
        columnbase=50

        label = Label(self, text="Test Commands")
        label.grid(row=0,column=columnbase, columnspan=50)

        #Adding the check test stand button
        check_setup_button = Button(self, text="Check Test Stand", command=self.check_setup,width=25)
        check_setup_button.grid(row=1,column=columnbase,columnspan=25)

        self.check_setup_result = Label(self, text="",width=25)
        self.check_setup_result.grid(sticky=W,row=1,column=columnbase+25,columnspan=25)

        #Adding the record data button
        record_data_button = Button(self, text="Record Data", command=self.record_data,width=25)
        record_data_button.grid(row=2,column=columnbase,columnspan=25)

        self.record_data_result = Label(self, text="",width=25)
        self.record_data_result.grid(sticky=W,row=2,column=columnbase+25,columnspan=25)

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

    def check_setup(self):
        operator_name = self.operator_entry.get()
        test_stand = self.test_stand_entry.get()
        boardid = self.boardid_entry.get()
        traveller = self.traveller_entry.get()
        print("Operator Name: " + str( operator_name ) )
        print("Test Stand # : " + str( test_stand ) )
        print("Board/Chip ID: " + str( boardid ) )
        print("Traveller #  : " + str( traveller ) )

        self.femb_test.check_setup()
        if self.femb_test.status_check_setup == 0:
            self.check_setup_result["text"] = "TERRIBLE FAILURE"
        else:
            self.check_setup_result["text"] = "SUCCESS"

    def record_data(self):
        self.femb_test.record_data()
        if self.femb_test.status_record_data == 0:
            self.record_data_result["text"] = "TERRIBLE FAILURE"
        else:
            self.record_data_result["text"] = "SUCCESS"

    def analyze_data(self):
        self.femb_test.do_analysis()
        if self.femb_test.status_do_analysis == 0:
            self.analyze_data_result["text"] = "TERRIBLE FAILURE"
        else:
            self.analyze_data_result["text"] = "SUCCESS"

    def archive_results(self):
        self.femb_test.archive_results()
        if self.femb_test.status_archive_results == 0:
            self.archive_results_result["text"] = "TERRIBLE FAILURE"
        else:
            self.archive_results_result["text"] = "TOTAL VICTORY"

def main():
    root = Tk()
    root.title("Example Test GUI")
    window = GUI_WINDOW(root)
    root.mainloop() 

if __name__ == '__main__':
    main()
