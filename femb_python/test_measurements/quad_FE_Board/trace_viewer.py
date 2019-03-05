# -*- coding: utf-8 -*-
"""
Created on Fri Feb  1 12:24:57 2019

@author: eraguzin

This module contains a class that displays a live ADC readout and its FFT for all
16 channels of an ASIC:
               
1 | 2 | 3 | 4  
---------------
5 | 6 | 7 | 8  
---------------
9 | 10| 11| 12
---------------
13| 14| 15| 16

Configurations handled elsewhere.

"""
from __future__ import division
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()

import datetime
import re


import matplotlib
matplotlib.use("TkAgg")
import matplotlib.gridspec as gridspec

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg as FigureCanvas
from matplotlib.backends.backend_tkagg import NavigationToolbar2TkAgg as NavigationToolbar
from matplotlib.figure import Figure
from matplotlib import animation
from femb_python.configuration import CONFIG
from femb_python.configuration.config_base import FEMB_CONFIG_BASE

import tkinter as Tk

matplotlib.rc('xtick',labelsize=8)
matplotlib.rc('ytick',labelsize=8)

class TRACE_VIEWER(Tk.Frame):
  """
  This window displays a live ADC readout
  """
  
  def __init__(self, master=None):  
    
    self.config = CONFIG
    self.functions = FEMB_CONFIG_BASE(self.config)
    #Gets the low level module to do UDP packets
    self.femb = self.functions.lower_functions
    self.master = master
    
    self.functions.configFeAsic(test_cap="on", base=self.config["SYNC_SETTINGS"]["SYNC_BASELINE"], gain=self.config["SYNC_SETTINGS"]["SYNC_GAIN"], shape=self.config["SYNC_SETTINGS"]["SYNC_PEAK"], 
                                        monitor_ch=None, buffer=self.config["SYNC_SETTINGS"]["SYNC_BUFFER"], leak = self.config["SYNC_SETTINGS"]["SYNC_LEAK"], monitor_param = None, s16=None, 
                                        acdc=self.config["SYNC_SETTINGS"]["SYNC_ACDC"], test_dac="test_int", dac_value=int(self.config["SYNC_SETTINGS"]["SYNC_DAC_PEAK_HEIGHT"]))
    self.functions.writeFE()
    #Creates Tkinter object
    Tk.Frame.__init__(self,master) # hack to make work in python2
    self.pack()
    #Creates Matplotlib object
    self.figure = Figure(figsize=(20,7), dpi=100, facecolor='white')
    self.canvas = FigureCanvas(self.figure, master=self)
    self.canvas.show()
    self.canvas.get_tk_widget().pack(side=Tk.TOP, fill=Tk.BOTH, expand=1)
    #Create toolbar for bottom
    self.toolbar = NavigationToolbar(self.canvas,self)
    self.toolbar.update()

    self.pauseButton = Tk.Button(self,text="Pause",command=self.pause)
    self.pauseButton.pack(side=Tk.LEFT)

    self.playButton = Tk.Button(self,text="Play",command=self.play,state=Tk.DISABLED)
    self.playButton.pack(side=Tk.LEFT)
    
    pulse_options = ["None", "Internal Pulse", "External Pulse"]
    self.pulse_entry_choices = Tk.StringVar(self.master, name = "pulse_entry")
    self.pulse_entry_choices.set(pulse_options[0]) # initial value
    self.pulse_entry_choices.trace("w", self.gui_callback)
    
    self.pulse_entry = Tk.OptionMenu(self, self.pulse_entry_choices, *pulse_options)
    self.pulse_entry.pack(side=Tk.LEFT)
    
    self.chip = 0
    chip_options = []
    for i in range(int(self.config["DEFAULT"]["NASICS"])):
        chip_options.append("Chip {}".format(i))
        
    self.chip_entry_choices = Tk.StringVar(self.master, name = "chip_entry")
    self.chip_entry_choices.set(chip_options[0]) # initial value
    self.chip_entry_choices.trace("w", self.gui_callback)
    
    self.chip_entry = Tk.OptionMenu(self, self.chip_entry_choices, *chip_options)
    self.chip_entry.pack(side=Tk.LEFT)
    
    self.packets = 2
    self.packet_label = Tk.Label(self,text="Packet Length:",width=11)
    self.packet_label.pack(side=Tk.LEFT)
    self.packet_entry = Tk.Spinbox(self, width = 5, from_=1, to=100, name = "patcket_entry", command = self.packet_change)
    self.packet_entry.delete(0,"end")
    self.packet_entry.insert(0,self.packets)
    self.packet_entry.pack(side=Tk.LEFT)
    
    self.manualSyncButton = Tk.Button(self,text="Manual Sync",command=self.manualSync)
    self.manualSyncButton.pack(side=Tk.LEFT)
    
    self.reset()

  def reset(self):
    self.figure.clf()
    self.subgs = [None]*16
    self.ax = [None]*16
    self.plot = [None]*16
    
    self.figure.text(0.5,0.02,'Time [us]',ha='center',color='black',fontsize='25.0',weight='bold')
    self.figure.text(0.08,0.625,'ADC counts',ha='center',rotation=90,color='black',fontsize='25.0',weight='bold') 

    # 4x4 grid, one cell per channel
    self.gs  = gridspec.GridSpec(4,4)
    self.gs.update(wspace=0.2,hspace=0.2)
    # 1 plots per channel, create axes objects
    for row in range(4):
      for col in range(4):        
        ch = col+4*row
        self.subgs[ch] = gridspec.GridSpecFromSubplotSpec(1, 1, subplot_spec=self.gs[ch],hspace=0.0)
        self.ax[ch] = self.figure.add_subplot(self.subgs[ch][0])
        self.ax[ch].tick_params(axis='x', colors='black',labelsize='medium')
        self.ax[ch].tick_params(axis='y', colors='black',labelsize='smaller')
        

    #Continually updates by calling self.plotData
    self.ani = animation.FuncAnimation(self.figure, self.plotData, interval=1000, blit=True)
    self.canvas.draw()
    
  def packet_change(self):
      self.packets = int(self.packet_entry.get())
    
  def gui_callback(self,*args,**kwargs):
      if (args[0] == "pulse_entry"):
          if (self.pulse_entry_choices.get() == "None"):
              self.femb.femb_udp.write_reg(int(self.config["REGISTERS"]["REG_MUX_MODE"]), int(self.config["DEFINITIONS"]["MUX_GND_GND"]))
          elif (self.pulse_entry_choices.get() == "Internal Pulse"):
              self.femb.femb_udp.write_reg(int(self.config["REGISTERS"]["REG_MUX_MODE"]), int(self.config["DEFINITIONS"]["MUX_GND_GND_INTPULSE"]))
          elif (self.pulse_entry_choices.get() == "External Pulse"):
              self.femb.femb_udp.write_reg(int(self.config["REGISTERS"]["REG_MUX_MODE"]), int(self.config["DEFINITIONS"]["MUX_GND_DACPULSE"]))
                
      elif (args[0] == "chip_entry"):
         self.chip = int(re.findall(r'\d+',self.chip_entry_choices.get())[0])

  def pause(self):
    self.ani.event_source.stop()
    self.pauseButton['state'] = Tk.DISABLED
    self.playButton['state'] = Tk.NORMAL

  def play(self):
    self.ani.event_source.start()
    self.pauseButton['state'] = Tk.NORMAL
    self.playButton['state'] = Tk.DISABLED

  def plotData(self, iFrame):
    for a in self.ax:
        #Clears all previous traces
        a.cla()
        #Limits the number of traces on each subplot
        a.locator_params(tight=True, nbins=3)

    #In case no data, return an empty plot
