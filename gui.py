#!/usr/bin/python3.4
from time import sleep
from gi.repository import Gtk
from femb_config import FEMB_CONFIG

import numpy as np
from matplotlib import pyplot

from subprocess import Popen

class GUI_WINDOW():

    #GUI window defined entirely in init function
    #individual sub-panes/frames defined in functions to keep things organized
    #Note: main_hbox is the main container, it's a class member so functions can access it
    def __init__(self):

        #define configuration object
        self.femb_config = FEMB_CONFIG()

        #do any checks here for system state

        #define main GUI window
        window = Gtk.Window()
        window.set_title("Live Feed")
        window.set_default_size(600, 150)
        window.set_position(Gtk.WindowPosition.CENTER)
        window.connect('destroy', self.destroy)

        self.main_hbox = Gtk.HBox(True,0)
        window.add(self.main_hbox)

        #Define general commands column
        self.define_general_commands_column()

        #Define configuration commands column
        self.define_config_commands_column()

        #Define fe-asic configuration column
        self.define_feasic_config_commands_column()

        #Define adc asic configuration column
        self.define_adcasic_config_commands_column()

        #Show GUI
        window.show_all()

        #call plots
        self.plot_process = Popen(["python", "plot_data.py"])

    def define_general_commands_column(self):
        #Define general commands column-----------------------------------
        frame_cmd = Gtk.Frame()
        frame_cmd.set_label("General Commands")
        self.main_hbox.pack_start(frame_cmd, True, True, 10) 

        vbox_cmd = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        frame_cmd.add(vbox_cmd)

        #add general command buttons column

        #add select register button + associated field to command column
        selectreg_box = Gtk.HBox(True,0)
        vbox_cmd.pack_start(selectreg_box, False, False, 0)

        selectreg_label = Gtk.Label("Select Register")
        selectreg_box.pack_start(selectreg_label, True, True, 0)

        self.selectreg_entry = Gtk.Entry()
        self.selectreg_entry.set_text("6")
        selectreg_box.pack_start(self.selectreg_entry, True, True, 0)

        #add read register button + associated field to command column
        readreg_box = Gtk.HBox(True,0)
        vbox_cmd.pack_start(readreg_box, False, False, 0)

        readreg_button = Gtk.Button.new_with_label("Read Register")
        readreg_button.connect("clicked", self.call_readRegister)
        readreg_box.pack_start(readreg_button, True, True, 0)

        self.readreg_entry = Gtk.Entry()
        self.readreg_entry.set_text("Register Value")
        readreg_box.pack_start(self.readreg_entry, True, True, 0)

        #add write register button + associated field to command column
        writereg_box = Gtk.HBox(True,0)
        vbox_cmd.pack_start(writereg_box, False, False, 0)

        writereg_button = Gtk.Button.new_with_label("Write Register")
        writereg_button.connect("clicked", self.call_writeRegister)
        writereg_box.pack_start(writereg_button, True, True, 0)

        self.writereg_entry = Gtk.Entry()
        self.writereg_entry.set_text("Enter Register Value")
        writereg_box.pack_start(self.writereg_entry,True, True, 0)

        #add reset plot button to command column
        reset_plot_button = Gtk.Button.new_with_label("Reset Plots")
        reset_plot_button.connect("clicked", self.reset_plot)
        vbox_cmd.pack_start(reset_plot_button, False, False, 0)

        #add quit button to command column
        quit_button = Gtk.Button.new_with_label("QUIT")
        quit_button.connect("clicked", self.destroy)
        vbox_cmd.pack_start(quit_button, False, False, 0)

        #END general commands column-----------------------------------

    def define_config_commands_column(self):
        #Define configuration command column-----------------------------------
        frame_config = Gtk.Frame()
        frame_config.set_label("Configuration Commands")
        self.main_hbox.pack_start(frame_config, True, True, 10) 

        vbox_config = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        frame_config.add(vbox_config)

        #add reset button
        reset_box = Gtk.HBox(True,0)
        vbox_config.pack_start(reset_box, False, False, 0)

        reset_button = Gtk.Button.new_with_label("Reset")
        reset_button.connect("clicked", self.call_reset)
        reset_box.pack_start(reset_button, True, True, 0)

        #add initialization button
        init_box = Gtk.HBox(True,0)
        vbox_config.pack_start(init_box, False, False, 0)

        init_button = Gtk.Button.new_with_label("Initialize")
        init_button.connect("clicked", self.call_initialize)
        init_box.pack_start(init_button, True, True, 0)

        init_entry = Gtk.Entry()
        init_entry.set_text("Initialization Status")
        init_box.pack_start(init_entry, True, True, 0)

        #add select channel button + associated field to configuration column
        selectChannel_box = Gtk.HBox(True,0)
        vbox_config.pack_start(selectChannel_box, False, False, 0)

        selectChannel_button = Gtk.Button.new_with_label("Select Channel")
        selectChannel_button.connect("clicked", self.call_selectChannel)
        selectChannel_box.pack_start(selectChannel_button, True, True, 0)

        self.selectChannel_entry = Gtk.Entry()
        self.selectChannel_entry.set_text("0")
        selectChannel_box.pack_start(self.selectChannel_entry, True, True, 0)

        #End configuration command column-----------------------------------

    def define_feasic_config_commands_column(self):
        #Define FE ASIC configuration column-----------------------------------
        frame_feasic_config = Gtk.Frame()
        frame_feasic_config.set_label("FE-ASIC Configuration")
        self.main_hbox.pack_start(frame_feasic_config, True, True, 10) 

        vbox_feasic_config = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        frame_feasic_config.add(vbox_feasic_config)

        #add configure all FE-ASIC channels button
        feasic_config_box = Gtk.HBox(True,0)
        vbox_feasic_config.pack_start(feasic_config_box, False, False, 0)

        feasic_config_button = Gtk.Button.new_with_label("Config FE-ASIC")
        feasic_config_button.connect("clicked", self.call_feasic_config)
        feasic_config_box.pack_start(feasic_config_button, True, True, 0)

        #add gain select box
        selgain_box = Gtk.HBox(True,0)
        vbox_feasic_config.pack_start(selgain_box, False, False, 0)

        selgain_label = Gtk.Label("Gain")
        selgain_box.pack_start(selgain_label, True, True, 0)

        self.gainval_combo = Gtk.ComboBoxText()
        # values should be obtained from config object, hardcode for now
        self.gainval_combo.append_text("4.7 mV/fC")
        self.gainval_combo.append_text("7.8 mV/fC")
        self.gainval_combo.append_text("14 mV/fC")
        self.gainval_combo.append_text("25 mV/fC")
        self.gainval_combo.set_active(0)
        selgain_box.pack_start(self.gainval_combo, True, True, 0)

        #add shaping time select box
        selshape_box = Gtk.HBox(True,0)
        vbox_feasic_config.pack_start(selshape_box, False, False, 0)

        selshape_label = Gtk.Label("Shape")
        selshape_box.pack_start(selshape_label, True, True, 0)

        self.selshape_combo = Gtk.ComboBoxText()
        # values should be obtained from config object, hardcode for now
        self.selshape_combo.append_text("0.5 us")
        self.selshape_combo.append_text("1 us")
        self.selshape_combo.append_text("2 us")
        self.selshape_combo.append_text("3 us")
        self.selshape_combo.set_active(0)
        selshape_box.pack_start(self.selshape_combo, True, True, 0)

        #add baseline select box
        selbase_box = Gtk.HBox(True,0)
        vbox_feasic_config.pack_start(selbase_box, False, False, 0)

        selbase_label = Gtk.Label("Baseline")
        selbase_box.pack_start(selbase_label, True, True, 0)

        self.selbase_combo = Gtk.ComboBoxText()
        # values should be obtained from config object, hardcode for now
        self.selbase_combo.append_text("200 mV")
        self.selbase_combo.append_text("900 mV")
        self.selbase_combo.set_active(0)
        selbase_box.pack_start(self.selbase_combo, True, True, 0)

        #END FE ASIC configuration column-----------------------------------

    def define_adcasic_config_commands_column(self):
        #Define FE ASIC configuration column-----------------------------------
        frame_adcasic_config = Gtk.Frame()
        frame_adcasic_config.set_label("ADC ASIC Configuration")
        self.main_hbox.pack_start(frame_adcasic_config, True, True, 10) 

        vbox_adcasic_config = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        frame_adcasic_config.add(vbox_adcasic_config)

        #add configure all ADC-ASIC channels button
        adc_config_box = Gtk.HBox(True,0)
        vbox_adcasic_config.pack_start(adc_config_box, False, False, 0)

        adc_config_button = Gtk.Button.new_with_label("Config ADC ASIC")
        adc_config_button.connect("clicked", self.call_adcasic_config)
        adc_config_box.pack_start(adc_config_button, True, True, 0)

        #END ADC ASIC configuration column-----------------------------------   

    def call_readRegister(self, button):
        #print " call_readRegiste"
        #print str(self.readreg_entry.get_text())
        regVal = self.femb_config.femb.read_reg(self.selectreg_entry.get_text())
        if regVal != None:
                self.readreg_entry.set_text(str(hex(regVal)))
  
    def call_writeRegister(self, button):
        #print "call_writeRegister"
        #print str(self.writereg_entry.get_text())
        regNum = self.femb_config.femb.write_reg(self.selectreg_entry.get_text(),self.writereg_entry.get_text())

    def call_reset(self, button):
        #print "call_initialize"
        self.femb_config.resetBoard()

    def call_initialize(self, button):
        #print "call_initialize"
        self.femb_config.initBoard()

    def call_selectChannel(self, button):
        #print str(self.selectChannel_entry.get_text())
        chVal = int(self.selectChannel_entry.get_text())
        # need to get min + max channel values from femb_config object
        if (chVal < 0) or (chVal >= 128):
                return
        asic = chVal / 16
        chan = chVal % 16
        self.femb_config.selectChannel(asic,chan)

    def call_feasic_config(self, button):
        #print "call_initialize"
        gainInd = int(self.gainval_combo.get_active())
        shapeInd = int(self.selshape_combo.get_active())
        baseInd = int(self.selbase_combo.get_active())
        self.femb_config.configFeAsic(gainInd,shapeInd,baseInd)

    def call_adcasic_config(self, button):
        print("call_adcasic_config")
        #self.femb_config.initBoard()

    def reset_plot(self, button):
        self.plot_process.kill()
        self.plot_process = Popen(["python", "plot_data.py" ])

    def destroy(self, window):
        self.plot_process.kill()
        Gtk.main_quit()

def main():
    app = GUI_WINDOW()
    Gtk.main()

if __name__ == '__main__':
    main()
