""" 
Board-specific function
"""

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import
from builtins import int
from builtins import range
from builtins import hex
from builtins import str
from future import standard_library
standard_library.install_aliases()
from builtins import object
from femb_python.generic_femb_udp import FEMB_UDP
from femb_python.test_measurements.quad_FE_Board.detect_peaks import detect_peaks
from femb_python.test_measurements.quad_FE_Board.low_level_pre_udp import LOW_LEVEL
from femb_python.configuration.FE_config import FE_CONFIG 
from femb_python.configuration.config_module_loader import getDefaultDirectory
import time
import matplotlib.pyplot as plt
import numpy as np
import os
import json

class SYNC_FUNCTIONS(object):
    """
    Base class for configuration files. These should be considered the 'public'
    methods of the config classes, non-configuration code should only use this set
    of functions.  
    """

    def __init__(self, config_file = None):
        """
        Initialize this class (no board communication here. Should setup self.femb_udp as a femb_udp instance, get FE Registers, etc...)
        """
        if (config_file == None):
            from femb_python.configuration import CONFIG
            self.config = CONFIG
        else:
            self.config = config_file
            
        self.femb_udp = FEMB_UDP(self.config)     
        self.low_func = LOW_LEVEL(self.config)
        self.FE_Regs = FE_CONFIG(chip_num = int(self.config["DEFAULT"]["NASICS"]), chn_num = int(self.config["DEFAULT"]["NASICCH"]))

    #Returns boolean array of the chips that pass.  If a chips is not part of "working chips", its place will be empty in the array
    #chip_id[0] is the index of the chip, where it sits on the board (spot 0, 1, 2, 3 etc...)
    #chip_id[1] is its name (A2567, A2568, etc...)
    def syncADC(self, **kwargs):
        print ("sync_functions--> Start sync ADC")
        outputdir = kwargs["outputdir"]
        #Chips that have failed SPI or have been disabled by the GUI wont be tested
        working_chips = kwargs["working_chips"]
        return_array = []
        print(int(self.config["DEFAULT"]["NASICS"]))
        for i in range(int(self.config["DEFAULT"]["NASICS"])):
            return_array.append([])
            
        #Don't ask me why (ask Jack), but you need to set a new channel at this point for it to output the right data on the quad board
        self.low_func.selectChipChannel(chip = 0, chn = 1)
        for chip in working_chips:
            #"chiplist" is an argument if the function call came from the sumatra runner i.e. the full suite of tests are being run, and there's a timestamp and permanent directory
            #If there's no "chiplist", this has been called by the GUI as a check to get the live trace tester to make sure everything's working.  In that case, output the results to a temporary directory in the test root
            if ("chiplist" in kwargs):
                chiplist = kwargs["chiplist"]
                datadir = kwargs["datadir"]
                chip_id = chiplist[chip]
                self.savefigpath = os.path.join(datadir,chip_id[1],outputdir,"syncplots")
            else:
                chip_id = [chip,chip]   
                self.savefigpath = os.path.join(outputdir,str(chip_id[1]))
                
            os.makedirs(self.savefigpath)
            self.sync_prep_output()
            print ("sync_functions--> Trying to sync ADC {}({})".format(chip_id[0],chip_id[1]))
            output_result = True
            for chn in range(self.NASICCH):
                #Tests if it's synchronized, returns True if it is
                unsync = self.testUnsync(chip = chip_id, chn = chn)
                if unsync != True:
                    print ("sync_functions--> Chip {}({}), Chn {} not synced, try to fix".format(chip_id[0],chip_id[1], chn))
                    response = self.fixUnsync_outputADC(chip = chip_id, chn = chn)
                    if (response != True):
                        output_result = False
                        print ("sync_functions--> Something is wrong with Chip {}({}), Chn {}".format(chip_id[0],chip_id[1], chn))
            if (output_result == True):
                print ("sync_functions--> ADC {}({}) synced!".format(chip_id[0],chip_id[1]))

            #Prints a plot of the whole chip so we can be sure there was no sketchiness
            print("sync_functions--> Printing synchronization plot for Chip {}({})".format(chip_id[0],chip_id[1]))
            data = self.get_data_chipX(chip = chip_id[0], packets = self.sync_desired_peaks, tagged = True)
            plot_path = os.path.join(self.savefigpath,"syncplots")
            self.plot.plot_chip(data = data, plot_name = plot_path, title_name = "Pulses for synchronization: Gain = {}/fC, Peaking Time = {}, Buffer {}, "
                                                                                 "DAC Pulse at {} \nPeaks should be between {} and {}, Baseline should be between "
                                                                                 "{} and {}".format(self.sync_gain, self.sync_pulse, self.sync_buffer, hex(self.sync_peak_height), self.sync_peak_min, 
                                                                                   self.sync_peak_max, self.sync_baseline_min, self.sync_baseline_max))
            
            print ("sync_functions--> Trying to sync test ADC {}({})".format(chip_id[0],chip_id[1]))
            self.sync_prep_test(chip = chip_id[0])
            test_result = True
            unsync = self.testUnsync(chip = chip_id, chn = chn)
            if unsync != True:
                print ("sync_functions--> Chip {}({}) (test ADC) not synced, try to fix".format(chip_id[0],chip_id[1]))
                response = self.fixUnsync_testADC(chip = chip_id)
                if (response != True):
                    test_result = False
                    print ("sync_functions--> Something is wrong with Chip {}({}) (test ADC)".format(chip_id[0],chip_id[1]))
            if (test_result == True):
                print ("sync_functions--> Chip {}({}) (test ADC) synced!".format(chip_id[0],chip_id[1]))
                
            if (output_result and test_result):
                return_array[chip_id[0]] = True
            else:
                return_array[chip_id[0]] = False
            
        #This just helps so that if we continuously need to sync on a board, we can go back and see what the settings it finds are and make those the default.
        outputfile = os.path.join(outputdir,"syncresults.txt")
        with open(outputfile, 'w') as f:
            f.write("sync_functions--> Final Shift Settings: \n")
            for reg in range(self.REG_Latch_Min, self.REG_Latch_Max + 1):
                value = self.femb_udp.read_reg(reg)
                f.write("Register {}: {}\n".format(reg, hex(value)))
    
            f.write("sync_functions--> Final Phase Settings: \n")
            for reg in range(self.REG_Phase_Min, self.REG_Test_ADC + 1):
                value = self.femb_udp.read_reg(reg)
                f.write("Register {}: {}\n".format(reg, hex(value)))
            
        self.sync_finish()
        return return_array
                
    def testUnsync(self, chip, chn, index=0):
        #Get some packets of data
        self.selectChipChannel(chip = chip[0], chn = chn)
        data = list(self.get_data_chipXchnX_tagged(chip = chip[0], chn = chn, packets = self.sync_desired_peaks, data_format = "counts"))
        peaks_index = detect_peaks(x=data, mph=self.sync_peak_min, mpd=self.pulse_spacing/2)
        
        #Check that we have the amount of peaks we want (sync issues lead to too many or too little peaks)
        if (len(peaks_index) != self.sync_desired_peaks):
            print ("sync_functions--> Chip {}({}), Channel {} has {} peaks!".format(chip[0],chip[1], chn, len(peaks_index)))
            figure_data = self.plot.quickPlot(data)
            ax = figure_data[0]
            for j in peaks_index:
                y_value = data[j]
                ax.scatter(j * self.sample_period, y_value, marker='x')
                
            ax.set_ylabel('ADC Counts')
            ax.set_title("sync_functions: Chip {}({}), Chn {} has {} peaks".format(chip[0],chip[1], chn, len(peaks_index)))
            ax.title.set_fontsize(30)
            for item in ([ax.xaxis.label, ax.yaxis.label] +ax.get_xticklabels() + ax.get_yticklabels()):
                item.set_fontsize(20)
            plt.savefig(os.path.join(self.savefigpath,"chip{}chn{}peaks{}_index{}.jpg".format(chip[1],chn,len(peaks_index),index)))
            plt.close()
            
            print("sync_functions--> Chip {}({}), Channel {} has {} peaks!\n".format(chip[0],chip[1], chn, len(peaks_index)))