#    self.plot[0] = self.ax[0].plot()
    t, adc, thistimestamp = self.getData()
    for r in range(4):
        for c in range(4):
            ch = c+4*r
            if not (t is None) and not (adc is None):
                self.plot[ch] = self.ax[ch].plot(t,adc[ch])
                if ch < 12: self.ax[ch].set_xticklabels([])
                self.ax[ch].title.set_text("Channel {}".format(ch))
    

    if not (thistimestamp is None):
        self.figure.suptitle(thistimestamp.replace(microsecond=0).isoformat(" "))
    self.canvas.draw()
    return self.plot[0]
    
  def closeSync(self):
      self.syncWindow.destroy()
      self.syncWindow.quit()
      self.syncWindow = None
    
  def manualSync(self):
      self.syncWindow = Tk.Toplevel(self.master)
      self.app = manSync(self.syncWindow, config = self.config, femb = self.femb)
      self.syncWindow.title("Manual Synchronization")
    
  def getData(self):
    """
    Gets trace from FEMB and returns 4 1D arrays:
        times, ADC counts
    """
    
    data = self.femb.get_data_chipX(chip = self.chip, packets = self.packets, data_format = "counts", tagged = False, header = False)
#    data = [[1,2,3,4,5,6,7,8,9,10]]*16
    timestamp = datetime.datetime.now()

    if data == None:
        return None, None, None
    if len(data) == 0:
        return None, None, None

    xpoint = []
    for num,samp in enumerate(data[0]):
      xpoint.append(num*float(self.config["DEFAULT"]["SAMPLE_PERIOD"]))

    return xpoint, data, timestamp
    
