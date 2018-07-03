#!/usr/bin/env python33

import sys 
import time
import os
#import visa
#from visa import VisaIOError
import matplotlib.pyplot as plt
import numpy as np
import pickle

from femb_python.test_measurements.sbnd_femb_test.femb_udp_cmdline import FEMB_UDP
from femb_python.configuration.config_base import FEMB_CONFIG_BASE
from femb_python.test_measurements.sbnd_femb_test.fe_asic_reg_mapping import FE_ASIC_REG_MAPPING
from femb_python.test_measurements.sbnd_femb_test.detect_peaks import detect_peaks
from femb_python.test_measurements.sbnd_femb_test.plotting import plot_functions

class FEMB_CONFIG(FEMB_CONFIG_BASE):
    #__INIT__#
    def __init__(self):
        super().__init__()
        #declare board specific registers
        self.FEMB_VER = "quadasictest"
        self.NASICS = 4
        self.NASICCH = 16
        
        self.REG_RESET = 0
        self.REG_FEASIC_SPI = 5
        self.REG_FESPI_BASE = 20
        self.REG_FESPI_RDBACK_BASE = None
        self.REG_ADCSPI_RDBACK_BASE = None 
        self.REG_HS = 17
        self.REG_TEST_PULSE = 99
        self.REG_TEST_PULSE_FREQ = 500
        self.REG_TEST_PULSE_DLY = 80
        self.REG_TEST_PULSE_AMPL = 0 % 32
        self.REG_EN_CALI = 16