#            print (peaks_index)
            return False
            
        #So that function before only gives you the X locations of where the peaks are.  Let's get the Y values from that
        peaks_value = []
        for i in peaks_index :
            peaks_value.append(data[i])
#        print("Peak values are {}\n".format(peaks_value))
#        print ("Chip {}({}), Channel {} has peak values {}".format(chip_id[0],chip_id[1], chn, peaks_value))
        #Check if the peak is at the wrong height (happens when it's not synced, the peak will be halved or doubled)
        for peak in peaks_value:
            if ((peak < self.sync_peak_min) or (peak > self.sync_peak_max)):
                print ("sync_functions--> Chip {}({}), Chn {} has a peak that's {}".format(chip[0],chip[1], chn, peak))
                figure_data = self.plot.quickPlot(data)
                ax = figure_data[0]
                for j in peaks_index:
                    y_value = data[j]
                    ax.scatter(j * self.sample_period, y_value, marker='x')
                    
                ax.set_ylabel('mV')
                ax.set_title("sync_functions: Chip {}({}), Chn {} has a peak that's {}".format(chip[0],chip[1], chn, peak))
                ax.title.set_fontsize(30)
                for item in ([ax.xaxis.label, ax.yaxis.label] +ax.get_xticklabels() + ax.get_yticklabels()):
                    item.set_fontsize(20)
                plt.savefig(os.path.join(self.savefigpath,"chip{}chn{}peak{}.jpg".format(chip,chn,peak)))
                plt.close()
                return False 
                
        #Check if the baseline is right (this also gets halved and doubled with unsynced ADCs) (avoid the peak to grab a middle section)
        try:
            baseline_area_start = peaks_index[0] + 15
            baseline_area_end = peaks_index[1] - 15
        except IndexError:
            baseline_area_start = 15
            baseline_area_end = 185
        baseline_data = data[baseline_area_start : baseline_area_end]
        baseline = np.mean(baseline_data)
        if (isinstance(baseline, np.float64) != True):
            print("sync_functions--> Baseline is {}".format(type(baseline)))
            return False
        if ((baseline < self.sync_baseline_min) or (baseline > self.sync_baseline_max)):
            print ("sync_functions--> Chip {}({}), Chn {} has a baseline that's {}".format(chip[0],chip[1], chn, baseline))
            figure_data = self.plot.quickPlot(data)
            ax = figure_data[0]
            for j in peaks_index:
                y_value = data[j]
                ax.scatter(j * self.sample_period, y_value, marker='x')
                
            ax.set_ylabel('mV')
            ax.set_title("Chip {}({}), Chn {} has a baseline that's {}".format(chip[0],chip[1], chn, baseline))
            ax.title.set_fontsize(30)
            for item in ([ax.xaxis.label, ax.yaxis.label] +ax.get_xticklabels() + ax.get_yticklabels()):
                item.set_fontsize(20)
            plt.savefig(os.path.join(self.savefigpath,"chip{}chn{}baseline{}.jpg".format(chip,chn,baseline)))
            plt.close()
            return False
                
        #check if the pulse has high frequency noise
        #Giving errors.  There's gotta be a simpler way of checking for high frequency noise, maybe just seeing if there's any sample that are X far away from baseline, or looking at histogram distribution?
