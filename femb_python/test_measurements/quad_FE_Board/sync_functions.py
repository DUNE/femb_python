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
from femb_python.test_measurements.quad_FE_Board.ASIC_config import ASIC_CONFIG_FUNCTIONS
from femb_python.test_measurements.quad_FE_Board.plotting import plot_functions
import matplotlib.pyplot as plt
import numpy as np
import os

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
        self.ASIC_Func = ASIC_CONFIG_FUNCTIONS(self.config)
        self.plot = plot_functions(self.config)

    #Returns boolean array of the chips that pass.  If a chips is not part of "working chips", its place will be empty in the array
    #chip_id[0] is the index of the chip, where it sits on the board (spot 0, 1, 2, 3 etc...)
    #chip_id[1] is its name (A2567, A2568, etc...)
    def syncADC(self, **kwargs):
        print ("sync_functions--> Start syncing ADCs")
        data = list(self.low_func.get_data_chipXchnX_tagged(chip = 1, chn = 1, packets = int(self.config["SYNC_SETTINGS"]["SYNC_PACKETS"]), data_format = "counts"))
        print_when_good = kwargs["to_print"]
        #Chips that have failed SPI or have been disabled by the GUI wont be tested
        working_chips = kwargs["working_chips"]
        return_array = []
        for i in range(int(self.config["DEFAULT"]["NASICS"])):
            return_array.append([])
            
        #Don't ask me why (ask Jack), but you need to set a new channel at this point for it to output the right data on the quad board
        self.low_func.selectChipChannel(chip = 0, chn = 1)
        for chip in working_chips:
            #"chiplist" is an argument that has the chip names.  Here we make an array with the chip index (where it is on the board) and it's name that was put in ("A5039")
            chiplist = kwargs["chip_list"]
            chip_id = (chiplist[chip])
            datadir = kwargs["datadir"]
            try:
                
                outputdir = kwargs["outlabel"]
                self.savefigpath = os.path.join(datadir,chip_id[1],outputdir)
            except KeyError:
                self.savefigpath = os.path.join(datadir,chip_id[1])
                
            os.makedirs(self.savefigpath, exist_ok=True)
            
            #Read from DATA output ADCs
            self.femb_udp.write_reg(int(self.config["REGISTERS"]["REG_READOUT_OPTIONS"]), int(self.config["DEFINITIONS"]["READOUT_NORMAL"]))
            
            #Select the MUX to ground so nothing is pulsing
            self.femb_udp.write_reg(int(self.config["REGISTERS"]["REG_MUX_MODE"]), int(self.config["DEFINITIONS"]["MUX_GND_GND"]))
            
            #Adds tracer bits on data coming in when the internal pulser has an edge
            self.femb_udp.write_reg(int(self.config["REGISTERS"]["REG_TAGGING"]), int(self.config["DEFINITIONS"]["TAGGING_ON"]))
            
            #Get the ASIC to send out pulses
            self.low_func.setInternalPulser(period = int(self.config["SYNC_SETTINGS"]["SYNC_INTERNAL_PULSE_FREQ"]), shift = int(self.config["SYNC_SETTINGS"]["SYNC_INTERNAL_PULSE_DLY"]), enable = True)
            self.ASIC_Func.configFeAsic(test_cap="on", base=self.config["SYNC_SETTINGS"]["SYNC_BASELINE"], gain=self.config["SYNC_SETTINGS"]["SYNC_GAIN"], shape=self.config["SYNC_SETTINGS"]["SYNC_PEAK"], 
                                        monitor_ch=None, buffer=self.config["SYNC_SETTINGS"]["SYNC_BUFFER"], leak = self.config["SYNC_SETTINGS"]["SYNC_LEAK"], monitor_param = None, s16=None, 
                                        acdc=self.config["SYNC_SETTINGS"]["SYNC_ACDC"], test_dac="test_int", dac_value=int(self.config["SYNC_SETTINGS"]["SYNC_DAC_PEAK_HEIGHT"]))
            self.ASIC_Func.writeFE()
        
            print ("sync_functions--> Trying to sync ADC {}({})".format(chip_id[0],chip_id[1]))
            channel_output_result = True
            for chn in range(int(self.config["DEFAULT"]["NASICS"])):
                #Tests if it's synchronized, returns True if it is
                unsync = self.testUnsync(chip = chip_id, chn = chn)
                if unsync != True:
                    print ("sync_functions--> Chip {}({}), Chn {} not synced, try to fix".format(chip_id[0],chip_id[1], chn))
                    response = self.fixUnsync_outputADC(chip = chip_id, chn = chn)
                    if (response != True):
                        channel_output_result = False
                        print ("sync_functions--> Unable to fix Chip {}({}), Chn {}".format(chip_id[0],chip_id[1], chn))
            if (channel_output_result == True):
                print ("sync_functions--> ADC {}({}) regular output channels synced!".format(chip_id[0],chip_id[1]))
            else:
                print ("sync_functions--> ADC {}({}) regular output channels failed!".format(chip_id[0],chip_id[1]))

            if (print_when_good == True):
                #Prints a plot of the whole chip so we can be sure there was no sketchiness (takes some time)
                print("sync_functions--> Printing synchronization plot for Chip {}({})".format(chip_id[0],chip_id[1]))
                data = self.low_func.get_data_chipX(chip = chip_id[0], packets = int(self.config["SYNC_SETTINGS"]["SYNC_PACKETS"]), tagged = True)
                plot_path = os.path.join(self.savefigpath,self.config["FILENAMES"]["SYNC_LINK"])
                self.plot.plot_chip(data = data, plot_name = plot_path, title_name = "Pulses for synchronization: Gain = {}/fC, Peaking Time = {}, Buffer {}, "
                                                                                     "DAC Pulse at {} \nPeaks should be between {} and {}, Baseline should be between "
                                                                                     "{} and {}".format(self.config["SYNC_SETTINGS"]["SYNC_GAIN"], self.config["SYNC_SETTINGS"]["SYNC_PEAK"], self.config["SYNC_SETTINGS"]["SYNC_BUFFER"], 
                                                                                    self.config["SYNC_SETTINGS"]["SYNC_DAC_PEAK_HEIGHT"], self.config["SYNC_SETTINGS"]["SYNC_PEAK_MIN"], self.config["SYNC_SETTINGS"]["SYNC_PEAK_MAX"], 
                                                                                    self.config["SYNC_SETTINGS"]["SYNC_BASELINE_MIN"], self.config["SYNC_SETTINGS"]["SYNC_BASELINE_MAX"]))
            
            print ("sync_functions--> Trying to sync test ADC {}({})".format(chip_id[0],chip_id[1]))
            
            #Have one of the channels output its pulse to the test monitor pin
            self.ASIC_Func.FE_Regs.set_fe_chn(chip = chip_id[0], chn = 0, smn = 1)
            self.ASIC_Func.writeFE()
            
            #Read from TEST output ADCs
            self.femb_udp.write_reg(int(self.config["REGISTERS"]["REG_READOUT_OPTIONS"]), int(self.config["DEFINITIONS"]["READOUT_TEST_ADC"]))
            
            #Select the monitor readout to ADC
            self.femb_udp.write_reg(int(self.config["REGISTERS"]["REG_MUX_MODE"]), int(self.config["DEFINITIONS"]["MUX_ADC_GND"]))
            
            monitor_test_result = True
            unsync = self.testUnsync(chip = chip_id, chn = chn)
            if unsync != True:
                print ("sync_functions--> Chip {}({}) (test ADC) not synced, try to fix".format(chip_id[0],chip_id[1]))
                response = self.fixUnsync_testADC(chip = chip_id)
                if (response != True):
                    monitor_test_result = False
                    print ("sync_functions--> Something is wrong with Chip {}({}) (test ADC)".format(chip_id[0],chip_id[1]))
            if (monitor_test_result == True):
                print ("sync_functions--> Chip {}({}) (test ADC) synced!".format(chip_id[0],chip_id[1]))
            else:
                print ("sync_functions--> Chip {}({}) (test ADC) failed!".format(chip_id[0],chip_id[1]))
                
            if (channel_output_result and monitor_test_result):
                return_array[chip_id[0]] = True
            else:
                return_array[chip_id[0]] = False
                
            if (print_when_good == True):
                #Prints a plot of the monitor test pin so we can be sure there was no sketchiness
                print("sync_functions--> Printing synchronization plot for Chip {}({})".format(chip_id[0],chip_id[1]))
                data = self.low_func.get_data_chipXchnX_tagged(chip = chip_id[0], chn = 1, packets = int(self.config["SYNC_SETTINGS"]["SYNC_PACKETS"]), data_format = "counts")
                plot_path = os.path.join(self.savefigpath,self.config["FILENAMES"]["SYNC_LINK_MONITOR"])
                title = "Pulses for synchronization: Gain = {}/fC, Peaking Time = {}, Buffer {}, DAC Pulse at {} \nPeaks should be between {} and {}, Baseline should be between {} and {}".format(self.config["SYNC_SETTINGS"]["SYNC_GAIN"], 
                        self.config["SYNC_SETTINGS"]["SYNC_PEAK"], self.config["SYNC_SETTINGS"]["SYNC_BUFFER"], self.config["SYNC_SETTINGS"]["SYNC_DAC_PEAK_HEIGHT"], self.config["SYNC_SETTINGS"]["SYNC_PEAK_MIN"], 
                        self.config["SYNC_SETTINGS"]["SYNC_PEAK_MAX"], self.config["SYNC_SETTINGS"]["SYNC_BASELINE_MIN"], self.config["SYNC_SETTINGS"]["SYNC_BASELINE_MAX"])
                self.plot.debugScatterplot(data = data, save_location = plot_path, title = title, peaks_index = None)
            
        #This just helps so that if we continuously need to sync on a board, we can go back and see what the settings it finds are and make those the default.
        outputfile = os.path.join(datadir,"syncresults.txt")
        with open(outputfile, 'w') as f:
            f.write("sync_functions--> Final Shift Settings: \n")
            for reg in range(int(self.config["REGISTERS"]["REG_LATCH_MIN"]), int(self.config["REGISTERS"]["REG_LATCH_MAX"]) + 1):
                value = self.femb_udp.read_reg(reg)
                f.write("Register {}: {}\n".format(reg, hex(value)))
    
            f.write("sync_functions--> Final Phase Settings: \n")
            for reg in range(int(self.config["REGISTERS"]["REG_PHASE_MIN"]), int(self.config["REGISTERS"]["REG_TEST_ADC"]) + 1):
                value = self.femb_udp.read_reg(reg)
                f.write("Register {}: {}\n".format(reg, hex(value)))
            
        #Bring things back to normal
        self.femb_udp.write_reg(int(self.config["REGISTERS"]["REG_READOUT_OPTIONS"]), int(self.config["DEFINITIONS"]["READOUT_NORMAL"]))
        self.femb_udp.write_reg(int(self.config["REGISTERS"]["REG_TAGGING"]), int(self.config["DEFINITIONS"]["TAGGING_OFF"]))
        self.low_func.setInternalPulser(period = int(self.config["SYNC_SETTINGS"]["SYNC_INTERNAL_PULSE_FREQ"]), shift = int(self.config["SYNC_SETTINGS"]["SYNC_INTERNAL_PULSE_DLY"]), enable = False)
        
        return return_array
                
    def testUnsync(self, chip, chn, index=0):
        save_error_path = os.path.join(self.savefigpath, "sync_fails")
        os.makedirs(save_error_path, exist_ok=True)
        #Get some packets of data
        self.low_func.selectChipChannel(chip = chip[0], chn = chn)
        data = list(self.low_func.get_data_chipXchnX_tagged(chip = chip[0], chn = chn, packets = int(self.config["SYNC_SETTINGS"]["SYNC_PACKETS"]), data_format = "counts"))
        peaks_index = detect_peaks(x=data, mph=int(self.config["SYNC_SETTINGS"]["SYNC_PEAK_MIN"]), mpd=int(self.config["SYNC_SETTINGS"]["SYNC_PULSE_SPACING"])/2)
        
        #Check that we have the amount of peaks we want (sync issues lead to too many or too little peaks)
        if (len(peaks_index) != int(self.config["SYNC_SETTINGS"]["SYNC_PACKETS"])):
            error = "sync_functions: Chip {}({}), Chn {} has {} peaks".format(chip[0],chip[1], chn, len(peaks_index))
            print (error)
            save_location = os.path.join(save_error_path,"chip{}chn{}peaks{}_index{}.jpg".format(chip[1],chn,len(peaks_index),index))
            self.plot.debugScatterplot(data=data, peaks_index=peaks_index, title=error, save_location=save_location)
            return False
            
        #So that function before only gives you the X locations of where the peaks are.  Let's get the Y values from that
        peaks_value = []
        for i in peaks_index :
            peaks_value.append(data[i])
