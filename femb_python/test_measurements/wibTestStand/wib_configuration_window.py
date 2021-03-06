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

from femb_python.configuration import CONFIG
from femb_python.test_measurements.wibTestStand.wib_trace_fft_window import TRACE_FFT_WINDOW
from femb_python.test_measurements.wibTestStand.wib_trace_fft_allchan_window import TRACE_FFT_ALLCHAN_WINDOW

import numpy as np
from matplotlib import pyplot

from tkinter import *

GAINVALS = ("4.7 mV/fC","7.8 mV/fC","14 mV/fC","25 mV/fC")
SHAPEVALS = ("0.5 us", "1 us", "2 us", "3 us")
BASEVALS = ("200 mV--collection","900 mV--induction")
CHAN_OPTIONS = ("ALL",0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15)

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

        self.trace_fft_window = None
        #self.trace_fft_allchan_window = None
        self.trace_fft = None

    def define_general_commands_column(self):
        columnbase=0

        label = Label(self, text="General Commands")
        label.grid(row=0,column=columnbase, columnspan=2)

        label = Label(self,text="Register to read:")
        label.grid(sticky=W,row=1,column=columnbase+0)

        # Adding register number to read entry box
        self.readreg_number_entry = Entry(self,width=4)
        self.readreg_number_entry.grid(sticky=W,row=1,column=columnbase+1)

        # Adding read register result label
        label = Label(self,text="Register contents:")
        label.grid(sticky=W,row=2,column=columnbase+0)
        self.readreg_result = Label(self, text="",width=10)
        self.readreg_result.grid(sticky=W,row=2,column=columnbase+1)

        #Adding the read register button
        readreg_button = Button(self, text="Read Register", command=self.call_readRegister)
        readreg_button.grid(row=3,column=columnbase,columnspan=2)      

        label = Label(self,text="Register to write:")
        label.grid(sticky=W,row=4,column=columnbase+0)

        # Adding register number to write entry box
        self.writereg_number_entry = Entry(self,width=4)
        self.writereg_number_entry.grid(sticky=W,row=4,column=columnbase+1)

        label = Label(self,text="Value to write:")
        label.grid(sticky=W,row=5,column=columnbase+0)

        # Adding register value to write entry box
        self.writereg_value_entry = Entry(self,width=15)
        self.writereg_value_entry.grid(sticky=W,row=5,column=columnbase+1)

        #Adding the write register button
        writereg_button = Button(self, text="Write Register", command=self.call_writeRegister)
        writereg_button.grid(row=6,column=columnbase,columnspan=2)

        # Adding write register result label
        self.writereg_result = Label(self, text="")
        self.writereg_result.grid(sticky=W,row=7,column=columnbase,columnspan=2)

        #Adding the reset plot button
        reset_plot_button = Button(self, text="Show/Reset Plots", command=self.call_reset_plot)   
        reset_plot_button.grid(row=8,column=columnbase,columnspan=2)


    def define_config_commands_column(self):
        columnbase=10

        label = Label(self, text="Configuration Commands")
        label.grid(row=0,column=columnbase,columnspan=2)

        #Adding the reset button
        reset_button = Button(self, text="Reset", command=self.call_reset)
        reset_button.grid(row=1,column=columnbase,columnspan=2)

        #Adding the initialization button
        init_button = Button(self, text="Initialize", command=self.call_initialize)
        init_button.grid(row=2,column=columnbase,columnspan=2)

        # Adding femb number to select
        label = Label(self,text="FEMB:")
        label.grid(sticky=W,row=3,column=columnbase+0)
        self.femb_number_entry = Spinbox(self,from_=0,to=15,insertwidth=3,width=4)
        self.femb_number_entry.grid(sticky=W,row=3,column=columnbase+1)

        # Adding asic number to select
        label = Label(self,text="ASIC:")
        label.grid(sticky=W,row=4,column=columnbase+0)
        self.asic_number_entry = Spinbox(self,from_=0,to=7,insertwidth=1,width=4)
        self.asic_number_entry.grid(sticky=W,row=4,column=columnbase+1)

        # Adding channel number to select
        label = Label(self,text="Channel:")
        label.grid(sticky=W,row=5,column=columnbase+0)
        self.channel_number_entry = Spinbox(self,values=CHAN_OPTIONS,insertwidth=3,width=4)
        self.channel_number_entry.grid(sticky=W,row=5,column=columnbase+1)
        #self.channel_number_entry = Menu(self,insertwidth=3,width=4)
        #self.channel_number_entry.add_command(label="1")
        #self.channel_number_entry.grid(sticky=W,row=5,column=columnbase+1)

        #Adding the select channel button
        selectChannel_button = Button(self, text="Select Channel", command=self.call_selectChannel)
        selectChannel_button.grid(row=6,column=columnbase,columnspan=2)

        self.selectChannel_result = Label(self, text="")
        self.selectChannel_result.grid(sticky=W,row=7,column=columnbase)

    def define_feasic_config_commands_column(self):
        columnbase=20

        label = Label(self, text="FE ASIC Configuration Commands")
        label.grid(row=0,column=columnbase,columnspan=2)

        # FE ASIC config entry
        label = Label(self, text="Gain")
        label.grid(sticky=W,row=1,column=columnbase)
        self.feasic_config_gain_entry = Spinbox(self,values=GAINVALS,state="readonly")
        self.feasic_config_gain_entry.grid(sticky=W,row=1,column=columnbase+1)
        label = Label(self, text="Shape")
        label.grid(sticky=W,row=2,column=columnbase)
        self.feasic_config_shape_entry = Spinbox(self,values=SHAPEVALS,state="readonly")
        self.feasic_config_shape_entry.grid(sticky=W,row=2,column=columnbase+1)
        label = Label(self, text="Baseline")
        label.grid(sticky=W,row=3,column=columnbase)
        self.feasic_config_base_entry = Spinbox(self,values=BASEVALS,state="readonly")
        self.feasic_config_base_entry.grid(sticky=W,row=3,column=columnbase+1)
        
        #Adding the configure all FE-ASIC channels button
        feasic_config_button = Button(self, text="Config FE-ASIC", command=self.call_feasic_config)
        feasic_config_button.grid(row=4,column=columnbase,columnspan=2)

    def define_adcasic_config_commands_column(self):
        columnbase=30

        label = Label(self, text="ADC ASIC Configuration Commands")
        label.grid(row=0,column=columnbase)

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
        femb = None
        asic = None
        chan = None
        try:
          femb = int(self.femb_number_entry.get())
        except ValueError:
          self.selectChannel_result["text"] = "Error femb must be an int"
          return
        try:
          asic = int(self.asic_number_entry.get())
        except ValueError:
          self.selectChannel_result["text"] = "Error asic must be an int"
          return
        try:
          if self.channel_number_entry.get() != "ALL":
              chan = int(self.channel_number_entry.get())
          else: chan = self.channel_number_entry.get()
        except ValueError:
          self.selectChannel_result["text"] = "Error channel must be an int or ALL"
          return
        message = ""
        if femb < 0 or femb >=4 :
          self.selectChannel_result["text"] = "Error femb only from 0 to 3"
          return
        if asic < 0 or asic >= 7:
          self.selectChannel_result["text"] = "Error asic only from 0 to 7"
          return
        if chan != "ALL":
          if chan < 0 or chan >= 16:
            self.selectChannel_result["text"] = "Error channel only from 0 to 15 or ALL"
            return
        self.femb_config.selectFemb(femb)
        self.femb_config.selectChannel(asic,chan)
        self.selectChannel_result["text"] = ""

        #WIB specific
        if isinstance( chan, int ): self.trace_fft_window.selChan = chan
        self.call_reset_plot()

    def call_feasic_config(self):
        gain = GAINVALS.index(self.feasic_config_gain_entry.get())
        shape = SHAPEVALS.index(self.feasic_config_shape_entry.get())
        base = BASEVALS.index(self.feasic_config_base_entry.get())
        self.femb_config.configFeAsic(gain,shape,base)

    def call_set_pulser(self):
        enabled = self.pulser_enable_var.get()
        if not(enabled == 0 or enabled == 1):
           raise ValueError("Pulser enabled must be 0 or 1")
        pulseHeight = None
        try:
          pulseHeight = int(self.pulser_height_entry.get())
        except ValueError:
          self.pulser_result["text"] = "Error pulseHeight must be an int"
          return
        if pulseHeight < 0 or pulseHeight >= 32:
          self.pulser_result["text"] = "Error pulseHeight must be 0 to 31"
          return
        self.pulser_result["text"] = ""
        self.femb_config.setInternalPulser(enabled,pulseHeight)

    def call_adcasic_config(self):
        print("call_adcasic_config")
        enabled = self.adc_offset_enable_var.get()
        if not(enabled == 0 or enabled == 1):
           raise ValueError("Pulser enabled must be 0 or 1")
        offsetCurrent = None
        try:
          offsetCurrent = int(self.adc_offset_current_entry.get())
        except ValueError:
          self.adc_result["text"] = "Error offsetCurrent must be an int"
          return
        if offsetCurrent < 0 or offsetCurrent >= 16:
          self.adc_result["text"] = "Error offsetCurrent must be 0 to 15"
          return
        self.adc_result["text"] = ""

        f2default = 0
        clkdefault = "fifo"
        if hasattr(self.femb_config,"F2DEFAULT"):
            f2default = self.femb_config.F2DEFAULT
        if hasattr(self.femb_config,"CLKDEFAULT"):
            clkdefault = self.femb_config.CLKDEFAULT

        clockMonostable = False
        clockExternal = False
        clockFromFIFO = False
        if clkdefault=="fifo":
          clockFromFIFO = True
        elif clkdefault=="monostable":
          clockMonostable = True
        elif clkdefault=="external":
          clockExternal = True
        else:
          print("Error: CLKDEFAULT='{}' not one of the allowed options. Try fife, monostable, or external..".format(clkdefault))

        self.femb_config.configAdcAsic(enableOffsetCurrent=enabled,offsetCurrent=offsetCurrent,f2=f2default,clockMonostable=clockMonostable,clockExternal=clockExternal,clockFromFIFO=clockFromFIFO,pdsr=1,pcsr=1)
        #nRetries = 5
        #for iRetry in range(nRetries):
        #    self.femb_config.configAdcAsic(enableOffsetCurrent=enabled,offsetCurrent=offsetCurrent,f2=f2default,clockMonostable=clockMonostable,clockExternal=clockExternal,clockFromFIFO=clockFromFIFO)
        #    # Check that board streams data
        #    data = self.femb.get_data(1)
        #    if data == None:
        #        print("Board not streaming data, retrying initialization...")
        #        continue # try initializing again
        #    self.adc_result["text"] = ""
        #    return
        #self.adc_result["text"] = "Board not streaming data after {} tries".format(nRetries)

    def call_sync_adc(self):
        print("call_sync_adc")
        message = "Sync Error"
        isAlreadySynced, latchloc1, latchloc2, phase = self.femb_config.syncADC()
        if isAlreadySynced: 
           message = "Already Sync'd"
        else:

      	   message = "Sync'd: latch latency " + str(hex(latchloc1)) + str(hex(latchloc2)) + "\tPhase " + str(hex(phase))
        self.adc_sync_result["text"] = message

    def call_quit(self):
        print("call_adcasic_config")

    def call_reset_plot(self):
        selChan = self.channel_number_entry.get()
        if self.trace_fft_window:
            self.trace_fft_window.destroy()
        if selChan == "ALL":
            self.trace_fft_window = Toplevel(self)
            self.trace_fft_window.title("Trace FFT Window")
            self.trace_fft = TRACE_FFT_ALLCHAN_WINDOW(self.trace_fft_window)
        else:
            self.trace_fft_window = Toplevel(self)
            self.trace_fft_window.title("Trace FFT Window")
            self.trace_fft = TRACE_FFT_WINDOW(self.trace_fft_window)
###################################################

def main():
  
  root = Tk()
  root.title("Configuration Window")
  window = CONFIGURATION_WINDOW(root)
  window.call_reset_plot()
  root.mainloop()

if __name__ == '__main__':
    main()
