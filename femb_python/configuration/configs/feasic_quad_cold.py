#!/usr/bin/env python33

import sys 
import time
import os
#import visa
#from visa import VisaIOError
import matplotlib.pyplot as plt
import numpy as np
import pickle

from femb_python.configuration.config_base import FEMB_CONFIG_BASE
from femb_python.test_measurements.quad_FE_Board.fe_asic_reg_mapping import FE_ASIC_REG_MAPPING
from femb_python.test_measurements.quad_FE_Board.detect_peaks import detect_peaks
from femb_python.test_measurements.quad_FE_Board.plotting import plot_functions

#TODO add functions for the LEDs to do
class FEMB_CONFIG2(FEMB_CONFIG_BASE):
    #__INIT__#
    def __init__(self):
        
        #declare board specific registers
        #REQUIRED SETTINGS#################################################################################
        #These settings need to be filled in for each new hardware configuration, or else it will not work!

        self.FEMB = "quadFE"
        self.NASICS = 4
        self.NASICCH = 16
        self.FE_ASIC_VER = 7
        #REGISTER DEFINITIONS
        
        #Global Reset
        self.REG_RESET = 0
        #Initiates an SPI
        self.REG_FEASIC_SPI = 5
        self.FEASIC_SPI_RESET = 2
        self.FEASIC_SPI_START = 1
        self.FEASIC_SPI_STOP = 0
        #Registers that hold settings to write during SPI
        self.REG_FESPI_BASE = 20
        #ASIC Readback registers (done internally now)
        self.REG_FESPI_RDBACK_BASE = None
        self.REG_ADCSPI_RDBACK_BASE = None 
        #Channel mode vs. WIB mode readout
        self.REG_HS = 17
        self.REG_TEST_PULSE = 99
        self.REG_TEST_PULSE_FREQ = 500
        self.REG_TEST_PULSE_DLY = 80
        self.REG_TEST_PULSE_AMPL = 0 % 32
        self.REG_EN_CALI = 16
        self.REG_ON_OFF = 12
        self.REG_CH_SEL = 4
        #For the sampling scope option Jack put in the FE Quad board
        self.REG_SS = 10
        #For the mux configurations on the quad board
        self.REG_MUX_MODE = 9
        
        self.REG_TAGGING = 74

        self.REG_TIMEOUT = 76
        self.REG_SAMPLESPEED = 75        
        self.REG_FW_VER = 0x64
        
        self.latest_fw = 0x204
        #UDP Packet header size in bytes
        self.header_size = 16
        self.default_ss = 0
        
        #Info for packet number location
        self.packet_num1 = ">1I"
        self.packet_num2 = 0
        
        self.adc = "LTC2314"
        self.adc_full_scale = 0x3FFF
        self.TAGGING_ON = 1
        self.TAGGING_OFF = 0
        #in microsends.  This affects plots only
        self.sample_period = 0.5
        
        #MUX Options
        self.default_mux = 8
        self.MUX_internal_pulser = 3
        
        #Readout Options
        self.REG_READOUT_OPTIONS = 60
        self.READOUT_NORMAL = 0
        self.READOUT_TEST_ADC = 1
        
        #Internal DAC
        self.REG_INTERNAL = 17
        self.sync_INTERNAL_PERIOD = 800
        self.sync_INTERNAL_SHIFT = 0
        self.sync_INTERNAL_ON = 0b01000000
        self.sync_INTERNAL_OFF = 0
        
        #Settings for the discrete DAC that sits on the PCB, if there is one
        self.has_PCB_DAC = True
        self.PCB_DAC_VAL_MAX = 0xFFFF
        
        self.PCB_DAC_STOP = 0
        self.PCB_DAC_START = 1
        self.REG_PCB_DAC_VAL = 1
        self.REG_PCB_DAC_SET = 2
        self.REG_PCB_DAC_TIMING=7
        
        self.default_PCB_DAC = 0x270
        #The period in sampling counts
        self.default_PCB_DAC_TP_Period = 800
        #Addition to the period in 80 MHz counts
        self.default_PCB_DAC_TP_Shift = 0
    
        #GUI SETTINGS#################################################################################
        #Settings specific to the GUI
        self.known_test_stands = ["1", "2", "3", "Other"]
        self.known_quad_boards = ["2v0", "3v0", "Other"]
        self.known_fpga_mezzanines = ["FM17", "FM43", "16", "Other"]
        self.known_chip_versions = ["7", "8", "Other"]
        self.chip_range = [0,2000]
        self.socket_range = [0,200]
        
        
        self.default_file_name = "defaults.json"
