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

from Tkinter import *


class CONFIGURATION_WINDOW:


    def __init__(self, master):
        mainframe = Frame(master)
        mainframe.pack()

        #Define configuration object
        self.femb_config = CONFIG()

        #Define general commands column
        self.define_general_commands_column(mainframe)

        #Define configuration commands column
        self.define_config_commands_column(mainframe)

        #Define fe-asic configuration column
        self.define_feasic_config_commands_column(mainframe)

        #Define adc asic configuration column
        self.define_adcasic_config_commands_column(mainframe)


    def define_general_commands_column(self, master):
        frame_cmd = Frame(master)
        frame_cmd.pack(side=TOP)
        
        #Now you need to fill inbetween here ---------------------------------------------------------------|

        self.label = Label(frame_cmd, text="General Commands Column")
        self.label.pack()

        #Need to write to the register here (define the variable to write there)

        #Adding the read register button
        readreg_button = Button(frame_cmd, text="Read Register", command=self.call_readRegister)
        readreg_button.pack()      

        #Adding the write register button
        writereg_button = Button(frame_cmd, text="Write Register", command=self.call_writeRegister)
        writereg_button.pack()

        #Adding the reset plot button
        reset_plot_button = Button(frame_cmd, text="Show/Reset Plots", command=self.reset_plot)   
        reset_plot_button.pack()

        #And here ------------------------------------------------------------------------------------------|


    def define_config_commands_column(self, master):
        frame_config = Frame(master)
        frame_config.pack(side=TOP)

        #Now you need to fill inbetween here ---------------------------------------------------------------|

        self.label = Label(frame_config, text="Configuration Commands Column")
        self.label.pack()

        #Need to write to the register here (define the variable to write there)

        #Adding the reset button
        reset_button = Button(frame_config, text="Reset", command=self.call_reset)
        reset_button.pack()

        #Adding the initialization button
        init_button = Button(frame_config, text="Initialize", command=self.call_initialize)
        init_button.pack()

        #Adding the select channel button
        selectChannel_button = Button(frame_config, text="Select Channel", command=self.call_selectChannel)
        selectChannel_button.pack()

        #And here ------------------------------------------------------------------------------------------|


    def define_feasic_config_commands_column(self, master):
        frame_feasic_config = Frame(master)
        frame_feasic_config.pack(side=TOP)

        #Now you need to fill inbetween here ---------------------------------------------------------------|

        self.label = Label(frame_feasic_config, text="FE ASIC Configuration Commands Column")
        self.label.pack()

        #Adding the configure all FE-ASIC channels button
        feasic_config_button = Button(frame_feasic_config, text="Config FE-ASIC", command=self.call_feasic_config)
        feasic_config_button.pack()

        #And here ------------------------------------------------------------------------------------------|


    def define_adcasic_config_commands_column(self, master):
        frame_adcasic_config = Frame(master)
        frame_adcasic_config.pack(side=TOP)

        #Now you need to fill inbetween here ---------------------------------------------------------------|

        self.label = Label(frame_adcasic_config, text="ADC ASIC Configuration Commands Column")
        self.label.pack()

        #Adding the configure all ADC-ASIC channels button
        adc_config_button = Button(frame_adcasic_config, text="Config ADC-ASIC", command=self.call_adcasic_config)
        adc_config_button.pack()

        #And here ------------------------------------------------------------------------------------------|


    #The buttons will go inbetween here! ===================================================================|

    def call_readRegister(self):
        regVal = self.femb_config.femb.read_reg(self.selectreg_entry.get_text())
        if regVal != None:
                self.readreg_entry.set_text(str(hex(regVal)))


    def call_writeRegister(self):
        regNum = self.femb_config.femb.write_reg(self.selectreg_entry.get_text(),self.writereg_entry.get_text())


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
        try:
          if self.plot_window.get_property("visible"):
            self.plot_window.reset()
          else:
            self.plot_window = trace_fft_window.TRACE_FFT_WINDOW()
        except AttributeError:
            self.plot_window = trace_fft_window.TRACE_FFT_WINDOW()

    #And here! =============================================================================================|


root = Tk()
root.title("Configuration Window")
window = CONFIGURATION_WINDOW(root)
root.mainloop()        