#        total_high_freq_noise = 0
#        for peak in peaks_index:
#            dt = 0
#            t_high = 0
#            t_low = 0
#            print("Length of data is {}".format(len(data)))
#            while True:
#                dt = dt + 1
#                #check to see if we have reached the neighborhood of the baseline
#                print("peak is {}".format(peak))
#                print("dt is {}".format(dt))
#                if abs(data[peak+dt] - baseline) < self.sync_baseline_r and not t_high:
#                    t_high = peak+dt
#                if abs(data[peak-dt] - baseline) < self.sync_baseline_r and not t_low:
#                    t_low = peak-dt
#                if t_high and t_low:
#                    break
#                if dt == 100:
#                    if not t_high:
#                        t_high = peak + 100
#                    if not t_low:
#                        t_low = peak - 100
#                    break
#            pulse_data = data[t_low:t_high]
#            pulse_data_fft = np.fft.fft(pulse_data)[:int(len(pulse_data)/2)]
#            total_high_freq_noise = total_high_freq_noise + np.sum(abs(pulse_data_fft[5:].real))
#        avg_high_freq_noise = total_high_freq_noise / len(peaks_index)
#        
#        if avg_high_freq_noise > self.sync_high_freq_noise_max:
#            if saveresults:
#                print("FEMB CONFIG--> Chip {}({}), Chn {} has lots of high frequency noise".format(chip_id[0],chip_id[1], chn))
#                figure_data = self.plot.quickPlot(pulse_data)
#                ax = figure_data[0]
#                    
#                ax.set_ylabel('mV')
#                ax.set_title("Chip {}({}), Chn {} has lots of high frequency noise".format(chip_id[0],chip_id[1], chn))
#                ax.title.set_fontsize(30)
#                for item in ([ax.xaxis.label, ax.yaxis.label] +ax.get_xticklabels() + ax.get_yticklabels()):
#                    item.set_fontsize(20)
#                plt.savefig(os.path.join(savefigpath,"chip{}chn{}high_freq.jpg"))
#                plt.close()
#                return False
#            
        #If we made it through that gauntlet, it looks like the right peaks are there and it must be synced!
        return True
            
    #Shifts through all possible delay and phase options, checking to see if each one fixed the issue.  This is for the ADCs that read out the regular 16 channel outputs
    def fixUnsync_outputADC(self, chip, chn):
        self.selectChipChannel(chip = chip[0], chn = chn)
        
        shift_reg = chip + 65
        phase_reg = chip + 69