#        self.comm_settings = None

        self.fe_reg = FE_ASIC_REG_MAPPING()
        self.plot = plot_functions(sample_period = self.sample_period)
        
        self.WIB_RESET = 1
        
        self.BPS = 13 #Bytes per sample
        self.selected_chip = None
        self.selected_chn = None    
        
        self.baseArray = ["200mV", "900mV"]
        self.gainArray = ["4.7mV", "7.8mV", "14mV", "25mV"]
        self.shapeArray = ["0.5us", "1us", "2us", "3us"]
        self.buffArray = ["b_off", "b_on"]
        
        #GENERAL SETTINGS#################################################################################
        #The temp you're saying the run was at.  This affects how the analysis looks at the test pulses
        #Since both DACs give slightly different values at different temperatures
        self.chips_to_use = [0,1,2,3]
#        self.chip_num = 4

#        self.FEMB_VER = "Quad FE Chip Tester with v0x201 Firmware"
        self.default_frame_size = 0x01f8
        self.default_timeout = 0x00005000
        self.default_sample_speed = 0x26
        
        #POWER SETTINGS#####################################################################################
        #Settings for the power supply
        self.ps_heating_chn = 1
        self.ps_quad_chn = 2
        self.ps_fpga_chn = 3
        
        
        #SYNC SETTINGS#####################################################################################
        self.Latch_Settings_default = [0x00000000, 0x00000000, 0x00000000, 0x00000000]
        self.Phase_Settings_default = [0x00000000, 0x00000000, 0x00000000, 0x00000000]
        self.Latch_Settings = {'1v0': [0x00000000, 0x00000000, 0x00000000, 0x00000000],'2v0': [0x00000000, 0x00000000, 0x00000000, 0x00000000],'3v0': [0x00000000, 0x00000000, 0x00000000, 0x00000000]}
        self.Phase_Settings = {'1v0': [0x55555555, 0x51401550, 0x55555555, 0x01555004], '2v0': [0x00000000, 0x00000000, 0x00000000, 0x00000000], '3v0': [0x01000005, 0x00000000, 0x55555555, 0x00000000]}
        self.test_ADC_Settings = 0x000000C8
        
        self.REG_Latch_Min = 65
        self.REG_Latch_Max = 68
        self.REG_Phase_Min = 69
        self.REG_Phase_Max = 72
        self.REG_Test_ADC = 73
        
        self.sync_baseline = "200mV"
        self.sync_gain = "14mV"
        self.sync_pulse = "2us"
        self.sync_leak = "500pA"
        self.sync_buffer = "off"
        self.sync_peak_min = 3500
        self.sync_peak_max = 7500
        self.sync_peak_height = 11
        self.sync_desired_peaks = 5
        self.sync_baseline_min = 1000
        self.sync_baseline_max = 3500
        self.sync_baseline_r = 15
        self.sync_high_freq_noise_max = 100000
        
        self.pulse_spacing = 200
        #TEST SETTINGS#####################################################################################
        #Amount of data to collect per packet
        self.baseline_length = 5
        self.alive_length = 5
        self.pulse_length = 25
        self.monitor_length = 5
        self.DAC_length = 5
        
        #Settings for the pulse during the "alive" test
        self.test_DAC_in = 0x390
        self.test_DAC_mon = 0x1390
        self.test_TP_Period = 0x64
        self.test_TP_Shift = 0x0
        self.power_cycles = 3
        
        #The bounds to measure the DAC output and the timing of the pulse for during the DAC output test
        self.DAC_meas_min = 0
        self.DAC_meas_max = 0x3F
        self.DAC_freq = 0x800
        self.DAC_delay = 0x0
        
        #Pulse timing settings for the monitor test
        self.monitor_freq = 800
        self.monitor_delay = 0x0
        self.monitor_amplitude = 15
        
        #Pulse timing settings for the gain calibration test
        self.pulse_freq = 4000
        self.pulse_delay_amplitude = 15
        self.pulse_delay_min = 0
        self.pulse_delay_max = 25
        self.pulse_DAC_min = 0
        self.pulse_DAC_max = 0x3F
        
        #BASELINE ANALYSIS SETTINGS########################################################################
        #Upper and lower bounds for the mean value of the baseline in mV
        self.baseline_200_reject_max = 700
        self.baseline_200_acceptable_max = 700
        self.baseline_200_good_max = 700
        self.baseline_200_good_min = 100
        self.baseline_200_acceptable_min = 100
        self.baseline_200_reject_min = 100
        
        self.baseline_900_reject_max = 1100
        self.baseline_900_acceptable_max = 1100
        self.baseline_900_good_max = 1100
        self.baseline_900_good_min = 700
        self.baseline_900_acceptable_min = 700
        self.baseline_900_reject_min = 700
        
        #Upper and lower bounds for the standard deviation (noise) in electrons        
        self.noise_reject_max = 800
        self.noise_acceptable_max = 600
        self.noise_good_max = 400
        self.noise_good_min = 300
        self.noise_acceptable_min = 200
        self.noise_reject_min = 150
        
        #CHANNEL ALIVE ANALYSIS SETTINGS###################################################################
        self.test_peak_min = 430
        self.under_max = 200
        self.test_peaks_min = 2
        self.test_peaks_max = 25

        self.alive_plot_x_back = 100
        self.alive_plot_x_forward = 100
        
        #PULSE ANALYSIS SETTINGS##########################################################################
        self.pulse_47_min = 3
        self.pulse_47_max = 5
        self.pulse_78_min = 6
        self.pulse_78_max = 8
        self.pulse_14_min = 12
        self.pulse_14_max = 15
        self.pulse_25_min = 20
        self.pulse_25_max = 26  
        
        #DAC STEP ANALYSIS SETTINGS#######################################################################
        self.ideal_DAC_step = 18.75
        self.min_DAC_step = 0x02
        self.max_DAC_step = 0x3F
        self.DAC_peak_min = 45
        
        #MONITOR ANALYSIS SETTINGS########################################################################
        self.monitor_peak_min = 400
        self.monitor_peak_max = 1200
        self.monitor_peaks_min = 2
        self.monitor_peaks_max = 20

        self.monitor_plot_x_back = 100
        self.monitor_plot_x_forward = 100      
        
        #Acceptable range shading values for the plots
        self.red = 'FF0000'
        self.blue = '0000FF'
        self.white = 'FFFFFF'
        self.green = '006400'
        self.yellow = 'FFFF00'
        self.alpha = 0.1
        
        self.Baseline_Naming = "Baseline_ch{}_{}_{}_{}_{}_{}.dat"
        self.Monitor_Naming = "Monitor_ch_{}.dat"
        self.Alive_Naming = "Alive_ch{}_{}_{}.dat"
        self.Alive_Naming2 = "Alive_ch{}_{}_{}_{}.dat"
        
        self.bits_to_mv = (2048.0 / 16384)
        self.bits_to_V = (2.048 / 16384)
        
        super().__init__()
        
    def additional_init_commands(self, **kwargs):
        self.selectChipChannel(chip = 2, chn = 7)
        self.selectChipChannel(chip = 1, chn = 6)
        board = kwargs["board"]
        if board in self.Latch_Settings:
            print("FEASIC_QUAD--> Using settings for {}".format(board))
            latch = self.Latch_Settings[board]
            phase = self.Phase_Settings[board]
        else:
            print("FEASIC_QUAD--> Using default settings for {}".format(board))
            latch = self.Latch_Settings_default
            phase = self.Phase_Settings_default
            
        for i,reg in enumerate([65,66,67,68]):
            self.femb.write_reg(reg, latch[i])
        for i,reg in enumerate([69,70,71,72]):
            self.femb.write_reg(reg, phase[i])
        self.femb.write_reg(73, self.test_ADC_Settings)
    def sync_prep_output(self):
        #Tells the FPGA to turn on each DAC