#        print("Peak values are {}\n".format(peaks_value))
#        print ("Chip {}({}), Channel {} has peak values {}".format(chip_id[0],chip_id[1], chn, peaks_value))
        #Check if the peak is at the wrong height (happens when it's not synced, the peak will be halved or doubled)
        for peak in peaks_value:
            if ((peak < int(self.config["SYNC_SETTINGS"]["SYNC_PEAK_MIN"])) or (peak > int(self.config["SYNC_SETTINGS"]["SYNC_PEAK_MAX"]))):
                error = "sync_functions: Chip {}({}), Chn {} has a peak that's {}".format(chip[0],chip[1], chn, peak)
                print (error)
                save_location = os.path.join(save_error_path,"chip{}chn{}peak{}.jpg".format(chip,chn,peak))
                self.plot.debugScatterplot(data=data, peaks_index=peaks_index, title=error, save_location=save_location)
                return False 
                
        #Check if the baseline is right (this also gets halved and doubled with unsynced ADCs) (grab a middle section to avoid the peaks)
        try:
            baseline_area_start = peaks_index[0] + int(self.config["SYNC_SETTINGS"]["SYNC_PULSE_WIDTH"])
            baseline_area_end = peaks_index[1] - int(self.config["SYNC_SETTINGS"]["SYNC_PULSE_WIDTH"])
        except IndexError:
            baseline_area_start = int(self.config["SYNC_SETTINGS"]["SYNC_PULSE_WIDTH"])
            baseline_area_end = int(self.config["SYNC_SETTINGS"]["SYNC_PULSE_SPACING"]) - int(self.config["SYNC_SETTINGS"]["SYNC_PULSE_WIDTH"])
        baseline_data = data[baseline_area_start : baseline_area_end]
        baseline = np.mean(baseline_data)
        #In case it's None or something weird like that like I was originally seeing
        if (isinstance(baseline, np.float64) != True):
            print("sync_functions--> Baseline is {}".format(type(baseline)))
            return False
        if ((baseline < int(self.config["SYNC_SETTINGS"]["SYNC_BASELINE_MIN"])) or (baseline > int(self.config["SYNC_SETTINGS"]["SYNC_BASELINE_MAX"]))):
            error = "sync_functions--> Chip {}({}), Chn {} has a baseline that's {}".format(chip[0],chip[1], chn, baseline)
            print (error)
            save_location = os.path.join(save_error_path,"chip{}chn{}baseline{}.jpg".format(chip,chn,baseline))
            self.plot.debugScatterplot(data=data, peaks_index=peaks_index, title=error, save_location=save_location)
                
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
    #TODO if internal pulser doesn't work, check external pulser
    def fixUnsync_outputADC(self, chip, chn):
        self.low_func.selectChipChannel(chip = chip[0], chn = chn)
        
        shift_reg = chip[0] + int(self.config["REGISTERS"]["REG_LATCH_MIN"])
        phase_reg = chip[0] + int(self.config["REGISTERS"]["REG_PHASE_MIN"])
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
                    print("sync_functions--> Chip {}({}), Chn {} fixed!\n".format(chip[0], chip[1], chn))
                    return True

        print ("sync_functions--> ADC SYNC process failed for Chip {}({}), Channel {}".format(chip[0], chip[1], chn))
        self.femb_udp.write_reg(shift_reg, init_shift)
        self.femb_udp.write_reg(phase_reg, init_phase)
        return False
        
    #TODO check other channels if one doesn't work
    def fixUnsync_testADC(self, chip):
        test_reg = int(self.config["REGISTERS"]["REG_TEST_ADC"])
        self.low_func.select_chip_chn(chip = chip, chn = 2)
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
            
        init_shift = self.femb.read_reg(test_reg)          
        #print ("Init shift is {}".format(hex(init_shift)))
        #print ("Init mask is {}".format(bin(init_mask)))
        #print ("Negative mask is {}".format(bin(neg_mask))))
        for shift in range(4):
            for phase in range(4):
                setting = (phase << 2) + shift
                #print ("Setting is {}".format(bin(setting)))
                final_setting = setting << (chip * 4)
                #print ("Final Setting is {}".format(bin(setting)))
                init_shift_with_mask = init_shift & neg_mask
                #print ("Initshift with mask is {}".format(hex(init_shift_with_mask)))
                really_final = init_shift_with_mask + final_setting
                #print ("Final setting to write is {}".format(bin(really_final)))
#                init_shift_with_mask = init_shift & neg_mask
#                final_shift = shift_setting + init_shift_with_mask
                
#                print ("Shift is {}".format(shift))
#                print ("phase is {}".format(phase))
#                print ("Negative mask is {}".format(bin(neg_mask)))                
#                print ("Initial reading is {}".format(bin(init_shift)))
#                print ("The new setting is {}".format(bin(shift_setting)))
#                print ("Making space for the new setting is {}".format(bin(init_shift_with_mask)))
#                print ("Adding together is {}".format(bin(final_shift)))
                
                self.femb.write_reg(test_reg, really_final)
                index = (shift+4) + phase + 100
                unsync = self.testUnsync(chip = chip, chn = 1, index = index)
                if unsync == True:
                    print ("FEMB_CONFIG--> Chip {} test ADC fixed!".format(chip))
                    return True

        print ("FEMB_CONFIG--> ADC SYNC process failed for Chip {} ADC".format(chip))
        self.femb.write_reg(test_reg, init_shift)
        return False