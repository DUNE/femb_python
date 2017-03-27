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

from .configuration import CONFIG
from . import trace_fft_window

import numpy as np
from matplotlib import pyplot

from tkinter import *


class CONFIGURATION_WINDOW(Frame):


    def __init__(self, master=None):
        Frame.__init__(self,master)
        self.pack()

        #Define configuration object
        self.femb_config = CONFIG()

        #Define general commands column
        self.define_general_commands_column()

        #Define configuration commands column
        self.define_config_commands_column()

        #Define fe-asic configuration column
        self.define_feasic_config_commands_column()

        #Define adc asic configuration column
        self.define_adcasic_config_commands_column()

    def define_general_commands_column(self):

        label = Label(self, text="General Commands Column")
        label.pack()

        #Adding the read register button
        readreg_button = Button(self, text="Read Register", command=self.call_readRegister)
        readreg_button.pack()      

        # Adding register number to read entry box
        self.readreg_number_entry = Entry(self,width=4)
        self.readreg_number_entry.pack()

        # Adding read register result label
        self.readreg_result = Label(self, text="")
        self.readreg_result.pack()

        #Adding the write register button
        writereg_button = Button(self, text="Write Register", command=self.call_writeRegister)
        writereg_button.pack()

        # Adding register number to write entry box
        self.writereg_number_entry = Entry(self,width=4)
        self.writereg_number_entry.pack()

        # Adding register number to write entry box
        self.writereg_value_entry = Entry(self,width=15)
        self.writereg_value_entry.pack()

        # Adding write register result label
        self.writereg_result = Label(self, text="")
        self.writereg_result.pack()

        #Adding the reset plot button
        reset_plot_button = Button(self, text="Show/Reset Plots", command=self.reset_plot)   
        reset_plot_button.pack()


    def define_config_commands_column(self):
        label = Label(self, text="Configuration Commands Column")
        label.pack()

        #Need to write to the register here (define the variable to write there)

        #Adding the reset button
        reset_button = Button(self, text="Reset", command=self.call_reset)
        reset_button.pack()

        #Adding the initialization button
        init_button = Button(self, text="Initialize", command=self.call_initialize)
        init_button.pack()

        #Adding the select channel button
        selectChannel_button = Button(self, text="Select Channel", command=self.call_selectChannel)
        selectChannel_button.pack()

    def define_feasic_config_commands_column(self):

        label = Label(self, text="FE ASIC Configuration Commands Column")
        label.pack()

        #Adding the configure all FE-ASIC channels button
        feasic_config_button = Button(self, text="Config FE-ASIC", command=self.call_feasic_config)
        feasic_config_button.pack()


    def define_adcasic_config_commands_column(self):

        label = Label(self, text="ADC ASIC Configuration Commands Column")
        label.pack()

        #Adding the configure all ADC-ASIC channels button
        adc_config_button = Button(self, text="Config ADC-ASIC", command=self.call_adcasic_config)
        adc_config_button.pack()


    def call_readRegister(self):
        regnum = self.readreg_number_entry.get()
        try:
          regnum = int(regnum)
          if regnum < 0:
            raise ValueError("regnum must be >= 0")
        except ValueError:
          self.readreg_result["text"] = "Error: Register must be a number >= 0"
          return
        message = ""
        regVal = self.femb_config.femb.read_reg(regnum)
        if regVal != None:
                message = "0x{:08x}".format(regVal)
        else:
                message = "Error: regVal = None"
        self.readreg_result["text"] = message

    def call_writeRegister(self):
        regnum = self.writereg_number_entry.get()
        try:
          regnum = int(regnum)
          if regnum < 0:
            raise ValueError("regnum must be >= 0")
        except ValueError:
          self.writereg_result["text"] = "Error: Register must be a number >= 0"
          return
        regval = self.writereg_value_entry.get()
        message = "value must be int literal e.g. 123, 0xF3, 0b0101"
        if regval[:2] == "0x":
          try:
            regval = int(regval,16)
          except ValueError:
            self.writereg_result["text"] = message
            return
        elif regval[:2] == "0b":
          try:
            regval = int(regval,2)
          except ValueError:
            self.writereg_result["text"] = message
            return
        else:
          try:
            regval = int(regval)
          except ValueError:
            self.writereg_result["text"] = message
            return
        if (regval < 0) or (regval > 0xFFFFFFFF):
            message = 'Value must be > 0 and < 0xFFFFFFFF'
            self.writereg_result["text"] = message
            return
        self.femb_config.femb.write_reg(regnum,regval)
        self.writereg_result["text"] = ""

    def call_reset(self):
        self.femb_config.resetBoard()


    def call_initialize(self):
        self.femb_config.initBoard()


    def call_selectChannel(self):
        chVal = int(self.selectChannel_entry.get_text())
        # need to get min + max channel values from femb_config object
        if (chVal < 0) or (chVal >= 128):
                return
        asic = chVal / 16
        chan = chVal % 16
        self.femb_config.selectChannel(asic,chan)


    def call_feasic_config(self):
        gainInd = int(self.gainval_combo.get_active())
        shapeInd = int(self.selshape_combo.get_active())
        baseInd = int(self.selbase_combo.get_active())
        self.femb_config.configFeAsic(gainInd,shapeInd,baseInd)


    def call_adcasic_config(self):
        print("call_adcasic_config")
        self.femb_config.configAdcAsic()


    def call_quit(self):
        print("call_adcasic_config")


    def reset_plot(self):
        window = tk.Toplevel(root)
        try:
          if window.plot_window.get_property("visible"):
            window.plot_window.reset()
          else:
            window.plot_window = trace_fft_window.TRACE_FFT_WINDOW()
        except AttributeError:
            window.plot_window = trace_fft_window.TRACE_FFT_WINDOW()

#And here! =============================================================================================|

def main():
  
  root = Tk()
  root.title("Configuration Window")
  window = CONFIGURATION_WINDOW(root)
  root.mainloop()        
