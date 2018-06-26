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
import pickle
import numpy as np
import warnings
import matplotlib.patches as mpatches
from femb_python.test_measurements.sbnd_femb_test.detect_peaks import detect_peaks
from femb_python.test_measurements.sbnd_femb_test.plotting import plot_functions
from scipy import stats
import math
import json
import warnings
with warnings.catch_warnings():
    warnings.simplefilter("ignore", category=RuntimeWarning)

from femb_python.configuration import CONFIG

class Data_Analysis2:
        
    def monitor_directory(self, directory, chip, datasubdir, datadir, gain, shape, leak, buff, base):
        print("Test--> Analyzing Monitor data for Chip {}...".format(chip))
        sys.stdout.flush()
        #Finds whatever the name of the baseline directory is (this is so it can be changed without problem) and gets the directories within
        self.test_folder = os.path.join(directory,datasubdir)
        data_folder = os.path.join(self.test_folder,"Data")

        data_file_scheme = "Monitor_ch_{}.dat"
        
        fig_summary = plt.figure(figsize=(16, 12), dpi=80)
        ax = fig_summary.add_subplot(1,1,1)
        ax.set_xlabel('Time (us)')
        for item in ([ax.xaxis.label, ax.yaxis.label] + ax.get_xticklabels() + ax.get_yticklabels()):
            item.set_fontsize(20)
        overall_result = True
        
        fig_summary2 = plt.figure(figsize=(16, 12), dpi=80)
        ax2 = fig_summary2.add_subplot(1,1,1)
        ax2.set_xlabel('Time (us)')
        for item in ([ax2.xaxis.label, ax.yaxis.label] + ax2.get_xticklabels() + ax2.get_yticklabels()):
            item.set_fontsize(20)
        
        #load baseline data
        peaks = [] 
        baseline_json_file = os.path.join(directory,"baseline_test_sequence-g{}s{}b{}-0010".format(gain,shape,base),"results.json")
        if os.path.isfile(baseline_json_file):
            with open(baseline_json_file, 'r') as f:
                baseline_data = json.load(f)
                results = baseline_data['results']

            for chn in range(self.femb_config.channels):  
                self.filename = data_file_scheme.format(chn)
                baseline = float(results[chn]['baseline'])   
                sample_pulse, result, average, corrected_pulse = self.monitor_file(os.path.join(data_folder,self.filename), baseline)
                overall_result = result and overall_result
                peaks.append(average)
                ax.plot(sample_pulse)
                ax2.plot(corrected_pulse)
        else:
            print("COULD NOT FIND {}".format(baseline_json_file))
                    
        ax.set_ylabel('mV')
        ax.set_title("Sample pulses for Chip {} Monitor Test".format(chip))
        ax.title.set_fontsize(30)
        save_file = (os.path.join(self.test_folder,"Sample_Pulses.png"))
        fig_summary.savefig (save_file)
        plt.close(fig_summary)

        
        average_peak = np.mean(peaks)
        
        differences = []
        for chn in range(self.femb_config.channels):
            difference = average_peak - peaks[chn]
            differences.append(difference)            
            
        ax2.set_ylabel('mV')
        ax2.set_title("Sample pulses for Chip {} Monitor Test, baseline corrected".format(chip))
        ax2.title.set_fontsize(30)
        response1 = "Average peak was {:.2f}".format(average_peak)
        response2 = "Average deviation was {:.2f}%".format(np.mean(differences))
        response3 = "Maximum deviation was {:.2f}%".format((max(differences)/average_peak) * 100)
        ax2.text(0.01,0.8,response1,transform=ax.transAxes, fontsize = 20)
        ax2.text(0.01,0.75,response2,transform=ax.transAxes, fontsize = 20)
        ax2.text(0.01,0.7,response3,transform=ax.transAxes, fontsize = 20)
        
        save_file = (os.path.join(self.test_folder,"Sample_Pulses_Gain_Matched.png"))
        fig_summary2.savefig (save_file)
        plt.close(fig_summary2)      
                
        for chn in range(self.femb_config.channels):
            peaks[chn] = [chn,peaks[chn]]                
                
        print ("Test--> Monitor data analyzed for Chip {}".format(chip))
        return overall_result, peaks, differences, average_peak
                    
    def monitor_file(self, filepath, baseline):
        fileinfo  = os.stat(filepath)
        filelength = fileinfo.st_size

        with open(filepath, 'rb') as f:
            raw_data = f.read(filelength)
            f.close()
        #Filelength is in bytes, but the data we're getting is 2 bytes each
        unpacked_shorts = struct.unpack_from(">{}H".format(int(filelength/2)),raw_data)

        #Ignore header for now
