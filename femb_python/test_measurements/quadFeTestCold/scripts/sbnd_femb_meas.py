import pickle
from scripts.femb_config_sbnd import FEMB_CONFIG
import numpy as np
from scripts.detect_peaks import detect_peaks
import os
import sys
import matplotlib.pyplot as plt
import time

from scripts.plotting import plot_functions
from user_settings import user_editable_settings
settings = user_editable_settings()
class FEMB_DAQ:

    def save_rms_noise(self, folder_path, chip_index, chip_name):
        print("Test--> Collecting Baseline data for Chip {}...".format(chip_name))
        #Because the statement will never print until after the giant for loop
        sys.stdout.flush()
        test_directory = folder_path + settings.baseline_folder
        os.makedirs(test_directory)
        
        data_directory = test_directory + settings.data
        os.makedirs(data_directory)
        
        #Select Ground to Test and FE input of all chips
        self.femb_config.femb.write_reg(9, 2)
            
        #Make sure nothing is coming from the FPGA DAC or for the signal for the ASIC's internal DAC
        self.femb_config.femb.write_reg(17, 0)
        
        #Read from FE output ADCs
        self.femb_config.femb.write_reg(60, 0)
        
        a = settings.asic_settings
        for gain in a["gains"]:
            print ("Baseline Data --> Collecting Data for {}".format(gain))
            sys.stdout.flush()
            for peak in a["peaks"]:
                for leak in a["leaks"]:
                    for buff in a["buffs"]:
                        for base in a["bases"]:
        
                            self.femb_config.fe_reg.set_fe_board(sts=0, snc=a[base], sg=a[gain], st=a[peak], 
                                    smn=0, sbf=a[buff], slk = a[leak][1], stb = 0, s16=0, slkh=a[leak][0], 
                                    sdc=0, sdacsw2=0, sdacsw1=0, sdac=0)
                                       
                            self.femb_config.configFeAsic(to_print = False)