#        sample_reg = 75 + (chip//2)
        
        #Get the initial setting you don't disturb the other channels
        init_shift = self.femb_udp.read_reg(shift_reg)
        init_phase = self.femb_udp.read_reg(phase_reg)

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
#            self.femb_udp.write_reg(sample_reg, value)
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
                
                self.femb_udp.write_reg(shift_reg, final_shift)
                
                phase_setting = phase << (2 * chn)
                init_phase_with_mask = init_phase & neg_mask
                final_phase = phase_setting + init_phase_with_mask
                
                self.femb_udp.write_reg(phase_reg, final_phase)
                
                #See if this new setting fixed it
                index = (shift+4) + phase
                print("Trying shift {} phase {} index {}".format(shift,phase,index))
                unsync = self.testUnsync(chip = chip, chn = chn,index = index)
                if unsync == True:
                    #print ("FEMB_CONFIG--> Chip {}, Chn {} fixed!".format(chip, chn))
                    print("sync_functions--> Chip {}, Chn {} fixed!\n".format(chip, chn))
                    return True

        print ("sync_functions--> ADC SYNC process failed for Chip {}, Channel {}".format(chip, chn))
        self.femb_udp.write_reg(shift_reg, init_shift)
        self.femb_udp.write_reg(phase_reg, init_phase)
        return False
        
    def sync_prep_output(self):
        #Tells the FPGA to turn on each DAC
#        self.write_reg(61, 0x0)
        #Read from DATA output ADCs
        self.femb_udp.write_reg(self.REG_READOUT_OPTIONS, self.READOUT_NORMAL)
        
        #Select the internal DAC readout
        self.femb_udp.write_reg(self.REG_MUX_MODE, self.MUX_internal_pulser)
        
        #Adds tracer bits on data coming in when the internal pulser has an edge
        self.femb_udp.write_reg(self.REG_TAGGING, self.TAGGING_ON)
        
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
        self.femb_udp.write_reg(self.REG_READOUT_OPTIONS, self.READOUT_TEST_ADC)
        
        #Select the monitor readout
        self.femb_udp.write_reg(9, self.MUX_internal_pulser)
        
    def sync_finish(self):
        #Read from TEST output ADCs
        self.femb_udp.write_reg(self.REG_READOUT_OPTIONS, self.READOUT_NORMAL)
        self.femb_udp.write_reg(self.REG_TAGGING, self.TAGGING_OFF)
        self.set_internal_DAC(period = self.sync_INTERNAL_PERIOD, shift = self.sync_INTERNAL_SHIFT, enable = False)