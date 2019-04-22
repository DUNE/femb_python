# -*- coding: utf-8 -*-
"""
Created on Tue Mar  5 13:52:17 2019

@author: eraguzin
"""
import os
import sys
import struct
import matplotlib.pyplot as plt
plt.switch_backend('agg')
import matplotlib.patches as mpatches
from femb_python.test_measurements.quad_FE_Board.detect_peaks import detect_peaks
from femb_python.test_measurements.quad_FE_Board.plotting import plot_functions
import warnings
with warnings.catch_warnings():
    warnings.simplefilter("ignore", category=RuntimeWarning)

class Data_Analysis:
    def __init__(self, config):
        self.plot = plot_functions()
        self.config = config
        
        ADC_voltage = float(self.config["DEFAULT"]["ADC_REF_VOLTAGE"]) * 1000
        num_bits = int(self.config["DEFAULT"]["ADC_FULL_SCALE"], 16)
        self.bits_to_mv = ADC_voltage/num_bits
        
    def alive_directory(self, directory, chip, datasubdir, tests, leaks, temp):
        print("Test--> Analyzing 'Channel Alive' data for Chip {}...".format(chip))
        
        self.data_folder = os.path.join(directory,datasubdir)

        data_file_scheme = self.config["FILENAMES"]["ALIVE_NAMING"]
        data_file_scheme_cycle = self.config["FILENAMES"]["ALIVE_NAMING2"]
        
        fig_summary = plt.figure(figsize=(16, 12), dpi=80)
        ax = fig_summary.add_subplot(1,1,1)
        ax.set_xlabel('Time (us)')
        for item in ([ax.xaxis.label, ax.yaxis.label] + ax.get_xticklabels() + ax.get_yticklabels()):
            item.set_fontsize(20)
            
        overall_result = True
        fails = []
        for i, test in enumerate(tests):
            for j, leak in enumerate([leaks]):
                 for chn in range(int(self.config["DEFAULT"]["NASICCH_MIN"]), int(self.config["DEFAULT"]["NASICCH_MAX"]) + 1, 1):
                    self.filename = data_file_scheme.format(chn,leak,test)
                    sample_pulse, result = self.alive_file(os.path.join(self.data_folder,self.filename))
                    overall_result = overall_result and result
                    if (result == False):
                        fails.append("Channel {}, {} not found!".format(chn,test))
                    if (test == "test_off"):
                        plot_color = "green"
                    elif (test == "test_ext"):
                        plot_color = "red"
                    ax.plot(sample_pulse, color = plot_color)
            if (temp == "LN"):
                for cycle in range(int(self.config["ALIVE_SETTINGS"]["ALIVE_POWER_CYCLES"])):
                    self.filename = data_file_scheme_cycle.format(leak,test,cycle)
                    sample_pulse, result = self.alive_file(os.path.join(self.data_folder,self.filename))
                    overall_result = overall_result and result
                    if (result == False):
                            fails.append("Cycle {}, {} not found!".format(cycle,test))
                    plot_color = "blue"
                    ax.plot(sample_pulse, color = plot_color)
                    
        green_patch = mpatches.Patch(color='green', label='Input pin to FE')
        red_patch = mpatches.Patch(color='red', label='Test pin to FE')
        blue_patch = mpatches.Patch(color='blue', label='Pulses after power cycles')
        plt.legend(handles=[green_patch, red_patch, blue_patch])
                    
        ax.set_ylabel('mV')
        ax.set_title("Sample pulses for Chip {} Channel Alive Test".format(chip))
        ax.title.set_fontsize(30)
        ax.set_ylim(0, 1000 * float(self.config["DEFAULT"]["ADC_REF_VOLTAGE"]))
        
        if len(fails) > 0:
            for num,i in enumerate(fails):
                ax.text(0.05,0.95 - (0.05 * num),i,transform=ax.transAxes, fontsize = 20)
        else:
            ax.text(0.05,0.95,"All peaks found!",transform=ax.transAxes, fontsize = 20)
        
        alive_text = self.config["FILENAMES"]["ALIVE_LINK"]
        save_file = os.path.join(directory,alive_text)
        fig_summary.savefig (save_file)
        plt.close(fig_summary)      
                
        print ("Test--> 'Channel Alive' data analyzed for Chip {}".format(chip))
        return overall_result
                        
    def alive_file(self, filepath):
        fileinfo  = os.stat(filepath)
        filelength = fileinfo.st_size

        with open(filepath, 'rb') as f:
            raw_data = f.read(filelength)
            f.close()
        #Filelength is in bytes, but the data we're getting is 2 bytes each
        unpacked_shorts = struct.unpack_from(">{}H".format(int(filelength/2)),raw_data)

        #Ignore header for now
        data = unpacked_shorts[8:]
        data_mv = []
        for i in range(len(data)):
            data_mv.append(data[i] * self.bits_to_mv)
        
        failure = False
        peaks_index = detect_peaks(x = data_mv, mph = int(self.config["ALIVE_SETTINGS"]["ALIVE_PEAK_MIN"])/2, mpd=int(self.config["SYNC_SETTINGS"]["SYNC_PULSE_SPACING"])-5)
        peaks_value = []
        for i in peaks_index :
            peaks_value.append(data_mv[i])
        
        peak_num = len(peaks_index)
        response = "Channel response response good"
        if ((peak_num < int(self.config["ALIVE_SETTINGS"]["ALIVE_PEAKS_MIN"])) or (peak_num > int(self.config["ALIVE_SETTINGS"]["ALIVE_PEAKS_MAX"]))):
            failure = True
            response = "Number of peaks should be between {} and {}, but it was {:.0f}.  Wanted peaks above {}".format(self.config["ALIVE_SETTINGS"]["ALIVE_PEAKS_MIN"],
                self.config["ALIVE_SETTINGS"]["ALIVE_PEAKS_MAX"], peak_num, self.config["ALIVE_SETTINGS"]["ALIVE_PEAK_MIN"])
    
        figure_data = self.plot.quickPlot(data_mv)
        ax = figure_data[0]
        for j in peaks_index:
            y_value = data_mv[j]
            ax.scatter(j * float(self.config["DEFAULT"]["SAMPLE_PERIOD"]), y_value, marker='x')
    
        ax.set_ylabel('mV')
        ax.set_title(self.filename)
        ax.title.set_fontsize(30)
        x_lim = ax.get_xlim()
        ax.set_xlim(0, x_lim[1])
        ax.text(0.01,0.95,response,transform=ax.transAxes, fontsize = 20)
        for item in ([ax.xaxis.label, ax.yaxis.label] +ax.get_xticklabels() + ax.get_yticklabels()):
            item.set_fontsize(20)
        save_file = os.path.join(self.data_folder,self.filename[:len(self.filename)-4] + ".png")
        figure_data[1].savefig (save_file)
        plt.close(figure_data[1])
                            
        plot_data = data_mv[500-int(self.config["ALIVE_SETTINGS"]["ALIVE_PLOT_X_BACK"]) : 500 + int(self.config["ALIVE_SETTINGS"]["ALIVE_PLOT_X_FORWARD"])]
        if (len(peaks_index) >= 1):
            peak = peaks_index[1]
            plot_data = data_mv[peak - int(self.config["ALIVE_SETTINGS"]["ALIVE_PLOT_X_BACK"]) : peak + int(self.config["ALIVE_SETTINGS"]["ALIVE_PLOT_X_FORWARD"])]
            
        return plot_data, not failure