#        self.plot = plot_functions()
        
        self.comm_settings = None

        #initialize FEMB UDP object
        self.femb = FEMB_UDP()
        self.fe_reg = FE_ASIC_REG_MAPPING()
        self.plot = plot_functions()
        
        self.WIB_RESET = 1
        
        self.BPS = 13 #Bytes per sample
        self.selected_chip = None
        self.selected_chn = None    
        
        #from Eric's user_settings function
        self.channels = 16
        self.chip_num=4
        self.PC_IP= '192.168.121.50'
        self.frame_size=0x02cb
        self.default_DAC = 0x270
        self.default_TP_Period = 800
        self.default_TP_Shift = 0
        self.pre_buffer = 200
        
        self.Latch_Settings = [0x00000000, 0x00000000, 0x00000000, 0x00000000]
        self.Phase_Settings = [0x00000000, 0x00000000, 0x00000000, 0x00000000]
        self.test_ADC_Settings = 0x000000C8
        self.Sample_Clock_Settings = [0x00000000, 0x00000000]
        
        self.sync_peak_min = 3500
        self.sync_peak_max = 7500
        self.sync_peak_height = 11
        self.sync_peaks_max = 90
        self.sync_baseline_min = 0
        self.sync_baseline_max = 3000
        
        #for fe_reg mapping
        self.fe_regs_sw = None
        self.fe_regs_sent = None
        
        #GENERAL SETTINGS#################################################################################
        #The temp you're saying the run was at.  This affects how the analysis looks at the test pulses
        #Since both DACs give slightly different values at different temperatures
        self.temp       = "LN"
        self.chips_to_use = [0,1,2,3]
        self.chip_num = 4
        #Which IP addresses you gave those 4 sockets
        self.PC_IP = '192.168.121.50'
        self.FPGA_IP = "192.168.121.1"
        self.FEMB_VER = "Quad FE Chip Tester with v0x201 Firmware"
        self.frame_size = 0x02cb
        
        #SYNC SETTINGS#####################################################################################
        self.default_DAC = 0x270
        self.default_TP_Period = 800
        self.default_TP_Shift = 0
        self.pre_buffer = 200
        
        self.Latch_Settings = [0x00000000, 0x00000000, 0x00000000, 0x00000000]
        self.Phase_Settings = [0x00000000, 0x00000000, 0x00000000, 0x00000000]
        self.test_ADC_Settings = 0x000000C8
        self.Sample_Clock_Settings = [0x00000000, 0x00000000]
        
        self.sync_peak_min = 3500
        self.sync_peak_max = 7500
        self.sync_peak_height = 11
        self.sync_peaks_max = 90
        self.sync_baseline_min = 0
        self.sync_baseline_max = 3500
        
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
        self.test_peak_min = 450
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
        
        self.channels = 16
        
        #mapping of settings
        self.baseArray = ["200mV", "900mV"]
        self.gainArray = ["4.7mV", "7.8mV", "14mV", "25mV"]
        self.shapeArray = ["0.5us", "1us", "2us", "3us"]
        self.buffArray = ["b_off", "b_on"]
    def leakArray(self,leak):
        if leak == "100pA": return [0,1]
        elif leak == "500pA": return [0,0]
        elif leak == "1nA": return [1,1]        
        elif leak == "5nA": return [1,0]
        else: return "Not an appropriate leak parameter"
    def testArray(self,test):
        if test == "test_off": return [0,0]
        elif test == "test_int": return [0,1]
        elif test == "test_ext": return [1,0]
        elif test == "test_meas": return [1,1]
        else: return "Not a good test paramater"
        
    def turnOffAsics(self):
        self.femb.write_reg(12, 0xF)
        #pause after turning off ASICs
        time.sleep(1)
        
    def turnOnAsics(self):
        self.femb.write_reg(12,0x0)
        #pause after turning on ASICSs
        time.sleep(1)
    
    def resetFEMBBoard(self):
        print ("FEMB_CONFIG--> Reset FEMB (4 seconds)")
        sys.stdout.flush()
        #Reset FEMB system
        self.femb.write_reg ( self.REG_RESET, 1)
        time.sleep(4)
        print ("FEMB_CONFIG--> Reset FEMB is DONE")

    def initBoard(self):
        print ("FEMB_CONFIG--> Initialize FEMB")
        #set up default registers
        
        #Tells the FPGA to turn on the ASICs
        self.femb.write_reg(12, 0x0)
        
        #Tells the FPGA to turn off each DAC
        self.femb.write_reg(61, 0xF)

        #Set to Regular Mode (as opposed to Sampling Scope mode) and pick a chip/channel output
        self.femb.write_reg(10, 0)
        self.select_chip_chn(chip = 2, chn = 7)
        
        #Select TP FE Mode
        self.femb.write_reg(9, 8)
        
        #Allows internal DAC to pulse
        self.femb.write_reg(13, 0)
        
        #Give a default DAC value
        self.femb.write_reg(1, self.default_DAC)
        self.femb.write_reg(2, 1)
        self.femb.write_reg(2, 0)
        
        #Give a default pulse timing
        self.femb.write_reg(7, (self.default_TP_Shift << 16) + self.default_TP_Period)

        #Write the default ADC settings
        i = 0
        for reg in range(65, 69, 1):
            self.femb.write_reg(reg, self.Latch_Settings[i])
            i = i + 1
            
        i = 0
        for reg in range(69, 73, 1):
            self.femb.write_reg(reg, self.Phase_Settings[i])
            i = i + 1
            
        self.femb.write_reg(73, self.test_ADC_Settings)
        
        self.femb.write_reg(74, self.pre_buffer)
        
        i = 0
        for reg in range(75, 77, 1):
            self.femb.write_reg(reg, self.Sample_Clock_Settings[i])
            i = i + 1
            
        #Write the frame size as a multiple of 16
        frame_size = self.frame_size
        if (frame_size%16 != 0):
            frame_size = 16 * (frame_size//16)

        #Write the default ASIC settings
        self.fe_reg.set_fe_board(sts=1, snc=1, sg=1, st=1, smn=0, sbf=1, 
                       slk = 0, stb = 0, s16=0, slkh=0, sdc=0, sdacsw2=1, sdacsw1=0, sdac=self.sync_peak_height)

        self.configFeAsic()
        
        print ("FEMB_CONFIG--> Initialize FEMB is DONE")
        

    def configFeAsic(self, to_print = False):
        #Grab ASIC settings from linked class
        Feasic_regs = self.fe_reg.REGS
        #print(Feasic_regs)
        #Choose to output status updates or not
        if (to_print == True):
            print ("FEMB_CONFIG--> Config FE ASIC SPI")
        #Try 10 times (ocassionally it wont work the first time)
        for k in range(10):
            i = 0
            for regNum in range(self.REG_FESPI_BASE,self.REG_FESPI_BASE+len(Feasic_regs),1):
                    self.femb.write_reg( regNum, Feasic_regs[i])
#                    print (hex(Feasic_regs[i]))
                    i = i + 1
                    
            #Write ADC ASIC SPI
            if (to_print == True):
                print ("FEMB_CONFIG--> Program FE ASIC SPI")
            #Reset, then write twice
            self.femb.write_reg ( self.REG_FEASIC_SPI, 2)
            self.femb.write_reg ( self.REG_FEASIC_SPI, 0)
            time.sleep(.2)
            self.femb.write_reg ( self.REG_FEASIC_SPI, 1)
            self.femb.write_reg ( self.REG_FEASIC_SPI, 0)
            time.sleep(.2)
            self.femb.write_reg ( self.REG_FEASIC_SPI, 1)
            self.femb.write_reg ( self.REG_FEASIC_SPI, 0)
            time.sleep(.2)
            
            if (to_print == True):
                print ("FEMB_CONFIG--> Check FE ASIC SPI")

            #The FPGA automatically compares the readback to check if it matches what was written.  That result is read back
            #A bit that's zero means the corresponding ASIC didn't write properly
            val = self.femb.read_reg(self.REG_FEASIC_SPI) 
            wrong = False

            if (((val & 0x10000) >> 16) != 1 and (0 in self.chips_to_use)):
                print ("FEMB_CONFIG--> Something went wrong when programming FE 1")
                wrong = True
                
            if (((val & 0x20000) >> 17) != 1 and (1 in self.chips_to_use)):
                print ("FEMB_CONFIG--> Something went wrong when programming FE 2")
                wrong = True
                
            if (((val & 0x40000) >> 18) != 1 and (2 in self.chips_to_use)):
                print ("FEMB_CONFIG--> Something went wrong when programming FE 3")
                wrong = True
                
            if (((val & 0x80000) >> 19) != 1 and (3 in self.chips_to_use)):
                print ("FEMB_CONFIG--> Something went wrong when programming FE 4")
                wrong = True

            if (wrong == True and k == 9):
                print ("FEMB_CONFIG--> SPI_Status is {}").format(hex(val))
                sys.exit("FEMB_CONFIG--> femb_config_femb : Wrong readback. FE SPI failed")
                return
                
            elif (wrong == False): 
                self.fe_reg.info.fe_regs_sent = Feasic_regs
                if (to_print == True):
                    print ("FEMB_CONFIG--> FE ASIC SPI is OK")
                break        
            
            
        
        
    #ASSUMES ASICS HAVE BEEN SET FOR THE INTERNAL PULSER
    def syncADC(self, datadir, chiplist, datasubdir, saveresults=False): 
        print ("FEMB_CONFIG--> Start sync ADC")
        chips = self.chips_to_use
        #Don't ask me why, but you need to set the channel at this point for it to output the right data
        self.select_chip_chn(chip = 0, chn = 1)
            
        for chip in chips:            
            outputfile = os.path.join(datadir,chiplist[chip][1],datasubdir,"syncOutput.txt")            
            savefigpath = os.path.join(datadir,chiplist[chip][1],datasubdir,"syncplots")
            os.makedirs(savefigpath)
            with open(outputfile, 'w') as f:
                #Tells the FPGA to turn on each DAC
                self.femb.write_reg(61, 0x0)
                
                #Read from DATA output ADCs
                self.femb.write_reg(60, 0)
    
                #Set to Regular Mode (not sampling scope mode)
                self.femb.write_reg(10, 0)
                
                #Select the internal DAC readout
                self.femb.write_reg(9, 3)
    
                #Get the ASIC to send out pulses.  Bit 6 needs to be high for ASIC DAC
                self.reg_17_value = (self.default_TP_Period << 16) + (self.default_TP_Shift << 8) + (0b01000000)
                self.femb.write_reg(17, self.reg_17_value)
                
                
                print ("FEMB_CONFIG--> Test ADC {}".format(chip))
                if saveresults:
                    f.write("FEMB_CONFIG--> Test ADC {}\n".format(chip))
                for chn in range(self.channels):
                    #Tests if it's synchronized, returns True if it is
                    unsync = self.testUnsync(f, savefigpath, saveresults, chip = chip, chn = chn)
                    if unsync != True:
                        #print ("FEMB_CONFIG--> Chip {}, Chn {} not synced, try to fix".format(chip, chn))
                        if saveresults:
                            f.write("FEMB_CONFIG--> Chip {}, Chn {} not synced, try to fix\n".format(chip, chn))
                        response = self.fixUnsync_outputADC(f, savefigpath, saveresults, chip = chip, chn = chn)
                        if (response != True):
                            #print ("FEMB_CONFIG--> Something is wrong with Chip {}, Chn {}".format(chip, chn))
                            if saveresults:
                                f.write("FEMB_CONFIG--> Something is wrong with Chip {}, Chn {}\n".format(chip, chn))
    #                        sys.exit ("FEMB_CONFIG--> ADC {} could not sync".format(chip))
    
                #print ("FEMB_CONFIG--> ADC {} synced!".format(chip))
                if saveresults:
                    f.write("FEMB_CONFIG--> ADC {} synced!\n".format(chip))
                
                #print ("FEMB_CONFIG--> Trying to sync test ADC".format(chip))
                if saveresults:
                    f.write("FEMB_CONFIG--> Trying to sync test ADC\n".format(chip))
                
                #Have one of the channels output its pulse to the test monitor pin
                self.fe_reg.set_fe_chn(chip = chip, chn = 0, smn = 1)
                self.configFeAsic()
                
                #Read from TEST output ADCs
                self.femb.write_reg(60, 1)
                
                #Select the monitor readout
                self.femb.write_reg(9, 3)
                
                unsync = self.testUnsync(f, savefigpath, saveresults, chip = chip, chn = chn)
                if unsync != True:
                    #print ("FEMB_CONFIG--> Chip {} (test ADC) not synced, try to fix".format(chip))
                    if saveresults:
                        f.write("FEMB_CONFIG--> Chip {} (test ADC) not synced, try to fix\n".format(chip))
                    response = self.fixUnsync_testADC(f, savefigpath, saveresults, chip = chip)
                    if (response != True):
                        #print ("FEMB_CONFIG--> Something is wrong with Chip {} (test ADC)".format(chip))
                        if saveresults:
                            f.write("FEMB_CONFIG--> Something is wrong with Chip {} (test ADC)\n".format(chip))
                else:
                    print ("FEMB_CONFIG--> Chip {} (test ADC) synced!".format(chip))
                    if saveresults:
                        f.write("FEMB_CONFIG--> Chip {} (test ADC) synced!\n".format(chip))
            
            #clean up if not debugging sync output
            if not saveresults:
                os.remove(outputfile)
                os.rmdir(savefigpath)
                
        outputfile = os.path.join(datadir,"syncresults.txt")
        with open(outputfile, 'w') as f:
            self.comm_settings = []
            print ("FEMB_CONFIG--> Final Shift Settings: ")
            if saveresults:
                f.write("FEMB_CONFIG--> Final Shift Settings: \n")
            for reg in range(65, 69, 1):
                value = self.femb.read_reg(reg)
                print("Register {}: {}".format(reg, hex(value)))
                if saveresults:
                    f.write("Register {}: {}\n".format(reg, hex(value)))
                self.comm_settings.append(value)
    
            print ("FEMB_CONFIG--> Final Phase Settings: ")
            if saveresults:
                f.write("FEMB_CONFIG--> Final Phase Settings: \n")
            for reg in range(69, 73, 1):
                value = self.femb.read_reg(reg)
                #print("Register {}: {}".format(reg, hex(value)))
                if saveresults:
                    f.write("Register {}: {}\n".format(reg, hex(value)))
                self.comm_settings.append(value)
            
            for reg in range(73,77,1):
                value = self.femb.read_reg(reg)
                #print("Register {}: {}".format(reg, hex(value)))
                if saveresults:
                    f.write("Register {}: {}\n".format(reg, hex(value)))
                self.comm_settings.append(value)
            
            self.femb.write_reg(17, 0)
                
            print ("FEMB_CONFIG--> ADC passed Sync Test!")
            if saveresults:
                f.write("FEMB_CONFIG--> ADC passed Sync Test!\n")
        
        #clean up if not saving output
        if not saveresults:
            os.remove(outputfile)

    def testUnsync(self, f, savefigpath, saveresults, chip, chn):
        #Get some packets of data
        self.select_chip_chn(chip = chip, chn = chn)
        packets = 25
        data = self.get_data_chipXchnX(chip = chip, chn = chn, packets = packets, data_format = "counts")
        
        #Find some peaks
        peaks_index = detect_peaks(x=data, mph=self.sync_peak_min, mpd=100) 
        #Make sure you have more than 0 peaks (so it's not flat) and less than the maximum 
        #(if there's no peak, the baseline will give hundreds of peaks)
        #If it's bad, print it, so we see (must enable inline printing for iPython)
#        figure_data = self.plot.quickPlot(data)
#        ax = figure_data[0]
#        for j in peaks_index:
#            y_value = data[j]
#            ax.scatter(j/2, y_value, marker='x')
#            
#        ax.set_ylabel('mV')
#        ax.set_title("Error")
#        ax.title.set_fontsize(30)
#        for item in ([ax.xaxis.label, ax.yaxis.label] +ax.get_xticklabels() + ax.get_yticklabels()):
#            item.set_fontsize(20)
#        plt.show()
#        plt.close()
        if (len(peaks_index) == 0) or (len(peaks_index) > packets):
            #print ("Chip {}, Channel {} has {} peaks!".format(chip, chn, len(peaks_index)))
            if saveresults:            
                f.write("Chip {}, Channel {} has {} peaks!\n".format(chip, chn, len(peaks_index)))
#            print (peaks_index)
            return False
            
        #So that function before only gives you the X locations of where the peaks are.  Let's get the Y values from that
        peaks_value = []
        for i in peaks_index :
            peaks_value.append(data[i])
#        print ("Chip {}, Channel {} has peak values {}".format(chip, chn, peaks_value))
        #Check if the peak is at the wrong height (happens when it's not synced, the peak will be havled or doubled)
        for peak in peaks_value:
            if ((peak < self.sync_peak_min) or (peak > self.sync_peak_max)):
                #print ("FEMB CONFIG--> Chip {}, Chn {} has a peak that's {}".format(chip, chn, peak))
                if saveresults:
                    f.write("FEMB CONFIG--> Chip {}, Chn {} has a peak that's {}\n".format(chip, chn, peak))
                    figure_data = self.plot.quickPlot(data)
                    ax = figure_data[0]
                    for j in peaks_index:
                        y_value = data[j]
                        ax.scatter(j/2, y_value, marker='x')
                        
                    ax.set_ylabel('mV')
                    ax.set_title("Error")
                    ax.title.set_fontsize(30)
                    for item in ([ax.xaxis.label, ax.yaxis.label] +ax.get_xticklabels() + ax.get_yticklabels()):
                        item.set_fontsize(20)
                    plt.savefig(os.path.join(savefigpath,"chip{}chn{}peak{}.jpg".format(chip,chn,peak)))
                    plt.close()
                    return False 
        #Check if the baseline is right (this also gets halved and doubled with unsynced ADCs) (avoid the peak to grab a middle section)
        try:
            baseline_area_start = peaks_index[0] + 200
            baseline_area_end = peaks_index[1] - 200
        except IndexError:
            baseline_area_start = 100
            baseline_area_end = 500
        baseline_data = data[baseline_area_start : baseline_area_end]
        baseline = np.mean(baseline_data)
        if ((baseline < self.sync_baseline_min) or (baseline > self.sync_baseline_max)):
            #print ("FEMB CONFIG--> Chip {}, Chn {} has a baseline that's {}".format(chip, chn, baseline))
            if saveresults:
                f.write("FEMB CONFIG--> Chip {}, Chn {} has a baseline that's {}\n".format(chip, chn, baseline))
                figure_data = self.plot.quickPlot(data)
                ax = figure_data[0]
                for j in peaks_index:
                    y_value = data[j]
                    ax.scatter(j/2, y_value, marker='x')
                    
                ax.set_ylabel('mV')
                ax.set_title("Error")
                ax.title.set_fontsize(30)
                for item in ([ax.xaxis.label, ax.yaxis.label] +ax.get_xticklabels() + ax.get_yticklabels()):
                    item.set_fontsize(20)
                plt.savefig(os.path.join(savefigpath,"chip{}chn{}baseline{}.jpg".format(chip,chn,baseline)))
                plt.close()
                return False 
        return True
            
    #Shifts through all possible delay and phase options, checking to see if each one fixed the issue

    def fixUnsync_outputADC(self, f, savefigpath, saveresults, chip, chn):
        self.select_chip_chn(chip = chip, chn = chn)
        
        shift_reg = chip + 65
        phase_reg = chip + 69
        sample_reg = 75 + (chip//2)
        
        #Get the initial setting you don't disturb the other channels
        init_shift = self.femb.read_reg(shift_reg)
        init_phase = self.femb.read_reg(phase_reg)
        init_sample= self.femb.read_reg(sample_reg)

        #Because Python can't have a friggin NAND or XOR function that works right at the bitwise level, this is how we get the bitmask
        #This will find the 2 bits in the register that correspond to the channel you want to change.  Say it's channel 2
        #In binary, it makes 0b00000000000000000000000000110000
        #Then inverts it to  0b11111111111111111111111111001111
        #Now you AND that with the initial result to get the initial values WITHOUT the channel you want to change
        #Now you can bitshift your desired setting to that empty space with zeroes, like say you wanted to write a 0b10,
        #It would be 0b100000.  Then add that to whatever the result of the initial values AND mask was.  Boom, you've done it.
        init_mask = (0x3 << (2 * chn))
        neg_mask = 0
        for i in range(32):
            FF_bit = (0xFFFFFFFF >> i) & 0x1
            test_bit = (init_mask >> i) & 0x1
            if (FF_bit != test_bit):
                result_bit = 1
            else:
                result_bit = 0
            neg_mask = neg_mask + (result_bit << i)
        
        #There are 16 possible sync permutations for every ADC
#        for sample_clock in range(2):
#            value = (sample_clock << chn) << (16 * (chip%2))
#            print ("Clock setting for chip {}, channel {} is {}".format(chip, chn, hex(value)))
#            self.femb.write_reg(sample_reg, value)
        for shift in range(4):
            for phase in range(4):
                
                shift_setting = shift << (2 * chn)
                init_shift_with_mask = init_shift & neg_mask
                final_shift = shift_setting + init_shift_with_mask
                
#                print ("Shift is {}".format(shift))
#                print ("phase is {}".format(phase))
#                print ("Negative mask is {}".format(bin(neg_mask)))                
#                print ("Initial reading is {}".format(bin(init_shift)))
#                print ("The new setting is {}".format(bin(shift_setting)))
#                print ("Making space for the new setting is {}".format(bin(init_shift_with_mask)))
#                print ("Adding together is {}".format(bin(final_shift)))
                
                self.femb.write_reg(shift_reg, final_shift)
                
                phase_setting = phase << (2 * chn)
                init_phase_with_mask = init_phase & neg_mask
                final_phase = phase_setting + init_phase_with_mask
                
                self.femb.write_reg(phase_reg, final_phase)
                
                #See if this new setting fixed it
                unsync = self.testUnsync(f, savefigpath, saveresults, chip = chip, chn = chn)
                if unsync == True:
                    #print ("FEMB_CONFIG--> Chip {}, Chn {} fixed!".format(chip, chn))
                    if saveresults:
                        f.write(("FEMB_CONFIG--> Chip {}, Chn {} fixed!\n".format(chip, chn)))
                    return True

        print ("FEMB_CONFIG--> ADC SYNC process failed for Chip {}, Channel {}".format(chip, chn))
        if saveresults:        
            f.write("FEMB_CONFIG--> ADC SYNC process failed for Chip {}, Channel {}\n".format(chip, chn))
        self.femb.write_reg(shift_reg, init_shift)
        self.femb.write_reg(phase_reg, init_phase)
        return False
        
    #Same thing as above, except the timing register is different, so the bitmath has to be changed.

    def fixUnsync_testADC(self, f, savefigpath, saveresults, chip):
        self.select_chip_chn(chip = chip, chn = 2)
        init_mask = (0xF << (2 * chip))
        
        neg_mask = 0
        for i in range(32):
            FF_bit = (0xFFFFFFFF >> i) & 0x1
            test_bit = (init_mask >> i) & 0x1
            if (FF_bit != test_bit):
                result_bit = 1
            else:
                result_bit = 0
            neg_mask = neg_mask + (result_bit << i)
            
        init_shift = self.femb.read_reg(73)          
        #print ("Init shift is {}".format(hex(init_shift)))
        if saveresults:
            f.write("Init shift is {}\n".format(hex(init_shift)))
        #print ("Init mask is {}".format(bin(init_mask)))    
        if saveresults:
            f.write("Init mask is {}\n".format(bin(init_mask))) 
        #print ("Negative mask is {}".format(bin(neg_mask))) 
        if saveresults:
            f.write("Negative mask is {}\n".format(bin(neg_mask)))
        for shift in range(4):
            for phase in range(4):
                setting = (phase << 2) + shift
                #print ("Setting is {}".format(bin(setting)))
                if saveresults:
                    f.write("Setting is {}\n".format(bin(setting)))
                
                final_setting = setting << (chip * 4)
                #print ("Final Setting is {}".format(bin(setting)))
                if saveresults:
                    f.write("Final Setting is {}\n".format(bin(setting)))
                
                init_shift_with_mask = init_shift & neg_mask
                #print ("Initshift with mask is {}".format(hex(init_shift_with_mask)))
                if saveresults:
                    f.write("Initshift with mask is {}\n".format(hex(init_shift_with_mask)))
                really_final = init_shift_with_mask + final_setting
                #print ("Final setting to write is {}".format(bin(really_final)))
                if saveresults:
                    f.write("Final setting to write is {}\n".format(bin(really_final)))
                
#                init_shift_with_mask = init_shift & neg_mask
#                final_shift = shift_setting + init_shift_with_mask
                
#                print ("Shift is {}".format(shift))
#                print ("phase is {}".format(phase))
#                print ("Negative mask is {}".format(bin(neg_mask)))                
#                print ("Initial reading is {}".format(bin(init_shift)))
#                print ("The new setting is {}".format(bin(shift_setting)))
#                print ("Making space for the new setting is {}".format(bin(init_shift_with_mask)))
#                print ("Adding together is {}".format(bin(final_shift)))
                
                self.femb.write_reg(73, really_final)
                unsync = self.testUnsync(f, savefigpath, saveresults, chip = chip, chn = 1)
                if unsync == True:
                    print ("FEMB_CONFIG--> Chip {} test ADC fixed!".format(chip))
                    if saveresults:                    
                        f.write("FEMB_CONFIG--> Chip {} test ADC fixed!\n".format(chip))
                    return True

        print ("FEMB_CONFIG--> ADC SYNC process failed for Chip {} ADC".format(chip))
        if saveresults:
            f.write("FEMB_CONFIG--> ADC SYNC process failed for Chip {} ADC\n".format(chip))
        self.femb.write_reg(73, init_shift)
        return False
        
    #Select the chip and channel and read it out.  And check that it was actually set.  It's weirdly a problem
 
    #Select the chip and channel and read it out.  And check that it was actually set.  It's weirdly a problem
    def select_chip_chn(self, chip, chn):
        if (chip < 0 ) or (chip > self.chip_num ):
            print ("FEMB CONFIG -> Error in get_data_chipXchnX: Chip must be between 0 and {}".format(self.chip_num))
            return
            
        if (chn < 0 ) or (chn > 15 ):
            print ("FEMB CONFIG -> Error in get_data_chipXchnX: Channel must be between 0 and 15")
            return
          
        chip_int = int(chip + 1)
        chn_int = int(chn)
        
        reg4_value = chn_int + (chip_int << 8)
        
        for i in range(10):
            self.femb.write_reg(4, reg4_value)
            time.sleep(0.1)
            reg4_read = self.femb.read_reg(4)     
            try:
                if ((reg4_read & 0xF) != chn) or (((reg4_read >> 8) & 0xF) != chip + 1):
                    if (i == 9):
                        sys.exit("FEMB CONFIG--> Register response was {}, should have been {}, trying again...".format(hex(reg4_read), hex(reg4_value)))
                    else:
                        print ("FEMB CONFIG--> Register response was {}, should have been {}, trying again...".format(hex(reg4_read), hex(reg4_value)))
                else:
                    self.selected_chip = chip
                    self.selected_chn = chn
                    break
            except TypeError:
                print ("FEMB CONFIG--> No readback value, trying again...")

    #Get data in a variety of ways.  You can even pre-convert it to mV!
    def get_data_chipXchnX(self, chip, chn, packets = 1, data_format = "counts"):
        
        if (chn < -1 ) or (chn > 15 ):
            print ("FEMB CONFIG -> Error in get_data_chipXchnX: Channel must be between 0 and 15, or -1 for all channels")
            return
        
        if (chip < 0 ) or (chip > self.chip_num ):
            print ("FEMB CONFIG -> Error in get_data_chipXchnX: Chip must be between 0 and {}, but it's {}".format(self.chip_num, chip))
            return
            
        if (self.selected_chip != chip) or (self.selected_chn != chn):
            self.select_chip_chn(chip = chip, chn = chn)
            
        if (data_format == "bin"):
            data = self.femb.get_data_packets(data_type = "bin", num = packets, header = True)

        data = self.femb.get_data_packets(data_type = "int", num = packets, header = False)
        
        if (data_format == "mV"):
            for i in range (len(data)):
                data[i] = data[i] * (0.0018 / 16384)
                
        elif (data_format == "V"):
            for i in range (len(data)):
                data[i] = data[i] * (1.8 / 16384)
                
        if (data_format == "triggered"):
            return data[1:]
        else:
            return data
        
    #Get a whole chip's worth of data
    def get_data_chipX(self, chip, packets = 1, data_format = "counts"):

        chip_data = [chip, [],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]]
        for chn in range(16):
            for i in range(packets):
                chip_data[chn + 1].extend(list(self.get_data_chipXchnX(chip, chn, packets = 1, data_format = data_format)[1:]))
        return chip_data
    
    #Placeholder for the full chip readout
    def get_data_chipXchnX_SS(self, chip, chn, packets = 1):
        
        if (chn < -1 ) or (chn > 15 ):
            print ("FEMB CONFIG -> Error in get_data_chipXchnX: Channel must be between 0 and 15, or -1 for all channels")
            return
        
        if (chip < 0 ) or (chip > self.chip_num ):
            print ("FEMB CONFIG -> Error in get_data_chipXchnX: Chip must be between 0 and {}, but it's {}".format(self.chip_num, chip))
            return
            
        if (self.selected_chip != chip) or (self.selected_chn != chn):
            self.select_chip(chip = chip, chn = chn)

        k = 0
        for i in range(10):
            
            data = self.femb.get_data_packets(data_type = "int", num = packets, header = False)
            
            try:
                if (k > 0):
                    print ("FEMB CONFIG --> Now doing another test")
                    print (hex(data[0]))
                    print (data[0] == 0xFACE)
                    print (data[0] != 0xFACE)
                if (data[0] != 0xFACE):
                    #If FACE isn't the first 2 bytes, do the equivalent of turning WIB mode off and then on and try again
                    self.femb.write_reg(3, chip+1)
                    self.select_chip(chip)
                            
                    if (k > 8):
                        print ("FEMB CONFIG --> Error in get_data_chipXchnX: Packet format error")
                        print (hex(data[0]))
                        print (data)
                        return None
                    else:
                        print ("FEMB CONFIG --> Error in get_data_chipXchnX: Packet format error, trying again...")
                        print ("k = {}".format(k))
                        print (data[0:13])
                        print (hex(data[0]))
                        print (data[0] == 0xFACE)
                        k += 1
                else:
                    break
            except IndexError:
                print ("FEMB CONFIG --> Something was wrong with the incoming data")
                print (data)
            
        test_length = len(data)
        
#        if ((test_length % self.BPS) != 0):
#            print ("FEMB CONFIG -> Error in get_data_chipXchnX: Irregular packet size")
#            print (data)
#            return None
        
        full_samples = test_length // self.BPS
        
        chn_data = []
        
        for i in range (full_samples):
            if (chn == 7):
                chn_data.append(data[(self.BPS*i)+1] & 0x0FFF)
            if (chn == 6):
                chn_data.append(((data[(self.BPS*i)+2] & 0x00FF) << 4) + ((data[(self.BPS*i)+1] & 0xF000) >> 12))
            if (chn == 5):
                chn_data.append(((data[(self.BPS*i)+3] & 0x000F) << 8) + ((data[(self.BPS*i)+2] & 0xFF00) >> 8))
            if (chn == 4):
                chn_data.append(((data[(self.BPS*i)+3] & 0xFFF0) >> 4))
            if (chn == 3):
                chn_data.append(data[(self.BPS*i)+4] & 0x0FFF)
            if (chn == 2):
                chn_data.append(((data[(self.BPS*i)+5] & 0x00FF) << 4) + ((data[(self.BPS*i)+4] & 0xF000) >> 12))
            if (chn == 1):
                chn_data.append(((data[(self.BPS*i)+6] & 0x000F) << 8) + ((data[(self.BPS*i)+5] & 0xFF00) >> 8))
            if (chn == 0):
                chn_data.append(((data[(self.BPS*i)+6] & 0xFFF0) >> 4))
            if (chn == 15):
                chn_data.append(data[(self.BPS*i)+7] & 0x0FFF)
            if (chn == 14):
                chn_data.append(((data[(self.BPS*i)+8] & 0x00FF) << 4) + ((data[(self.BPS*i)+7] & 0xF000) >> 12))
            if (chn == 13):
                chn_data.append(((data[(self.BPS*i)+9] & 0x000F) << 8) + ((data[(self.BPS*i)+8] & 0xFF00) >> 8))
            if (chn == 12):
                chn_data.append(((data[(self.BPS*i)+9] & 0xFFF0) >> 4))
            if (chn == 11):
                chn_data.append(data[(self.BPS*i)+10] & 0x0FFF)
            if (chn == 10):
                chn_data.append(((data[(self.BPS*i)+11] & 0x00FF) << 4) + ((data[(self.BPS*i)+10] & 0xF000) >> 12))
            if (chn == 9):
                chn_data.append(((data[(self.BPS*i)+12] & 0x000F) << 8) + ((data[(self.BPS*i)+11] & 0xFF00) >> 8))
            if (chn == 8):
                chn_data.append(((data[(self.BPS*i)+12] & 0xFFF0) >> 4))
            if (chn == -1):
                return (data)
            
        return chn_data

####sec_chn_reg only sets a channel register, the other registers remains as before
    def set_adc_chn(self, chip=0, chn=0, d=-1, pcsr=-1, pdsr=-1, slp=-1, tstin=-1):

        tuple_num = 5 * chip + ((15 - chn) // 4)
        #print ("----------------------------------------------------------------")
        #print ("Chip {}, Channel {} will choose tuple {}".format(chip,chn,tuple_num))
        #print ("Settings of d={}, pcsr={},pdsr={},slp={},tstin={}".format(d,pcsr,pdsr,slp,tstin))
        #print ("Original Tuple {} is {}".format(tuple_num, hex(self.REGS[tuple_num])))
        
        if (chn%4 == 3):
            bitshift = 0
            and_mask = 0xFFFFFF00
            
        elif (chn%4 == 2):
            bitshift = 8
            and_mask = 0xFFFF00FF
            
        elif (chn%4 == 1):
            bitshift = 16
            and_mask = 0xFF00FFFF
            
        elif (chn%4 == 0):
            bitshift = 24
            and_mask = 0x00FFFFFF
            
        else:
            print ("ADC_ASIC_REG_MAPPING-->Error: incorrect chip or channel")
                
        #now we have bitmasks assigned for each position, so we can easily isolate the two hex letters we want
        
        find_mask = (0xFF << bitshift)
        existing_settings = ((self.REGS[tuple_num] & find_mask) >> bitshift)
        
        #now existing_settings is simply the two hex letters that already exist for this channel before anything has been done
        
        #if the bit is not being changed, we can just keep the existing settings
        if (d != -1):
            d_bit = (((d&0x01)//0x01)<<7)+(((d&0x02)//0x02)<<6)+(((d&0x04)//0x04)<<5)+(((d&0x08)//0x08)<<4)
        else:
            d_bit = (existing_settings & 0xF0)
            
        if (pcsr != -1):
            pcsr_bit = ((pcsr&0x01)<<3)
        else:
            pcsr_bit = (existing_settings & 0x08)
            
        if (pdsr != -1):
            pdsr_bit = ((pdsr&0x01)<<2)
        else:
            pdsr_bit = (existing_settings & 0x04)
            
        if (slp != -1):
            slp_bit = ((slp&0x01)<<1)
        else:
            slp_bit = (existing_settings & 0x02)
            
        if (tstin != -1):
            tstin_bit = ((tstin&0x01)<<0)
        else:
            tstin_bit = (existing_settings & 0x00)
            
            
        chn_reg = d_bit + pcsr_bit + pdsr_bit + slp_bit  + tstin_bit

        or_mask = (chn_reg << bitshift)

        self.REGS[tuple_num] = self.REGS[tuple_num] & (and_mask)
    
#---------------------------INPORT FE_ASIC_REG_MAPPING------------------------------------                 
    def set_fe_chn(self, chip, chn, sts=-1, snc=-1, sg=-1, st=-1, smn=-1, sbf=-1):

        #to find which array the channel/chip combination belongs in, then the specific byte of the array for the chip
        tuple_num = ((15 - chn) // 4) + (5 * chip)
        
        if (chn%4 == 3):
            bitshift = 0
            and_mask = 0xFFFFFF00
            
        elif (chn%4 == 2):
            bitshift = 8
            and_mask = 0xFFFF00FF
            
        elif (chn%4 == 1):
            bitshift = 16
            and_mask = 0xFF00FFFF
            
        elif (chn%4 == 0):
            bitshift = 24
            and_mask = 0x00FFFFFF
            
        else:
            print ("FE_ASIC_REG_MAPPING--> Error: incorrect chip or channel")
                
        #now we have bitmasks assigned for each position, so we can easily isolate the two hex letters we want
        
        find_mask = (0xFF << bitshift)
        existing_settings = ((self.REGS[tuple_num] & find_mask) >> bitshift)
        
        #now existing_settings is simply the two hex letters that already exist for this channel before anything has been done
        
        #if the bit is not being changed, we can just keep the existing settings
        if (sts != -1):
            sts_bit = ((sts&0x01)<<7)
        else:
            sts_bit = (existing_settings & 0x80)
            
        if (snc != -1):
            snc_bit = ((snc&0x01)<<6)
        else:
            snc_bit = (existing_settings & 0x40)
            
        if (sg != -1):
            sg_bit = ((sg&0x03)<<4)
        else:
            sg_bit = (existing_settings & 0x30)
            
        if (st != -1):
            st_bit = ((st&0x03)<<2)
        else:
            st_bit = (existing_settings & 0x0c)
            
        if (smn != -1):
            smn_bit = ((smn&0x01)<<1)
        else:
            smn_bit = (existing_settings & 0x02)
            
        if (sbf != -1):
            sbf_bit = ((sbf&0x01)<<0)
        else:
            sbf_bit = (existing_settings & 0x01)
            
        chn_reg = sts_bit + snc_bit + sg_bit + st_bit  + smn_bit + sbf_bit

        or_mask = (chn_reg << bitshift)

        self.REGS[tuple_num] = self.REGS[tuple_num] & (and_mask)
        
        self.REGS[tuple_num] = self.REGS[tuple_num] | (or_mask)

####sec_chip_global only sets a chip global register, the other registers remains as before
    def set_fe_global(self, chip, slk = -1, stb = -1, s16=-1, slkh=-1, sdc=-1, sdacsw2=-1, sdacsw1=-1, sdac=-1):

        tuple_num = (5 * chip) + 4
        existing_settings = self.REGS[tuple_num]
        
        if (sdac != -1):
            sdac_bit = (((sdac&0x01)//0x01)<<15)+(((sdac&0x02)//0x02)<<14)+\
                       (((sdac&0x04)//0x04)<<13)+(((sdac&0x08)//0x08)<<12)+\
                       (((sdac&0x10)//0x10)<<11)+(((sdac&0x20)//0x20)<<10)
        else:
            sdac_bit = (existing_settings & 0xfc00)
            
        if (sdacsw1 != -1):
            sdacsw1_bit = (((sdacsw1&0x01))<<9)
        else:
            sdacsw1_bit = (existing_settings & 0x0200)
            
        if (sdacsw2 != -1):
            sdacsw2_bit = (((sdacsw2&0x01))<<8)
        else:
            sdacsw2_bit = (existing_settings & 0x0100)
            
        if (sdc != -1):
            sdc_bit = (((sdc&0x01))<<5)
        else:
            sdc_bit = (existing_settings & 0x0020)
            
        if (slkh != -1):
            slkh_bit = ((slkh&0x01)<<4)
        else:
            slkh_bit = (existing_settings & 0x0010)
            
        if (s16 != -1):
            s16_bit = ((s16&0x01)<<3)
        else:
            s16_bit = (existing_settings & 0x0008)
            
        if (stb != -1):
            stb_bit = ((stb&0x03)<<1)
        else:
            stb_bit = (existing_settings & 0x0006)
            
        if (slk != -1):
            slk_bit = ((slk&0x01)<<0)
        else:
            slk_bit = (existing_settings & 0x0001)
            
        glo_reg = sdac_bit + sdacsw1_bit + sdacsw2_bit + sdc_bit + slkh_bit + s16_bit + stb_bit + slk_bit

        self.REGS[tuple_num] = glo_reg

####sec_chip sets registers of a whole chip, registers of the other chips remains as before
    def set_fe_chip(self, chip,
                 sts=0, snc=0, sg=0, st=0, smn=0, sbf=0,
                 slk=0, stb=0, s16=0, slkh=0, sdc=0, sdacsw2=0, sdacsw1=0, sdac=0):
        for chn in range(16):
            self.set_fe_chn(chip, chn, sts, snc, sg, st, smn, sbf)     

        self.set_fe_global (chip, slk, stb, s16, slkh, sdc, sdacsw2, sdacsw1, sdac)

####sec_sbnd_board sets registers of a whole board 
    def set_fe_board(self, sts=0, snc=0, sg=0, st=0, smn=0, sbf=0, 
                       slk = 0, stb = 0, s16=0, slkh=0, sdc=0, sdacsw2=0, sdacsw1=0, sdac=0):
        for chip in range (self.chip_num):
            self.set_fe_chip(chip, sts, snc, sg, st, smn, sbf, slk, stb, s16, slkh, sdc, sdacsw2, sdacsw1, sdac)
        
#-----------------------START FE_INFO-------------------------------------------------
    def fe_chip_status(self,chip=0,status="sent"):
        
        if (status == "sent"):
            fe_regs = self.fe_regs_sent
            if (fe_regs == None):
                print ("No registers have been written to the board yet")
                return
        elif (status == "to send"):
            fe_regs = self.fe_regs_sw
                
        else:
            print ("Incorrect status, do you want to see the registers that are 'to send'?  Or the ones 'sent'?")
            return
            
        headers = ["Channel", "Test Cap", "Baseline", "Gain", "Peaking Time", "Monitor", "Buffer", ]
        registers=[["0"],["1"],["2"],["3"],["4"],["5"],["6"],["7"],["8"],["9"],["10"],["11"],["12"],["13"],["14"],["15"],]

        for chn in range(16):
            spot = ((20*chip) + (15 - chn))
            tuple_num = (spot // 4)
            if (chn%4 == 0):
                bitshift = 24
            elif (chn%4 == 1):
                bitshift = 16
            elif (chn%4 == 2):
                bitshift = 8
            elif (chn%4 == 3):
                bitshift = 0
        #now we have bitmasks assigned for each position, so we can easily isolate the two hex letters we want
            find_mask = (0xFF << bitshift)
            existing_settings = ((fe_regs[tuple_num] & find_mask) >> bitshift)
            
            if ((existing_settings & 0x80)>>7 == 1):
                registers[chn].append("On")
            else:
                registers[chn].append("Off")
    
            if ((existing_settings & 0x40)>>6 == 1):
                registers[chn].append("200 mV")
            else:
                registers[chn].append("900 mV")
                
            if ((existing_settings & 0x30)>>4 == 0):
                registers[chn].append("4.7 mV/fC")
            elif ((existing_settings & 0x30)>>4 == 1):
                registers[chn].append("14 mV/fC")
            elif ((existing_settings & 0x30)>>4 == 2):
                registers[chn].append("7.8 mV/fC")
            else:
                registers[chn].append("25 mV/fC")
                
            if ((existing_settings & 0x0c)>>2 == 0):
                registers[chn].append("1 us")
            elif ((existing_settings & 0x0c)>>2 == 1):
                registers[chn].append("3 us")
            elif ((existing_settings & 0x0c)>>2 == 2):
                registers[chn].append("0.5 us")
            else:
                registers[chn].append("2 us")
                
            if ((existing_settings & 0x02)>>1 == 1):
                registers[chn].append("On")
            else:
                registers[chn].append("")
                
            if ((existing_settings & 0x01) == 1):
                registers[chn].append("On")
            else:
                registers[chn].append("Off")
                
        print ("Channel Registers for Front End chip " + str(chip) + " are:")
        print (tabulate(registers,headers,tablefmt="grid"))
        print ("\n")
        
        headers = ["DAC Value", "SDACSW1", "SDACSW2", "Coupling", "Leakage", "Ch16 Filter", "Ch1 Output" ]
        registers=[[]]

        tuple_num = (chip * 5) + 4
                
        find_mask = (0xFFFF)
        existing_settings = ((fe_regs[tuple_num] & find_mask) >> bitshift)
        
        dac_setting = (existing_settings & 0xfc00)
        dac_digit1 = (dac_setting & 0x8000) >> 15
        dac_digit2 = (dac_setting & 0x4000) >> 13
        dac_digit3 = (dac_setting & 0x2000) >> 11
        dac_digit4 = (dac_setting & 0x1000) >> 9
        dac_digit5 = (dac_setting & 0x0800) >> 7
        dac_digit6 = (dac_setting & 0x0400) >> 5
        dac_setting = dac_digit1 + dac_digit2 + dac_digit3 + dac_digit4 + dac_digit5 + dac_digit6

        registers[0].append(str(dac_setting))
        
        if ((existing_settings & 0x0200)>>9 == 1):
            registers[0].append("Closed")
        else:
            registers[0].append("Open")
    
        if ((existing_settings & 0x0100)>>8 == 1):
            registers[0].append("Closed")
        else:
            registers[0].append("Open")
             
        if ((existing_settings & 0x0020)>>5 == 0):
           registers[0].append("DC")
        else:
            registers[0].append("AC")
                
        if (((existing_settings & 0x0010)>>3) + ((existing_settings & 0x0001)) == 0):
            registers[0].append("500 pA")
        elif (((existing_settings & 0x0010)>>3) + ((existing_settings & 0x0001)) == 1):
            registers[0].append("100 pA")
        elif (((existing_settings & 0x0010)>>3) + ((existing_settings & 0x0001)) == 2):
            registers[0].append("5 nA")
        else:
           registers[0].append("1 nA")
           
        if ((existing_settings & 0x0008)>>3 == 0):
           registers[0].append("Disconnected")
        else:
            registers[0].append("Connected")
                
        if (((existing_settings & 0x0006)>>1) == 2):
            registers[0].append("Temperature")
        elif (((existing_settings & 0x0006)>>1) == 3):
            registers[0].append("Bandgap")
        else:
           registers[0].append("Normal output")

        print ("Global Registers for Front End chip " + str(chip) + " are:")
        print (tabulate(registers,headers,tablefmt="grid"))
        print ("\n")
        
    def make_filepaths(self, datadir, chip_list, datasubdir):
        for num,i in enumerate(chip_list):
            os.makedirs(os.path.join(datadir,i[1],datasubdir))
            
        