#        data = unpacked_shorts[8:]
        data = unpacked_shorts
        data_mv = []
        for i in range(len(data)):
            data_mv.append(data[i] * self.femb_config.bits_to_mv)
        
        failure = False
        peaks_index = detect_peaks(x = data_mv, mph = (self.femb_config.monitor_peak_min / 2), mpd=50) 
        peaks_value = []
        peaks_index_fix = []
        for i in peaks_index:
            if (data_mv[i] > self.femb_config.monitor_peak_min):
                peaks_value.append(data_mv[i])
                peaks_index_fix.append(i)
#        print ("Chip {}, Channel {} has peak values {}".format(chip, chn, peaks_value))
        #Check if the peak is in the wrong place (happens when it's not synced)
        response = "Good response, channel is detected"
        
        peak_num = len(peaks_index_fix)     
        if ((peak_num <= self.femb_config.monitor_peaks_min) or (peak_num >= self.femb_config.monitor_peaks_max)):
            failure = "num"
            response = "Number of peaks should be between {} and {}, but it was {:.0f}".format(self.femb_config.monitor_peaks_min, self.femb_config.monitor_peaks_max, peak_num)

#        if (failure != False):
        rejects_folder = os.path.join(self.test_folder,"Plots/")
        if (os.path.exists(rejects_folder) == False):
            os.makedirs(rejects_folder)

        figure_data = self.plot.quickPlot(data_mv)
        ax = figure_data[0]
        for j in peaks_index_fix:
            y_value = data_mv[j]
            ax.scatter(j/2, y_value, marker='x')
            
        ax.set_ylabel('mV')
        ax.set_title(self.filename)
        ax.title.set_fontsize(30)
        ax.text(0.01,0.95,response,transform=ax.transAxes, fontsize = 20)
        for item in ([ax.xaxis.label, ax.yaxis.label] +ax.get_xticklabels() + ax.get_yticklabels()):
            item.set_fontsize(20)
        save_file = os.path.join(rejects_folder,self.filename[:len(self.filename)-4] + ".png")
        figure_data[1].savefig (save_file)
        plt.close(figure_data[1])
            
        plot_data = data_mv[500-self.femb_config.alive_plot_x_back : 500 + self.femb_config.alive_plot_x_forward]
        if (len(peaks_index_fix) >= 2):
            peak = peaks_index_fix[1]
            plot_data = data_mv[peak - self.femb_config.monitor_plot_x_back : peak + self.femb_config.monitor_plot_x_forward]

        data_mv = []
        for i in range(len(data)):
            data_mv.append((data[i] * self.femb_config.bits_to_mv) - baseline)
        
        peaks_index = detect_peaks(x = data_mv, mph = (self.femb_config.monitor_peak_min / 2), mpd=self.femb_config.monitor_freq - 50) 
        peaks_value = []
        peaks_index_fix = []
        for i in peaks_index:
            if (data_mv[i] > self.femb_config.monitor_peak_min):
                peaks_value.append(data_mv[i])
                peaks_index_fix.append(i)
                
        plot_data_corrected = data_mv[500-self.femb_config.alive_plot_x_back : 500 + self.femb_config.alive_plot_x_forward]
        if (len(peaks_index_fix) >= 2):
            peak = peaks_index_fix[1]
            plot_data_corrected = data_mv[peak - self.femb_config.monitor_plot_x_back : peak + self.femb_config.monitor_plot_x_forward]
            
        average = np.mean(peaks_value)
            
        return plot_data, not failure, average, plot_data_corrected
        
#__INIT__#
    def __init__(self):
        self.test_folder = None
        self.filename = None
        self.curr_analysis = None
        self.plot = plot_functions()
        self.femb_config = CONFIG()
        
if __name__ == "__main__":
    single_channels = []
    for i in range (16):
        single_channels.append("/home/ryan/Desktop/Quad_Data_2017_09_26/axestest\ch{}.dat".format(i))
    
    Data_Analysis().PlotSingles(single_channels)
    #Data_Analysis().UnpackData("D:\\nEXO\\2017_06_19\\" + "ped.dat")
    #Data_Analysis().Missing_Packet_Check("D:\\Eric\\Packets\\")
    #Data_Analysis().Seperate_Packets("D:\\Eric\\Packets\\", 4, 4)