# -*- coding: utf-8 -*-
"""
Created on Fri Jun  2 11:50:17 2017

@author: vlsilab2
"""

import os
import sys
import struct
import matplotlib.pyplot as plt
plt.switch_backend('agg')
import numpy as np
from femb_python.test_measurements.quad_FE_Board.detect_peaks import detect_peaks
from femb_python.test_measurements.quad_FE_Board.plotting import plot_functions
import json
import warnings
with warnings.catch_warnings():
    warnings.simplefilter("ignore", category=RuntimeWarning)

class Data_Analysis:
    def __init__(self, config):
        self.plot = plot_functions()
        self.config = config
        
    def monitor_directory(self, directory, datasubdir, chip_name, chip_index, jsonFile):
        print("Monitor_Test_Analysis --> --> Analyzing Monitor data for Chip {}...".format(chip_name))
        sys.stdout.flush()
        #Finds whatever the name of the baseline directory is (this is so it can be changed without problem) and gets the directories within
        self.test_folder = os.path.join(directory,datasubdir)

        data_file_scheme = self.config["FILENAMES"]["MONITOR_NAMING"]
        
        fig_summary = plt.figure(figsize=(16, 12), dpi=80)
        ax = fig_summary.add_subplot(1,1,1)
        ax.set_xlabel('Time (us)')
        for item in ([ax.xaxis.label, ax.yaxis.label] + ax.get_xticklabels() + ax.get_yticklabels()):
            item.set_fontsize(20)
        overall_result = True
        
        fig_summary2 = plt.figure(figsize=(16, 12), dpi=80)
        ax2 = fig_summary2.add_subplot(1,1,1)
        ax2.set_xlabel('Time (us)')
        for item in ([ax2.xaxis.label, ax2.yaxis.label] + ax2.get_xticklabels() + ax2.get_yticklabels()):
            item.set_fontsize(20)
        
        #load baseline data to subtract in analysis
        peaks = []
        baselines = []
        if os.path.isfile(jsonFile):
            with open(jsonFile, 'r') as f:
                baseline_data = json.load(f)

            for chn in range(int(self.config["DEFAULT"]["NASICCH_MIN"]), int(self.config["DEFAULT"]["NASICCH_MAX"]) + 1, 1):
                index_name = "baseline_200_channel{}".format(chn)
                baseline = baseline_data[index_name]
                baselines.append(float(baseline))
        else:
            print("Monitor_Test_Analysis --> COULD NOT FIND {}".format(jsonFile))
            baselines = [0]*16
        fails = []
        for chn in range(int(self.config["DEFAULT"]["NASICCH_MIN"]), int(self.config["DEFAULT"]["NASICCH_MAX"]) + 1, 1):
            self.filename = data_file_scheme.format(chn)
            filepath = os.path.join(self.test_folder,self.filename)
            sample_pulse, result, average, corrected_pulse = self.monitor_file(filepath, baselines[chn])
            if (result == False):
                fails.append("Channel {} not found!".format(chn))
            overall_result = result and overall_result
            peaks.append(average)
            ax.plot(sample_pulse)
            ax2.plot(corrected_pulse)
                    
        ax.set_ylabel('mV')
        ax.set_title("Sample pulses for Chip {} Monitor Test".format(chip_name))
        ax.title.set_fontsize(30)
        ax.set_ylim(0, 1000 * float(self.config["DEFAULT"]["ADC_REF_VOLTAGE"]))

        if len(fails) > 0:
            for num,i in enumerate(fails):
                ax.text(0.05,0.95 - (0.05 * num),i,transform=ax.transAxes, fontsize = 20)
        else:
            ax.text(0.05,0.95,"All peaks found!",transform=ax.transAxes, fontsize = 20)
        
        save_file = (os.path.join(directory,"Sample_Pulses.png"))
        fig_summary.savefig (save_file)
        plt.close(fig_summary)

        
        average_peak = np.mean(peaks)
        
        differences = []
        for chn in range(int(self.config["DEFAULT"]["NASICCH_MIN"]), int(self.config["DEFAULT"]["NASICCH_MAX"]) + 1, 1):
            difference = average_peak - peaks[chn]
            differences.append(difference)            
            
        ax2.set_ylabel('mV')
        ax2.set_title("Sample pulses for Chip {} Monitor Test, baseline corrected".format(chip_name))
        ax2.title.set_fontsize(30)
        ax2.set_ylim(0, 1000 * float(self.config["DEFAULT"]["ADC_REF_VOLTAGE"]))
        response1 = "Average peak was {:.2f}".format(average_peak)
        response2 = "Average deviation was {:.2f}%".format(np.mean(differences))
        response3 = "Maximum deviation was {:.2f}%".format((max(differences)/average_peak) * 100)
        ax2.text(0.05,0.8,response1,transform=ax.transAxes, fontsize = 20)
        ax2.text(0.05,0.75,response2,transform=ax.transAxes, fontsize = 20)
        ax2.text(0.05,0.7,response3,transform=ax.transAxes, fontsize = 20)
        
        save_file = (os.path.join(directory,"Sample_Pulses_Gain_Matched.png"))
        fig_summary2.savefig (save_file)
        plt.close(fig_summary2)      
                
        for chn in range(int(self.config["DEFAULT"]["NASICCH_MIN"]), int(self.config["DEFAULT"]["NASICCH_MAX"]) + 1, 1):
            peaks[chn] = [chn,peaks[chn]]                
                
        print ("Monitor_Test_Analysis -->  Monitor data analyzed for Chip {}".format(chip_name))
        return overall_result, peaks, differences, average_peak
                    
    def monitor_file(self, filepath, baseline):
        fileinfo  = os.stat(filepath)
        filelength = fileinfo.st_size
        with open(filepath, 'rb') as f:
            raw_data = f.read(filelength)
            f.close()

        #Filelength is in bytes, but the data we're getting is 2 bytes each
        unpacked_shorts = struct.unpack_from(">{}H".format(int(filelength/2)),raw_data)

        ADC_voltage = float(self.config["DEFAULT"]["ADC_REF_VOLTAGE"]) * 1000
        num_bits = int(self.config["DEFAULT"]["ADC_FULL_SCALE"], 16)
        bits_to_mv = ADC_voltage/num_bits
        data = unpacked_shorts
        data_mv = []
        for i in range(len(data)):
            data_mv.append(data[i] * bits_to_mv)
        
        failure = False
        peaks_index = detect_peaks(x = data_mv, mph = int(self.config["MONITOR_SETTINGS"]["MONITOR_PEAK_MIN"]) / 2, mpd = int(self.config["SYNC_SETTINGS"]["SYNC_PULSE_SPACING"]) - 5)
        peak_num = len(peaks_index)
        response = "Channel response good!"
        if ((peak_num < int(self.config["MONITOR_SETTINGS"]["MONITOR_PEAK_NUM_MIN"])) or (peak_num > int(self.config["MONITOR_SETTINGS"]["MONITOR_PEAK_NUM_MAX"]))):
            failure = True
            response = "Number of peaks should be between {} and {}, but it was {:.0f}".format(int(self.config["MONITOR_SETTINGS"]["MONITOR_PEAK_NUM_MIN"]), int(self.config["MONITOR_SETTINGS"]["MONITOR_PEAK_NUM_MAX"]), peak_num)

        figure_data = self.plot.quickPlot(data_mv)
        ax = figure_data[0]
        for j in peaks_index:
            y_value = data_mv[j]
            ax.scatter(j * float(self.config["DEFAULT"]["SAMPLE_PERIOD"]), y_value, marker='x')
            
        ax.set_ylabel('mV')
        ax.set_title(self.filename)
        ax.title.set_fontsize(30)
        ax.text(0.01,0.95,response,transform=ax.transAxes, fontsize = 20)
        for item in ([ax.xaxis.label, ax.yaxis.label] +ax.get_xticklabels() + ax.get_yticklabels()):
            item.set_fontsize(20)
        save_file = os.path.join(self.test_folder,self.filename[:len(self.filename)-4] + ".png")
        figure_data[1].savefig (save_file)
        plt.close(figure_data[1])
            
        plot_data = data_mv[500-int(self.config["MONITOR_SETTINGS"]["MONITOR_PLOT_X_BACK"]) : 500 + int(self.config["MONITOR_SETTINGS"]["MONITOR_PLOT_X_FORWARD"])]
        if (len(peaks_index) >= 1):
            peak = peaks_index[1]
            plot_data = data_mv[peak - int(self.config["MONITOR_SETTINGS"]["MONITOR_PLOT_X_BACK"]) : peak + int(self.config["MONITOR_SETTINGS"]["MONITOR_PLOT_X_FORWARD"])]
        data_mv = []
        for i in range(len(data)):
            data_mv.append(data[i] * bits_to_mv - baseline)
                
        plot_data_corrected = data_mv[500-int(self.config["MONITOR_SETTINGS"]["MONITOR_PLOT_X_BACK"]) : 500 + int(self.config["MONITOR_SETTINGS"]["MONITOR_PLOT_X_FORWARD"])]
        
        if (len(peaks_index) >= 1):
            peak = peaks_index[1]
            plot_data_corrected = data_mv[peak - int(self.config["MONITOR_SETTINGS"]["MONITOR_PLOT_X_BACK"]) : peak + int(self.config["MONITOR_SETTINGS"]["MONITOR_PLOT_X_FORWARD"])]
            
        peaks_index = detect_peaks(x = data_mv, mph = int(self.config["MONITOR_SETTINGS"]["MONITOR_PEAK_MIN"]) / 2, mpd = int(self.config["SYNC_SETTINGS"]["SYNC_PULSE_SPACING"]) - 5)
        
        peaks_value = []
        for i in peaks_index:
            if (data_mv[i] > int(self.config["MONITOR_SETTINGS"]["MONITOR_PEAK_MIN"])):
                peaks_value.append(data_mv[i])
                
        average = np.mean(peaks_value)
        return plot_data, not failure, average, plot_data_corrected