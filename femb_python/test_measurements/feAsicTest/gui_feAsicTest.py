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
from femb_python.test_measurements.feAsicTest.doFembTest_simpleMeasurement import FEMB_TEST_SIMPLE
from femb_python.test_measurements.feAsicTest.doFembTest_gainMeasurement import FEMB_TEST_GAIN

class GUI_WINDOW(Frame):

    #GUI window defined entirely in init function
    def __init__(self, master=None):
        Frame.__init__(self,master)
        self.pack()

        #define test object
        #self.femb_test = FEMB_TEST()

        #Define general commands column
        self.define_test_details_column()

        #Define general commands column
        self.define_general_commands_column()

        #define test result variable
        self.test_result = 0

        #define required variables
        self.operator_name = ""
        self.test_stand = ""
        self.boardid = ""
        self.asic0id = ""
        self.asic1id = ""
        self.asic2id = ""
        self.asic3id = ""
        self.test_version = "1"

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
        label.grid(sticky=W,row=6,column=columnbase+0)

        self.asic0_entry = Entry(self,width=25)
        self.asic0_entry.grid(sticky=W,row=6,column=columnbase+1)

        # ASIC 1 ID
        label = Label(self,text="ASIC 1 ID:",width=25)
        label.grid(sticky=W,row=7,column=columnbase+0)

        self.asic1_entry = Entry(self,width=25)
        self.asic1_entry.grid(sticky=W,row=7,column=columnbase+1)

        # ASIC 2 ID
        label = Label(self,text="ASIC 2 ID:",width=25)
        label.grid(sticky=W,row=8,column=columnbase+0)

        self.asic2_entry = Entry(self,width=25)
        self.asic2_entry.grid(sticky=W,row=8,column=columnbase+1)

        # ASIC 3 ID
        label = Label(self,text="ASIC 3 ID:",width=25)
        label.grid(sticky=W,row=9,column=columnbase+0)

        self.asic3_entry = Entry(self,width=25)
        self.asic3_entry.grid(sticky=W,row=9,column=columnbase+1)


    def define_general_commands_column(self):
        columnbase=50

        label = Label(self, text="FE ASIC TESTS")
        label.grid(row=0,column=columnbase, columnspan=50)

        #Adding the check test stand button
        start_button = Button(self, text="Start Tests", command=self.start_measurements,width=25)
        start_button.grid(row=1,column=columnbase,columnspan=25)

        self.start_button_result = Label(self, text="NOT STARTED",width=25)
        self.start_button_result.grid(sticky=W,row=1,column=columnbase+25,columnspan=25)

        #Adding the record data button
        #record_data_button = Button(self, text="Record Data", command=self.record_data,width=25)
        #record_data_button.grid(row=2,column=columnbase,columnspan=25)

        self.check_setup_result = Label(self, text="CHECK SETUP - NOT STARTED",width=50)
        self.check_setup_result.grid(sticky=W,row=2,column=columnbase,columnspan=50)

        self.test_1_result = Label(self, text="GAIN+ENC ALL SETTINGS - NOT STARTED",width=50)
        self.test_1_result.grid(sticky=W,row=3,column=columnbase,columnspan=50)

        #self.test_2_result = Label(self, text="CROSSTALK ALL SETTINGS - NOT STARTED",width=50)
        #self.test_2_result.grid(sticky=W,row=4,column=columnbase,columnspan=50)

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
        self.operator_name = self.operator_entry.get()
        self.test_stand = self.test_stand_entry.get()
        self.boardid = self.boardid_entry.get()
        self.asic0id = self.asic0_entry.get()
        self.asic1id = self.asic1_entry.get()
        self.asic2id = self.asic2_entry.get()
        self.asic3id = self.asic3_entry.get()
        print("Operator Name: " + str( self.operator_name ) )
        print("Test Stand # : " + str( self.test_stand ) )
        print("Test Board ID: " + str( self.boardid ) )
        print("ASIC 1 ID: " + str(self.asic0id ) )
        print("ASIC 2 ID: " + str(self.asic1id ) )
        print("ASIC 3 ID: " + str(self.asic2id ) )
        print("ASIC 4 ID: " + str(self.asic3id ) )

        # only number 1-4 in the GUI to match the testboard
        
        if self.operator_name == "" :
            print("ENTER REQUIRED INFO")
            self.start_button_result["text"] = "ENTER REQUIRED INFO"
            self.update_idletasks()
            return

        print("BEGIN TESTS")
        self.start_button_result["text"] = "IN PROGRESS"
        self.update_idletasks()

        self.test_result = 0

        self.do_check_setup()
        if self.test_result == 0:
            self.start_button_result["text"] = "FAILED"
            self.update_idletasks()

        self.do_test_1()
        if self.test_result == 0:
            self.test_1_result["text"] = "FAILED"
            self.update_idletasks()

        #self.do_test_2()
        #if self.test_result == 0:
        #    self.test_2_result["text"] = "FAILED"

        self.start_button_result["text"] = "PASSED"
        self.update_idletasks()

        self.operator_entry.delete(0,1000)
        self.test_stand_entry.delete(0,1000)
        self.boardid_entry.delete(0,1000)
        self.asic0_entry.delete(0,1000)
        self.asic1_entry.delete(0,1000)
        self.asic2_entry.delete(0,1000)
        self.asic3_entry.delete(0,1000)

        print("FINISHED TEST - GUI RESET")

        #self.femb_test.check_setup()
        #if self.femb_test.status_check_setup == 0:
        #    self.check_setup_result["text"] = "TERRIBLE FAILURE"
        #else:
        #    self.check_setup_result["text"] = "SUCCESS"

    def do_check_setup(self):
        print("CHECK SETUP")
        self.check_setup_result["text"] = "CHECK SETUP - IN PROGRESS"
        self.update_idletasks()
        self.test_result = 0
        
        femb_test = FEMB_TEST_SIMPLE()

        femb_test.check_setup()
        if femb_test.status_check_setup == 0:
            self.check_setup_result["text"] = "CHECK SETUP - FAILED"
            self.update_idletasks()
            return

        femb_test.record_data()
        if femb_test.status_record_data == 0:
            self.check_setup_result["text"] = "CHECK SETUP - FAILED"
            self.update_idletasks()
            return

        femb_test.do_analysis()
        if femb_test.status_do_analysis == 0:
            self.check_setup_result["text"] = "CHECK SETUP - FAILED"
            self.update_idletasks()
            return
        
        self.check_setup_result["text"] = "CHECK SETUP - PASSED"
        self.update_idletasks()
        self.test_result = 1

    def do_test_1(self):
        testName = str("GAIN+ENC ALL SETTINGS")
        print(str(testName))
        self.test_1_result["text"] = str(testName) + " - IN PROGRESS"
        self.update_idletasks()
        self.test_result = 0
        
        #put loop here, but equivalently can go in script itself
        for g in range(2,3,1):
          for s in range(2,3,1):
            for b in range(0,1,1):
              femb_test = FEMB_TEST_GAIN()

              femb_test.gain = int(g)
              femb_test.shape = int(s)
              femb_test.base = int(b)

              femb_test.check_setup()
              if femb_test.status_check_setup == 0:
                self.test_1_result["text"] = str(testName) + " - FAILED"
                self.update_idletasks()
                return

              femb_test.record_data()
              if femb_test.status_record_data == 0:
                self.test_1_result["text"] = str(testName) + " - FAILED"
                self.update_idletasks()
                return

              femb_test.do_analysis()
              if femb_test.status_do_analysis == 0:
                self.test_1_result["text"] = str(testName) + " - FAILED"
                self.update_idletasks()
                return
        
        self.test_1_result["text"] = str(testName) + " - DONE"
        self.update_idletasks()
        self.test_result = 1

    def do_test_2(self):
        testName = str("CROSSTALK ALL SETTINGS")
        print(str(testName))
        self.test_2_result["text"] = str(testName) + " - IN PROGRESS"
        self.update_idletasks()
        self.test_result = 0
        
        femb_test = FEMB_TEST_GAIN()

        femb_test.test = 0
        femb_test.test = 2

        femb_test.check_setup()
        if femb_test.status_check_setup == 0:
            self.test_2_result["text"] = str(testName) + " - FAILED"
            self.update_idletasks()
            return

        femb_test.record_data()
        if femb_test.status_record_data == 0:
            self.test_2_result["text"] = str(testName) + " - FAILED"
            self.update_idletasks()
            return

        femb_test.do_analysis()
        if femb_test.status_do_analysis == 0:
            self.test_2_result["text"] = str(testName) + " - FAILED"
            self.update_idletasks()
            return
        
        self.test_2_result["text"] = str(testName) + " - DONE"
        self.update_idletasks()
        self.test_result = 1

def main():
    root = Tk()
    root.title("Quad FE ASIC Test GUI")
    window = GUI_WINDOW(root)
    root.mainloop() 

if __name__ == '__main__':
    main()
