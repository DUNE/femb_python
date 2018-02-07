import struct
import time
from scripts.femb_config_sbnd import FEMB_CONFIG
from scripts.adc_asic_reg_mapping import ADC_ASIC_REG_MAPPING
from scripts.fe_asic_reg_mapping import FE_ASIC_REG_MAPPING
import numpy as np
from scripts.detect_peaks import detect_peaks
import os
import sys
import matplotlib.pyplot as plt

from scripts.Data_Analysis import Data_Analysis
from user_settings import user_editable_settings
settings = user_editable_settings()
class FEMB_DAQ:

    def save_rms_noise(self):
        
        file_rec = self.path + "\\" + "noise_test_debug_info.txt"
        screendisplay = sys.stdout
        sys.stdout = open(file_rec, "a+")
        
        print ("FEMB_DAQ-->RMS measurement start")
        
        self.femb_config.configAdcAsic()
        self.femb_config.configFeAsic()
        
        
        for i in range(settings.chip_num):
            self.femb_config.fe_reg.info.fe_chip_status(i, status = "sent")
            self.femb_config.adc_reg.info.adc_chip_status(i, status = "sent")
            
        
        #Disable all test pulses
        self.femb_config.femb.write_reg(18, 0x1, board = "femb")
        
        #Disable FPGA test pulse
        self.femb_config.femb.write_reg(16, 0x1, board = "femb")

        rawdata = bytearray()
        filename = self.path + "\\" + "pedestal.dat"
        for chip in range(settings.chip_num):
            rawdata += self.femb_config.femb.get_data_packets(settings.CHIP_IP[chip], 
                                                              data_type = "bin", num = 1, header = True)
            for pack in range (383):
                rawdata += self.femb_config.femb.get_data_packets(settings.CHIP_IP[chip], 
                                                                  data_type = "bin", num = 1, header = False)

        with open(filename,"wb") as f:
            f.write(rawdata) 
            f.close()

        print ("FEMB_DAQ-->RMS measurement is DONE")
        
        sys.stdout.close()
        sys.stdout = screendisplay

    def ext_dly_search(self):
        print ("FEMB_DAQ-->Start to find proper DLY to locate the peak of shaper")
        #set proper ampl, which will let ADC value fall between 0x7ff and 0xb00
        ampl = 1
        print ("FEMB_DAQ-->Finding the optimal pulse height")
        while ( ampl < 32 ): 
            self.reg_5_value = (self.reg_5_value&0xFFFFFF00) + (ampl&0xFF)
            self.femb_config.femb.write_reg(5, self.reg_5_value, board = "femb")
            
            time.sleep(0.01)
            
            np_data = self.femb_config.get_data_chipXchnX(chip = 1, chn = 7, packets = 42)
            pedmean = np.mean(np_data[0:2048])
            peaks_index = detect_peaks(x=np_data, mph=(pedmean+200), mpd=(self.freq/2)) 
            peaks_value = []

            for i in peaks_index :
                peaks_value.append(np_data[i])
                
            print (peaks_value)
            if (len(peaks_value) > 1):
                peaksmean = np.mean(peaks_value)
                if (peaksmean > 0x7ff):
                    break
                else:
                    ampl = ampl + 1 
            else:
                    ampl = ampl + 1 

        dly_pos = []
        self.dly = 1
        delay_plot_path = (self.path+"\\Delay_Plots\\")
        if (os.path.exists(delay_plot_path) != True):
            try: 
                os.makedirs(delay_plot_path)
            except OSError:
                if os.path.exists(delay_plot_path):
                    raise 
        print ("FEMB_DAQ-->Finding the optimal delay")
        for dly in range(self.dly, self.dly+50,1):
            self.reg_5_value = (self.reg_5_value&0xFFFF00FF) + ((dly<<8)&0xFF00)
            self.femb_config.femb.write_reg(5, self.reg_5_value, board = "femb")
            
            np_data = self.femb_config.get_data_chipXchnX(chip = 1, chn = 7, packets = 42)
            pedmean = np.mean(np_data[0:2048])
            maxmean = max(np_data[0:2048])

            peaks_index = detect_peaks(x=np_data, mph=abs((maxmean-pedmean)/2)+pedmean, mpd=(self.freq/2)) 
            peaks_value = []
            for i in peaks_index :
                peaks_value.append(np_data[i])
            peaksmean = np.mean(peaks_value)
            dly_pos.append(peaksmean)
            
            data_to_plot = np_data[(peaks_index[0]-10) : (peaks_index[0]+10)]
            delay_plot = self.analyze.quickPlot(data_to_plot)
            
            delay_plot.savefig (delay_plot_path+"Delay_" + str(dly) + ".jpg")
            plt.close(delay_plot)
            
            print(peaks_index)
            print(peaks_value)

        max_peak = max(dly_pos)
        max_ind = np.where(dly_pos==max_peak)
        self.dly = self.dly + max_ind[0][0]
        self.reg_5_value = (self.reg_5_value&0xFFFF00FF) + ((self.dly<<8)&0xFF00)
        self.femb_config.femb.write_reg(5, self.reg_5_value, board = "femb")
        print ("FEMB_DAQ-->Best DLY for current configuration is: %d"%self.dly)

    def fpga_dac_cali(self):
        
        self.path = self.path + "\\cali_fpgadac\\"
        if (os.path.exists(self.path) != True):
            try: 
                os.makedirs(self.path)
            except OSError:
                if os.path.exists(self.path):
                    raise 
                    
        file_rec = self.path + "\\" + "gain_fpga_test_debug_info.txt"
        screendisplay = sys.stdout
        sys.stdout = open(file_rec, "a+")
        
        print ("FEMB_DAQ-->Calibration measurement with FPGA \"DAC\" starts")
        self.femb_config.configAdcAsic()
        self.femb_config.configFeAsic()
        
        for i in range(settings.chip_num):
            self.femb_config.fe_reg.info.fe_chip_status(i, status = "sent")
            self.femb_config.adc_reg.info.adc_chip_status(i, status = "sent")
            
        #Enable test pulses
        self.femb_config.femb.write_reg(18, 0x0, board = "femb")
        
        #Enable FPGA test pulse
        self.femb_config.femb.write_reg(16, 0x101, board = "femb")

        self.ext_dly_search()
        for dac in range(0,32,1):
            filename = self.path + "fpgadac_%x.dat"%dac
            self.ampl = dac 
            self.reg_5_value = (self.reg_5_value&0xFFFFFF00) + (self.ampl&0xFF)
            self.femb_config.femb.write_reg(5, self.reg_5_value, board = "femb")

            rawdata = bytearray()
            for chip in range(settings.chip_num):
                rawdata += self.femb_config.femb.get_data_packets(settings.CHIP_IP[chip], 
                                                              data_type = "bin", num = 1, header = True)
                for pack in range (1000):
                    rawdata += self.femb_config.femb.get_data_packets(settings.CHIP_IP[chip], 
                                                                       data_type = "bin", num = 1, header = False)

            with open(filename,"a+b") as f:
               f.write(rawdata)
               f.close()
               
        #Disable all test pulses
        self.femb_config.femb.write_reg(18, 0x1, board = "femb")
        
        #Disable FPGA test pulse
        self.femb_config.femb.write_reg(16, 0x1, board = "femb")
               
        print ("FEMB_DAQ-->Calibration measurement with FPGA \"DAC\" is DONE")

        sys.stdout.close()
        sys.stdout = screendisplay
        

    def int_dly_search(self):
        print ("FEMB_DAQ-->Start to find proper DLY to locate the peak of shaper")
        #set proper ampl, which will let ADC value fall between 0x7ff and 0xb00
        ampl = 1
        print ("FEMB_DAQ-->Finding the optimal pulse height")
        while ( ampl < 32 ): 
            self.reg_5_value = (self.reg_5_value&0xFFFFFF00) + (ampl&0xFF)
            self.femb_config.femb.write_reg(5, self.reg_5_value, board = "femb")
            
            self.femb_config.fe_reg.set_fe_board() # reset the registers value
            self.femb_config.fe_reg.set_fe_board(sts=1,sg=self.current_sg[0], st=self.current_st[0], snc=1,
                                                      sdacsw1=0, sdacsw2=1, sdac=ampl)
            self.femb_config.configFeAsic()
            
            time.sleep(0.01)
            
            np_data = self.femb_config.get_data_chipXchnX(chip = 1, chn = 7, packets = 42)
            pedmean = np.mean(np_data[0:2048])
            peaks_index = detect_peaks(x=np_data, mph=(pedmean+200), mpd=(self.freq/2)) 
            peaks_value = []

            for i in peaks_index :
                peaks_value.append(np_data[i])
                
            print (peaks_value)
            if (len(peaks_value) > 1):
                peaksmean = np.mean(peaks_value)
                if (peaksmean > 0x7ff):
                    break
                else:
                    ampl = ampl + 1 
            else:
                    ampl = ampl + 1 
        
        

        dly_pos = []
        self.dly = 1
        delay_plot_path = (self.path+"\\Delay_Plots\\")
        if (os.path.exists(delay_plot_path) != True):
            try: 
                os.makedirs(delay_plot_path)
            except OSError:
                if os.path.exists(delay_plot_path):
                    raise 
        print ("FEMB_DAQ-->Finding the optimal delay")
        
        for dly in range(self.dly, self.dly+50,1):
            self.reg_5_value = (self.reg_5_value&0xFFFF00FF) + ((dly<<8)&0xFF00)
            self.femb_config.femb.write_reg(5, self.reg_5_value, board = "femb")
            
            np_data = self.femb_config.get_data_chipXchnX(chip = 1, chn = 7, packets = 42)
            pedmean = np.mean(np_data[0:2048])
            maxmean = max(np_data[0:2048])

            peaks_index = detect_peaks(x=np_data, mph=abs((maxmean-pedmean)/2)+pedmean, mpd=(self.freq/2)) 
            peaks_value = []
            for i in peaks_index :
                peaks_value.append(np_data[i])
            peaksmean = np.mean(peaks_value)
            dly_pos.append(peaksmean)
            
            data_to_plot = np_data[(peaks_index[0]-10) : (peaks_index[0]+10)]
            delay_plot = self.analyze.quickPlot(data_to_plot)
            
            delay_plot.savefig (delay_plot_path+"Delay_" + str(dly) + ".jpg")
            plt.close(delay_plot)
            
            print(peaks_index)
            print(peaks_value)

        max_peak = max(dly_pos)
        max_ind = np.where(dly_pos==max_peak)
        self.dly = self.dly + max_ind[0][0]
        self.reg_5_value = (self.reg_5_value&0xFFFF00FF) + ((self.dly<<8)&0xFF00)
        self.femb_config.femb.write_reg(5, self.reg_5_value, board = "femb")
        print ("FEMB_DAQ-->Best DLY for current configuration is: %d"%self.dly)
        return ampl

              
    def intdac_cali(self):
        self.path = self.path + "\\cali_intdac\\"
        if (os.path.exists(self.path) != True):
            try: 
                os.makedirs(self.path)
            except OSError:
                if os.path.exists(self.path):
                    raise 
                    
        file_rec = self.path + "\\" + "gain_int_test_debug_info.txt"
        screendisplay = sys.stdout
        sys.stdout = open(file_rec, "a+")
        
        print ("FEMB_DAQ-->Calibration measurement with internal DAC starts")
        self.femb_config.configAdcAsic()
        self.femb_config.configFeAsic()
        
        for i in range(settings.chip_num):
            self.femb_config.fe_reg.info.fe_chip_status(i, status = "sent")
            self.femb_config.adc_reg.info.adc_chip_status(i, status = "sent")
            
        #Enable test pulses
        self.femb_config.femb.write_reg(18, 0x0, board = "femb")
        
        #Enable internal test pulses
        self.femb_config.femb.write_reg(16, 0x2, board = "femb")
            

        self.int_dly_search()

        for dac in range(0,64,1):
            filename = self.path + "intdac_%x.dat"%dac

            self.femb_config.fe_reg.set_fe_board() # reset the registers value
            self.femb_config.fe_reg.set_fe_board(sts=1,sg=self.current_sg[0], st=self.current_st[0], snc=1,
                                                      sdacsw1=0, sdacsw2=1, sdac=dac)
            self.femb_config.configFeAsic()

            rawdata = bytearray()
            for chip in range(settings.chip_num):
                rawdata += self.femb_config.femb.get_data_packets(settings.CHIP_IP[chip], 
                                                              data_type = "bin", num = 1, header = True)
                for pack in range (1000):
                    rawdata += self.femb_config.femb.get_data_packets(settings.CHIP_IP[chip], 
                                                                       data_type = "bin", num = 1, header = False)

            with open(filename,"a+b") as f:
               f.write(rawdata)
               f.close()
               
        
        print ("FEMB_DAQ-->Calibration measurement with internal DAC is DONE")
        sys.stdout.close()
        sys.stdout = screendisplay


    def make_dir(self, path):
        self.path = path + "\\" + self.testpattern + "\\"
        if (os.path.exists(self.path) != True):
            try: 
                os.makedirs(self.path)
            except OSError:
                if os.path.exists(self.path):
                    raise

    def __init__(self):
        np.set_printoptions(threshold=np.inf)
        self.testpattern = ""
        self.freq = 500
        self.dly = 40 
        self.ampl = 0 #% 32
        self.int_dac = 0 # or 0xA1
        self.dac_meas = self.int_dac  # or 60
        self.reg_5_value = ((self.freq<<16)&0xFFFF0000) + ((self.dly<<8)&0xFF00) + \
                ( (self.dac_meas|self.ampl)& 0xFF )

        self.femb_config = FEMB_CONFIG()
        self.adc_reg = ADC_ASIC_REG_MAPPING()
        self.fe_reg = FE_ASIC_REG_MAPPING() 
        self.path = ""
        
        self.analyze = Data_Analysis()
        
        self.current_st = None
        self.current_sg = None