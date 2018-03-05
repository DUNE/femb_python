#!/usr/bin/env python33

import sys 
import time
#import visa
#from visa import VisaIOError
import matplotlib.pyplot as plt
import numpy as np
from scripts.femb_udp_cmdline import FEMB_UDP
from scripts.detect_peaks import detect_peaks
from scripts.fe_asic_reg_mapping import FE_ASIC_REG_MAPPING
from user_settings import user_editable_settings
from scripts.plotting import plot_functions
settings = user_editable_settings()

class FEMB_CONFIG:

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
        
        #Give a default DAC value
        self.femb.write_reg(1, settings.default_DAC)
        self.femb.write_reg(2, 1)
        self.femb.write_reg(2, 0)
        
        #Give a default pulse timing
        self.femb.write_reg(7, (settings.default_TP_Shift << 16) + settings.default_TP_Period)

        #Write the default ADC settings
        i = 0
        for reg in range(65, 69, 1):
            self.femb.write_reg(reg, settings.Latch_Settings[i])
            i = i + 1
            
        i = 0
        for reg in range(69, 73, 1):
            self.femb.write_reg(reg, settings.Phase_Settings[i])
            i = i + 1
            
        self.femb.write_reg(73, settings.test_ADC_Settings)
        
        self.femb.write_reg(74, settings.pre_buffer)
            
        #Write the frame size as a multiple of 16
        frame_size = settings.frame_size
        if (frame_size%16 != 0):
            frame_size = 16 * (frame_size//16)

        #Write the defaul ASIC settings
        self.fe_reg.set_fe_board(sts=1, snc=1, sg=1, st=1, smn=0, sbf=1, 
                       slk = 0, stb = 0, s16=0, slkh=0, sdc=0, sdacsw2=1, sdacsw1=0, sdac=settings.sync_peak_height)

        self.configFeAsic()
        
        print ("FEMB_CONFIG--> Initialize FEMB is DONE")

    def configFeAsic(self, to_print = False):
        #Grab ASIC settings from linked class
        Feasic_regs = self.fe_reg.REGS
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
            val = self.femb.read_reg ( self.REG_FEASIC_SPI ) 
            wrong = False

            if (((val & 0x10000) >> 16) != 1 and (0 in settings.chips_to_use)):
                print ("FEMB_CONFIG--> Something went wrong when programming FE 1")
                wrong = True
                
            if (((val & 0x20000) >> 17) != 1 and (1 in settings.chips_to_use)):
                print ("FEMB_CONFIG--> Something went wrong when programming FE 2")
                wrong = True
                
            if (((val & 0x40000) >> 18) != 1 and (2 in settings.chips_to_use)):
                print ("FEMB_CONFIG--> Something went wrong when programming FE 3")
                wrong = True
                
            if (((val & 0x80000) >> 19) != 1 and (3 in settings.chips_to_use)):
                print ("FEMB_CONFIG--> Something went wrong when programming FE 4")
                wrong = True

            if (wrong == True and k == 9):
                print ("FEMB_CONFIG--> SPI_Status is {}").format(hex(val))
                #sys.exit("FEMB_CONFIG--> femb_config_femb : Wrong readback. FE SPI failed")
                return
                
            elif (wrong == False): 
                self.fe_reg.info.fe_regs_sent = Feasic_regs
                if (to_print == True):
                    print ("FEMB_CONFIG--> FE ASIC SPI is OK")
                break

    #ASSUMES ASICS HAVE BEEN SET FOR THE INTERNAL PULSER
    def syncADC(self, chips):
        print ("FEMB_CONFIG--> Start sync ADC")
        
        #Don't ask me why, but you need to set the channel at this point for it to output the right data
        self.select_chip_chn(chip = 0, chn = 1)
        for chip in chips:
            
            #Tells the FPGA to turn on each DAC
            self.femb.write_reg(61, 0x0)
            
            #Read from DATA output ADCs
            self.femb.write_reg(60, 0)
    
            #Set to Regular Mode (not sampling scope mode)
            self.femb.write_reg(10, 0)
            
            #Select the internal DAC readout
            self.femb.write_reg(9, 3)
                
            #Get the ASIC to send out pulses.  Bit 6 needs to be high for ASIC DAC
            self.reg_17_value = (settings.default_TP_Period << 16) + (settings.default_TP_Shift << 8) + (0b01000000)
            self.femb.write_reg(17, self.reg_17_value)

            print ("FEMB_CONFIG--> Test ADC {}".format(chip))
            
            for chn in range(settings.channels):
                #Tests if it's synchronized, returns True if it is
                unsync = self.testUnsync(chip = chip, chn = chn)
                if unsync != True:
                    print ("FEMB_CONFIG--> Chip {}, Chn {} not synced, try to fix".format(chip, chn))
                    response = self.fixUnsync_outputADC(chip = chip, chn = chn)
                    if (response != True):
                        print ("FEMB_CONFIG--> Something is wrong with Chip {}, Chn {}".format(chip, chn))
#                        sys.exit ("FEMB_CONFIG--> ADC {} could not sync".format(chip))

            print ("FEMB_CONFIG--> ADC {} synced!".format(chip))
            
            print ("FEMB_CONFIG--> Trying to sync test ADC".format(chip))
            
            #Have one of the channels output its pulse to the test monitor pin
            self.fe_reg.set_fe_chn(chip = chip, chn = 0, smn = 1)
            self.configFeAsic()
            
            #Read from TEST output ADCs
            self.femb.write_reg(60, 1)
            
            #Select the monitor readout
            self.femb.write_reg(9, 3)
            
            unsync = self.testUnsync(chip = chip, chn = chn)
            if unsync != True:
                print ("FEMB_CONFIG--> Chip {} (test ADC) not synced, try to fix".format(chip))
                response = self.fixUnsync_testADC(chip = chip)
                if (response != True):
                    print ("FEMB_CONFIG--> Something is wrong with Chip {} (test ADC)".format(chip))
            else:
                print ("FEMB_CONFIG--> Chip {} (test ADC) synced!".format(chip))

        self.comm_settings = []
        print ("FEMB_CONFIG--> Final Shift Settings: ")
        for reg in range(65, 69, 1):
            value = self.femb.read_reg(reg)
            print("Register {}: {}".format(reg, hex(value)))
            self.comm_settings.append(value)

        print ("FEMB_CONFIG--> Final Phase Settings: ")
        for reg in range(69, 73, 1):
            value = self.femb.read_reg(reg)
            print("Register {}: {}".format(reg, hex(value)))
            self.comm_settings.append(value)
            
        value = self.femb.read_reg(73)
        print("Register {}: {}".format(73, hex(value)))
        self.comm_settings.append(value)
        
        self.femb.write_reg(17, 0)
            
        print ("FEMB_CONFIG--> ADC passed Sync Test!")

            
    def testUnsync(self, chip, chn):
        #Get some packets of data
        self.select_chip_chn(chip = chip, chn = chn)
        data = self.get_data_chipXchnX(chip = chip, chn = chn, packets = 25, data_format = "counts")
        
        #Find some peaks
        peaks_index = detect_peaks(x=data, mph=settings.sync_peak_min, mpd=100) 
        #Make sure you have more than 0 peaks (so it's not flat) and less than the maximum 
        #(if there's no peak, the baseline will give hundreds of peaks)
        #If it's bad, print it, so we see (must enable inline printing for iPython)
        if (len(peaks_index) == 0) or (len(peaks_index) > settings.sync_peaks_max):
            print ("Chip {}, Channel {} has {} peaks!".format(chip, chn, len(peaks_index)))            
#            print (peaks_index)
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
            plt.show()
            plt.close()
            return False
            
        #So that function before only gives you the X locations of where the peaks are.  Let's get the Y values from that
        peaks_value = []
        for i in peaks_index :
            peaks_value.append(data[i])
#        print ("Chip {}, Channel {} has peak values {}".format(chip, chn, peaks_value))
        #Check if the peak is at the wrong height (happens when it's not synced, the peak will be havled or doubled)
        for peak in peaks_value:
            if ((peak < settings.sync_peak_min) or (peak > settings.sync_peak_max)):
                print ("FEMB CONFIG--> Chip {}, Chn {} has a peak that's {}".format(chip, chn, peak))
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
                plt.show()
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
        if ((baseline < settings.sync_baseline_min) or (baseline > settings.sync_baseline_max)):
            print ("FEMB CONFIG--> Chip {}, Chn {} has a baseline that's {}".format(chip, chn, baseline))
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
            plt.show()
            plt.close()
            return False 
        return True
            
    #Shifts through all possible delay and phase options, checking to see if each one fixed the issue
    def fixUnsync_outputADC(self, chip, chn):
        self.select_chip_chn(chip = chip, chn = chn)
        
        shift_reg = chip + 65
        phase_reg = chip + 69
        
        #Get the initial setting you don't disturb the other channels
        init_shift = self.femb.read_reg(shift_reg)
        init_phase = self.femb.read_reg(phase_reg)

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
                unsync = self.testUnsync(chip = chip, chn = chn)
                if unsync == True:
                    print ("FEMB_CONFIG--> Chip {}, Chn {} fixed!".format(chip, chn))
                    return True

        print ("FEMB_CONFIG--> ADC SYNC process failed for Chip {}, Channel {}".format(chip, chn))
        self.femb.write_reg(shift_reg, init_shift)
        self.femb.write_reg(phase_reg, init_phase)
        return False
        
    #Same thing as above, except the timing register is different, so the bitmath has to be changed.
    def fixUnsync_testADC(self, chip):
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
        print ("Init shift is {}".format(hex(init_shift)))
        print ("Init mask is {}".format(bin(init_mask)))    
        print ("Negative mask is {}".format(bin(neg_mask)))    
        for shift in range(4):
            for phase in range(4):
                setting = (phase << 2) + shift
                print ("Setting is {}".format(bin(setting)))
                
                final_setting = setting << (chip * 4)
                print ("Final Setting is {}".format(bin(setting)))
                
                init_shift_with_mask = init_shift & neg_mask
                print ("Initshift with mask is {}".format(hex(init_shift_with_mask)))
                
                really_final = init_shift_with_mask + final_setting
                print ("Final setting to write is {}".format(bin(really_final)))
                
#                init_shift_with_mask = init_shift & neg_mask
#                final_shift = shift_setting + init_shift_with_mask
                
#                print ("Shift is {}".format(shift))
#                print ("phase is {}".format(phase))
#                print ("Negative mask is {}".format(bin(neg_mask)))                
#                print ("Initial reading is {}".format(bin(init_shift)))
#                print ("The new setting is {}".format(bin(shift_setting)))
#                print ("Making space for the new setting is {}".format(bin(init_shift_with_mask)))
#                print ("Adding together is {}".format(bin(final_shift)))
                

                unsync = self.testUnsync(chip = chip, chn = 1)
                if unsync == True:
                    print ("FEMB_CONFIG--> Chip {} test ADC fixed!".format(chip))
                    return True

        print ("FEMB_CONFIG--> ADC SYNC process failed for Chip {} ADC".format(chip))
        return False
        
    #Select the chip and channel and read it out.  And check that it was actually set.  It's weirdly a problem
    def select_chip_chn(self, chip, chn):
        if (chip < 0 ) or (chip > settings.chip_num ):
            print ("FEMB CONFIG -> Error in get_data_chipXchnX: Chip must be between 0 and {}".format(settings.chip_num))
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
        
        if (chip < 0 ) or (chip > settings.chip_num ):
            print ("FEMB CONFIG -> Error in get_data_chipXchnX: Chip must be between 0 and {}, but it's {}".format(settings.chip_num, chip))
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
        
        if (chip < 0 ) or (chip > settings.chip_num ):
            print ("FEMB CONFIG -> Error in get_data_chipXchnX: Chip must be between 0 and {}, but it's {}".format(settings.chip_num, chip))
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
    
    
        

    #__INIT__#
    def __init__(self):
        #declare board specific registers
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
        self.plot = plot_functions()
        
        self.comm_settings = None

        #initialize FEMB UDP object
        self.femb = FEMB_UDP()
        self.fe_reg = FE_ASIC_REG_MAPPING() 
        
        self.WIB_RESET = 1
        
        self.BPS = 13 #Bytes per sample
        self.selected_chip = None
        self.selected_chn = None