class manSync(Tk.Frame):
    def __init__(self, master, config, femb):
        self.master = master
        Tk.Frame.__init__(self,self.master)
        self.pack()
        self.config = config
        self.femb = femb
        
        self.sync_fields = []
        
        self.buildGUI()
        
    #TODO if anything changes, rebuild sync registers and send
    def sync_change(self, *args, **kwargs):

        for i in range(int(self.config["DEFAULT"]["NASICS"])):
            shift_reg = i + int(self.config["REGISTERS"]["REG_LATCH_MIN"])
            phase_reg = i + int(self.config["REGISTERS"]["REG_PHASE_MIN"])
        
            shift_setting = 0
            phase_setting = 0
            for j in range(int(self.config["DEFAULT"]["NASICCH"])):
                shift_value = int(self.nametowidget("latch_entry{}-{}".format(i,j)).get())
                shift_setting = shift_setting + (shift_value << (2*j))
                
                phase_value = int(self.nametowidget("phase_entry{}-{}".format(i,j)).get())
                phase_setting = phase_setting + (phase_value << (2*j))
                
            self.femb.femb_udp.write_reg(shift_reg, shift_setting)
            self.femb.femb_udp.write_reg(phase_reg, phase_setting)
        
    def buildGUI(self):
        for i in range(int(self.config["DEFAULT"]["NASICCH"])):
            label = Tk.Label(self, text="Channel {}".format(i))
            label.grid(row=i+2,column=0, columnspan=1)

        for i in range(int(self.config["DEFAULT"]["NASICS"])):
            label = Tk.Label(self, text="Chip {} settings".format(i))
            label.grid(row=0,column=1 + (2*i), columnspan=2)
            
        for i in range(int(self.config["DEFAULT"]["NASICS"])):
            latchLabel = Tk.Label(self, text="Latch")
            phaseLabel = Tk.Label(self, text="Phase")
            latchLabel.grid(row=1,column=1 + (2*i), columnspan=1)
            phaseLabel.grid(row=1,column=2 + (2*i), columnspan=1)

        for i in range(int(self.config["DEFAULT"]["NASICS"])):
            shift_reg = i + int(self.config["REGISTERS"]["REG_LATCH_MIN"])
            phase_reg = i + int(self.config["REGISTERS"]["REG_PHASE_MIN"])
            
            shift_value = self.femb.femb_udp.read_reg(shift_reg)
            phase_value = self.femb.femb_udp.read_reg(phase_reg)
        
            for j in range(int(self.config["DEFAULT"]["NASICCH"])):
                initial_shift = (shift_value >> (2*j)) & 0x3
                initial_phase = (phase_value >> (2*j)) & 0x3
                
                self.latch_entry = Tk.Spinbox(self, width = 5, from_=0, to=3, name = "latch_entry{}-{}".format(i,j), command = self.sync_change)
                self.latch_entry.delete(0,"end")
                self.latch_entry.insert(0,initial_shift)
                self.latch_entry.grid(row=2+j,column=1 + (2*i), columnspan=1)
                
                self.phase_entry = Tk.Spinbox(self, width = 5, from_=0, to=3, name = "phase_entry{}-{}".format(i,j), command = self.sync_change)
                self.phase_entry.delete(0,"end")
                self.phase_entry.insert(0,initial_phase)
                self.phase_entry.grid(row=2+j,column=2 + (2*i), columnspan=1)
                
                
                self.sync_fields.append(self.latch_entry)
                self.sync_fields.append(self.phase_entry)
                
    def close_windows(self):
        self.master.destroy()
          
def main_start(window):
    window.title("Full Chip Waveform Viewer")
    TRACE_VIEWER(window)
    window.mainloop()
    window.quit()