#        self.write_reg(61, 0x0)
        
        #Read from DATA output ADCs
        self.femb.write_reg(self.REG_READOUT_OPTIONS, self.READOUT_NORMAL)
        
        #Select the internal DAC readout
        self.femb.write_reg(self.REG_MUX_MODE, self.MUX_internal_pulser)
        
        #Adds tracer bits on data coming in when the internal pulser has an edge
        self.femb.write_reg(self.REG_TAGGING, self.TAGGING_ON)
        
        #Get the ASIC to send out pulses
        self.set_internal_DAC(period = self.sync_INTERNAL_PERIOD, shift = self.sync_INTERNAL_SHIFT, enable = True)
        self.configFeAsic(test_cap="on", base=self.sync_baseline, gain=self.sync_gain, shape=self.sync_pulse, monitor_ch=None, buffer=self.sync_buffer, 
                       leak = self.sync_leak, monitor_param = None, s16=None, acdc="dc", test_dac="test_int", dac_value=self.sync_peak_height)
        self.writeFE()
        
    def sync_prep_test(self, chip):
        #Have one of the channels output its pulse to the test monitor pin
        self.FE_Regs.set_fe_chn(chip = chip, chn = 0, smn = 1)
        self.writeFE()
        
        #Read from TEST output ADCs
        self.femb.write_reg(self.REG_READOUT_OPTIONS, self.READOUT_TEST_ADC)
        
        #Select the monitor readout
        self.femb.write_reg(9, self.MUX_internal_pulser)
        
    def sync_finish(self):
        #Read from TEST output ADCs
        self.femb.write_reg(self.REG_READOUT_OPTIONS, self.READOUT_NORMAL)
        self.femb.write_reg(self.REG_TAGGING, self.TAGGING_OFF)
        self.set_internal_DAC(period = self.sync_INTERNAL_PERIOD, shift = self.sync_INTERNAL_SHIFT, enable = False)