#                            print ("Baseline Data --> Collecting Data for {}, {}, {}, {}, {}".format(gain, peak, leak, buff, base))
                            sys.stdout.flush()
                            time.sleep(0.1)
                            for chn in range(settings.channels):
                                self.femb_config.select_chip_chn(chip = chip_index, chn = chn)
                                filename = a["Baseline_Naming"].format(chn,gain,peak,leak,buff,base)
                                
                                rawdata = bytearray()
                                full_filename = data_directory + filename
                        
                                rawdata += self.femb_config.femb.get_data_packets(data_type = "bin", num = 1, header = True)
                                for pack in range (settings.baseline_length):
                                    rawdata += self.femb_config.femb.get_data_packets(data_type = "bin", num = 1, header = False)
                        
                                with open(full_filename,"wb") as f:
                                    f.write(rawdata) 
                                    f.close()
                                
        with open(data_directory + 'Configuration.cfg', 'wb') as f:
            pickle.dump(a, f, pickle.HIGHEST_PROTOCOL)
        self.get_state(data_directory)
        print ("Test--> Baseline data collected for Chip {}".format(chip_name))

    def save_alive_data(self, folder_path, chip_list):
        test_directory = []
        data_directory = []
        for i in range(len(chip_list)):
            test_directory.append(folder_path[i] + settings.alive_folder)
            os.makedirs(test_directory[i])
            
            data_directory.append(test_directory[i] + settings.data)
            os.makedirs(data_directory[i])

        #Give the test DAC value
        self.femb_config.femb.write_reg(1, settings.test_DAC)
        self.femb_config.femb.write_reg(2, 1)
        self.femb_config.femb.write_reg(2, 0)
        
        #Give the test pulse timing
        self.femb_config.femb.write_reg(7, (settings.test_TP_Shift << 16) + settings.test_TP_Period)

        #Make sure nothing is coming from the FPGA DAC or for the signal for the ASIC's internal DAC
        self.femb_config.femb.write_reg(17, 0)
        
        #Read from FE output ADCs
        self.femb_config.femb.write_reg(60, 0)
        for num,i in enumerate(chip_list):
            print("Test--> Collecting Input Alive data for Chip {}...".format(i[1]))
            sys.stdout.flush()
            a = settings.asic_settings
            for test in a["tests"]:
                for leak in a["leaks"]:
                    self.femb_config.fe_reg.set_fe_board(sts=a[test][0], snc=a["200mV"], sg=a["14mV"], st=a["2us"], 
                                smn=0, sbf=a["b_off"], slk = a[leak][1], stb = 0, s16=0, slkh=a[leak][0], sdc=0, 
                                sdacsw2=0, sdacsw1=a[test][0], sdac=0)
                               
                    self.femb_config.configFeAsic(to_print = False)
    #                print ("Input Alive --> Collecting Data for {}, {}".format(test, leak))
                    for chn in range(settings.channels):
                        self.femb_config.select_chip_chn(chip = i[0], chn = chn)
                        filename = a["Alive_Naming"].format(chn,leak,test)
                        
                        if (test == "test_off"):
                            #Select Ground to Test input and DAC pulse to FE input
                            self.femb_config.femb.write_reg(9, 8)
                            
                        elif (test == "test_external"):
                            #Select DAC pulse to Test input and Ground to FE input
                            self.femb_config.femb.write_reg(9, 4)
                            
                        rawdata = bytearray()
                        full_filename = data_directory[num] + filename
                
                        rawdata += self.femb_config.femb.get_data_packets(data_type = "bin", num = 1, header = True)
                        for pack in range (settings.alive_length):
                            rawdata += self.femb_config.femb.get_data_packets(data_type = "bin", num = 1, header = False)
                
                        with open(full_filename,"wb") as f:
                            f.write(rawdata) 
                            f.close()
        self.femb_config.femb.write_reg(9, 8)
        print("Test--> Testing {} power cycles (1 minute in between)".format(settings.power_cycles))
        sys.stdout.flush()
        for cycle in range(settings.power_cycles):
            print("Test--> Cycle {}".format(cycle))
            sys.stdout.flush()
            filename = a["Alive_Naming2"].format(chn,leak,test,cycle)
            sys.stdout.flush()
            self.femb_config.select_chip_chn(chip = 0, chn = 2)
            #Tells the FPGA to turn off the ASICs
            self.femb_config.femb.write_reg(12, 0xF)
            time.sleep(60)
            #Tells the FPGA to turn on the ASICs
            self.femb_config.femb.write_reg(12, 0x0)
            time.sleep(5)
            self.femb_config.fe_reg.set_fe_board(sts=0, snc=a["200mV"], sg=a["14mV"], st=a["2us"], 
                            smn=0, sbf=a["b_off"], slk = 0, stb = 0, s16=0, slkh=0, sdc=0, 
                            sdacsw2=0, sdacsw1=0, sdac=0)
                           
            self.femb_config.configFeAsic(to_print = False)
            
            time.sleep(1)          
            self.femb_config.femb.write_reg(1, settings.test_DAC)
            self.femb_config.femb.write_reg(2, 1)
            self.femb_config.femb.write_reg(2, 0)
            self.femb_config.femb.write_reg(61, 0x0)
            self.femb_config.femb.write_reg(7, (settings.test_TP_Shift << 16) + settings.test_TP_Period)
            self.femb_config.select_chip_chn(chip = 0, chn = 1)
            self.femb_config.femb.write_reg(9, 8)
            time.sleep(1)

            for num,i in enumerate(chip_list):
                self.femb_config.select_chip_chn(chip = i[0], chn = 1)
                print ("Test--> Input Alive power cycle data collecting for Chip {}".format(i[1]))
                sys.stdout.flush()
                full_filename = data_directory[num] + filename
                rawdata = bytearray()
                rawdata += self.femb_config.femb.get_data_packets(data_type = "bin", num = 1, header = True)
                for pack in range (settings.alive_length):
                    rawdata += self.femb_config.femb.get_data_packets(data_type = "bin", num = 1, header = False)
        
                with open(full_filename,"wb") as f:
                    f.write(rawdata) 
                    f.close()
        for i in range(len(chip_list)):
            with open(data_directory[i] + 'Configuration.cfg', 'wb') as f:
                pickle.dump(a, f, pickle.HIGHEST_PROTOCOL)
                
            self.get_state(data_directory[i])
        
        print ("Test--> Input Alive data completed")
        
    def save_DAC_data(self, folder_path, chip_index, chip_name):
        print("Test--> Collecting DAC step data for Chip {}...".format(chip_name))
        sys.stdout.flush()
		
        test_directory = folder_path + settings.DAC_folder
        os.makedirs(test_directory)
		
        data_directory = test_directory + settings.data
        os.makedirs(data_directory)
		
        #Select the monitor readout
        self.femb_config.femb.write_reg(9, 3)
            
        #Get the ASIC to send out pulses.  Bit 6 needs to be high for ASIC DAC
        reg17_value = (settings.DAC_freq << 16) + (settings.DAC_delay << 8) + (0b01000000)
        self.femb_config.femb.write_reg(17, reg17_value)
        
        #Read from test output ADCs
        self.femb_config.femb.write_reg(60, 1)
		
        a = settings.asic_settings
        for dac in range(settings.DAC_meas_min, settings.DAC_meas_max + 1, 1):
            self.femb_config.fe_reg.set_fe_board(sts=a["test_int"][0], snc=a["200mV"], sg=a["14mV"], st=a["2us"], 
					smn=0, sbf=a["b_off"], slk = a["500pA"][1], stb = 0, s16=0, slkh=a["500pA"][0], sdc=0, 
					sdacsw2=1, sdacsw1=1, sdac=dac)
            self.femb_config.configFeAsic(to_print = False)
            filename = a["DAC_Naming"].format(dac)
            rawdata = bytearray()
            full_filename = data_directory + filename
    
            rawdata += self.femb_config.femb.get_data_packets(data_type = "bin", num = 1, header = True)
            for pack in range (settings.monitor_length):
                rawdata += self.femb_config.femb.get_data_packets(data_type = "bin", num = 1, header = False)
                with open(full_filename,"wb") as f:
                    f.write(rawdata) 
                    f.close()
		
        with open(data_directory + 'Configuration.cfg', 'wb') as f:
            pickle.dump(a, f, pickle.HIGHEST_PROTOCOL)
		
        self.get_state(data_directory)
            
        print ("Test--> DAC step data collected for Chip {}".format(chip_name))
            
    def save_monitor_data(self, folder_path, chip_index, chip_name):
        print("Test--> Collecting monitor check data for Chip {}...".format(chip_name))
        sys.stdout.flush()
		
        test_directory = folder_path + settings.monitor_folder
        os.makedirs(test_directory)
		
        data_directory = test_directory + settings.data
        os.makedirs(data_directory)
		
        #Select the monitor readout
        self.femb_config.femb.write_reg(9, 3)
            
        #Get the ASIC to send out pulses.  Bit 6 needs to be high for ASIC DAC
        reg17_value = (settings.monitor_freq << 16) + (settings.monitor_delay << 8) + (0b01000000)
        self.femb_config.femb.write_reg(17, reg17_value)
        
        #Make sure the input to the DAC is not on
        self.femb_config.femb.write_reg(7, 0)
        
        #Read from test output ADCs
        self.femb_config.femb.write_reg(60, 1)
		
        a = settings.asic_settings
        for chn in range(settings.channels):
            self.femb_config.fe_reg.set_fe_board(sts=a["test_int"][0], snc=a["200mV"], sg=a["14mV"], st=a["2us"], 
					smn=0, sbf=a["b_on"], slk = a["500pA"][1], stb = 0, s16=0, slkh=a["500pA"][0], sdc=0, 
					sdacsw2=1, sdacsw1=0, sdac=settings.monitor_amplitude)
            self.femb_config.fe_reg.set_fe_chn(chip=chip_index, chn=chn, sts=1, snc=-1, sg=-1, st=-1, smn=1, sbf=-1)
            self.femb_config.configFeAsic(to_print = False)
    			
            self.femb_config.select_chip_chn(chip = chip_index, chn = chn)
            filename = a["Monitor_Naming"].format(chn)
            rawdata = bytearray()
            full_filename = data_directory + filename
    
#            rawdata += self.femb_config.femb.get_data_packets(data_type = "bin", num = 1, header = True)
            rawdata += self.femb_config.femb.get_data_packets(data_type = "bin", num = 1, header = False)[2:]
            for pack in range (settings.monitor_length):
                rawdata += self.femb_config.femb.get_data_packets(data_type = "bin", num = 1, header = False)[2:]
                with open(full_filename,"wb") as f:
                    f.write(rawdata) 
                    f.close()
                    
        self.femb_config.femb.write_reg(17, 0)
		
        with open(data_directory + 'Configuration.cfg', 'wb') as f:
            pickle.dump(a, f, pickle.HIGHEST_PROTOCOL)
		
        self.get_state(data_directory)
            
        print ("Test--> Monitor check data collected for Chip {}".format(chip_name))
              
    def save_pulse_data(self, folder_path, chip_index, chip_name):
        print("Test--> Collecting Pulse Calibration data for Chip {}...".format(chip_name))
        sys.stdout.flush()
        
        test_directory = folder_path + settings.pulse_folder
        os.makedirs(test_directory)
        
        data_directory = test_directory + settings.data
        os.makedirs(data_directory)

        #Select no MUX output
        self.femb_config.femb.write_reg(9, 2)
            
        #Get the ASIC to send out pulses.  Bit 6 needs to be high for ASIC DAC
        self.reg_17_value = (settings.pulse_freq << 16) + (settings.pulse_delay_min << 8) + (0b01000000)
        self.femb_config.femb.write_reg(17, self.reg_17_value)
        
        #Read from FE output ADCs
        self.femb_config.femb.write_reg(60, 0)
        
        a = settings.asic_settings
        for gain in a["gains"]:
            for peak in a["peaks"]:
                for leak in a["leaks"]:
                    for base in a["bases"]:
                        self.femb_config.fe_reg.set_fe_board(sts=1, snc=a[base], sg=a[gain], st=a[peak], 
                                        smn=0, sbf=0, slk = a[leak][1], stb = 0, s16=0, slkh=a[leak][0], 
                                        sdc=0, sdacsw2=1, sdacsw1=0, sdac=settings.pulse_delay_amplitude)
                                       
                        self.femb_config.configFeAsic(to_print = False)
                        specific_dir = a["Pulse_Naming2"].format(gain,peak,leak,base)
                        print ("Pulse Calibration --> Finding the optimum delay for {}".format(specific_dir))
                        self.int_dly_search(path = data_directory + specific_dir)
                        print ("Pulse Calibration --> Collecting Data for {}".format(specific_dir))
                            
                        for DAC_pulse_value in range(settings.pulse_DAC_min, settings.pulse_DAC_max + 1, 1):
    
                            self.femb_config.fe_reg.set_fe_board(sts=1, snc=a[base], sg=a[gain], st=a[peak], 
                                        smn=0, sbf=0, slk = a[leak][1], stb = 0, s16=0, slkh=a[leak][0], 
                                        sdc=0, sdacsw2=1, sdacsw1=0, sdac=DAC_pulse_value)
                                       
                            self.femb_config.configFeAsic(to_print = False)
                                                      
#                            debug = data_directory + specific_dir + "pulse_debug_info.txt"
#                            screendisplay = sys.stdout
#                            sys.stdout = open(debug, "a+")
#                            self.femb_config.fe_reg.info.fe_chip_status(chip_index, status = "sent")
#                            sys.stdout.close()
#                            sys.stdout = screendisplay
                            
                            for chn in range(settings.channels):
                                self.femb_config.select_chip_chn(chip = chip_index, chn = chn)
                                filename = a["Pulse_Naming"].format(chn,gain,peak,leak,base,DAC_pulse_value)
                                
                                rawdata = bytearray()
                                filename = data_directory + specific_dir + filename
                                
                                rawdata += self.femb_config.femb.get_data_packets(data_type = "bin", num = 1, header = True)
                                for pack in range (settings.pulse_length):
                                    rawdata += self.femb_config.femb.get_data_packets(data_type = "bin", num = 1, header = False)
                    
                                with open(filename,"a+b") as f:
                                   f.write(rawdata)
                                   f.close()
                                
        with open(data_directory + 'Configuration.cfg', 'wb') as f:
            pickle.dump(a, f, pickle.HIGHEST_PROTOCOL)
            
        self.get_state(data_directory)
        
        print ("Test--> Pulse Calibration data collected for Chip {}".format(chip_name))

        
    def int_dly_search(self, path):
        
        dly_pos = []
        self.dly = 0
        delay_plot_path = (path + "Delay_Plots/")
        os.makedirs(delay_plot_path)
        
        for dly in range(settings.pulse_delay_min, settings.pulse_delay_max,1):
            self.reg_17_value = (self.reg_17_value&0xFFFF00FF) + ((dly<<8)&0xFF00)
            self.femb_config.femb.write_reg(17, self.reg_17_value)
            
            np_data = self.femb_config.get_data_chipXchnX(chip = 1, chn = 7, packets = 50)
            pedmean = np.mean(np_data[0:2048])
            maxmean = max(np_data[0:2048])

            peaks_index = detect_peaks(x=np_data, mph=abs((maxmean-pedmean)/2)+pedmean, mpd=(settings.pulse_freq/2)) 
            peaks_value = []
            for i in peaks_index :
                peaks_value.append(np_data[i])
            peaksmean = np.mean(peaks_value)
            dly_pos.append(peaksmean)
            
            data_to_plot = np_data[(peaks_index[0]-10) : (peaks_index[0]+10)]
            delay_plot = self.analyze.quickPlot(data_to_plot)[1]
            
            delay_plot.savefig (delay_plot_path + "Delay_{}.png".format(dly))
            plt.close(delay_plot)

        max_peak = max(dly_pos)
        max_ind = np.where(dly_pos==max_peak)
        self.dly = self.dly + max_ind[0][0]
        self.reg_17_value = (self.reg_17_value&0xFFFF00FF) + ((self.dly<<8)&0xFF00)
        self.femb_config.femb.write_reg(17, self.reg_17_value)
        
    def plot_chips(self, data, plot_name, title_name):
        self.analyze.plot(data, plot_name, title_name)

    def get_state(self, folder):
        
        to_save = dict()
        for i in range(75):
            to_save["reg{}".format(i)] = hex(self.femb_config.femb.read_reg(i))
#            print ("Reg {} = {}".format(i, hex(self.sbnd.femb_config.femb.read_reg(i))))
        
        to_save["temp"] = settings.temp
        to_save["chip_num"] = settings.chip_num
        to_save["PC_IP"] = settings.PC_IP
        to_save["FPGA_IP"] = settings.FPGA_IP
        to_save["FEMB_VER"] = settings.FEMB_VER
        
        with open(folder + 'asic_state.cfg', 'wb') as f:
            pickle.dump(to_save, f, pickle.HIGHEST_PROTOCOL)

    def __init__(self):
        np.set_printoptions(threshold=np.inf)
        self.testpattern = ""
        self.freq = 500
        self.dly = 40 
        self.ampl = 0 #% 32
        self.int_dac = 0 # or 0xA1
        self.dac_meas = self.int_dac  # or 60
        self.reg_17_value = None

        self.femb_config = FEMB_CONFIG()

        self.path = ""
        
        self.analyze = plot_functions()
        
        self.current_st = None
        self.current_sg = None
