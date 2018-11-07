# -*- coding: utf-8 -*-
"""
Created on Fri Jun  2 11:50:17 2017

@author: vlsilab2
"""

import os
import sys
import struct
from datetime import datetime
import matplotlib.pyplot as plt
plt.switch_backend('agg')
import pickle
import numpy as np
import matplotlib.patches as mpatches
from femb_python.test_measurements.sbnd_femb_test.detect_peaks import detect_peaks
from femb_python.test_measurements.sbnd_femb_test.plotting import plot_functions
import warnings
with warnings.catch_warnings():
    warnings.simplefilter("ignore", category=RuntimeWarning)
    
from femb_python.configuration import CONFIG

class Data_Analysis:
    
    #Puts the channel designations where they should be, as long as you know how many discrete sections there are and what the spacing between them is
    def setup_spreadsheet(self, ws, sections, rows, start):
        for i in range(sections):
            ws.cell(row = (rows * i) + start, column = 1).value = "Channel"
            for j in range(16):
                ws.cell(row = j + (rows * i) + start + 1, column = 1).value = "{}".format(j)
            
    def baseline_directory(self, directory, chip, datasubdir, outlabel, gain, peak, leak, buff, base):
          
        print("Test--> Analyzing Baseline data for Chip {}...".format(chip))
        sys.stdout.flush()    
        self.test_folder = os.path.join(directory,datasubdir)
        data_folder = os.path.join(self.test_folder,"Data")
        #print("data_folder: {}".format(data_folder))       
        data_file_scheme = "Baseline_ch{}_{}_{}_{}_{}_{}.dat"     
        
        self.ws_name = "_mean"
        overall_result = True
        baselines = []
        
        fig_summary = plt.figure(figsize=(16,12), dpi=80)
        ax = fig_summary.add_subplot(1,1,1)
        ax.set_xlabel('Channel')
        for item in ([ax.xaxis.label, ax.yaxis.label] + ax.get_xticklabels() + ax.get_yticklabels()):
            item.set_fontsize(20)
        
        for base in ["200mV", "900mV"]:
            self.base = base
            for chn in range(self.femb_config.channels):
                self.filename = data_file_scheme.format(chn,gain,peak,leak,buff,base)
                    
                val, result = self.baseline_file(os.path.join(data_folder,self.filename))
                overall_result = overall_result and result
                
                if (val != None):
                    baselines.append([chn,val])
                
                ax.scatter(chn, val)
                        
            average = np.mean(baselines)
            if (self.ws_name == "_mean"):
                ax.set_ylabel('mV')
                ax.set_title("Baseline Summary for Chip {}".format(chip))
                if (base == "200mV"):
                    y_pos = 0.8
                    comment = "Average 200 mV baseline is {:.2f} mV".format(average)
                elif (base == "900mV"):
                    y_pos = 0.9
                    comment = "Average 900 mV baseline is {:.2f} mV".format(average)
                    
                ax.text(0.01,y_pos,comment,transform=ax.transAxes, fontsize = 20)
            elif (self.ws_name == "_std"):
                if (base == "200mV"):
                    comment = "Average noise is {:.2f} electrons".format(np.mean(average))
                elif (base == "900mV"):
                    comment = "Average noise is {:.2f} electrons".format(np.mean(average))
                    
                ax.set_ylabel('electrons')
                ax.set_title("Noise Summary for Chip {}, baseline {}".format(chip, base))
                y_pos = 0.01
                ax.text(0.01,y_pos,comment,transform=ax.transAxes, fontsize = 20)
                    
                chan = range(-1, 17)
                ax.set_xticks(chan)
                y_lim = ax.get_ylim()
                ax.set_ylim(1, y_lim[1])
                xticks = ax.xaxis.get_major_ticks()
                xticks[0].set_visible(False)
                xticks[17].set_visible(False)
                ax.title.set_fontsize(30)
    
                ax.axhspan(0, self.femb_config.noise_reject_min, color='red', alpha=self.femb_config.alpha, lw=0)
                ax.axhspan(self.femb_config.noise_reject_min, self.femb_config.noise_good_min, color='yellow', alpha=self.femb_config.alpha)
                ax.axhspan(self.femb_config.noise_good_min, self.femb_config.noise_good_max, color='green', alpha=self.femb_config.alpha, lw = 0)
                ax.axhspan(self.femb_config.noise_good_max, self.femb_config.noise_reject_max, color='yellow', alpha=self.femb_config.alpha)
                ax.axhspan(self.femb_config.noise_reject_max, y_lim[1], color='red', alpha=self.femb_config.alpha)
    
                save_file = (os.path.join(self.test_folder,"{}_Noise Summary Plot_{}.png".format(chip, base)))
                fig_summary.savefig (save_file)
                plt.close(fig_summary)
                fig_summary = plt.figure(figsize=(16, 12), dpi=80)
                ax = fig_summary.add_subplot(1,1,1)
                ax.set_xlabel('Channel')
                for item in ([ax.xaxis.label, ax.yaxis.label] + ax.get_xticklabels() + ax.get_yticklabels()):
                    item.set_fontsize(20)
                
                
                
            if (self.ws_name == "_mean"):
                chan = range(-1, 17)
                ax.set_xticks(chan)
                y_lim = ax.get_ylim()
                ax.set_ylim(0, 1800)
                xticks = ax.xaxis.get_major_ticks()
                xticks[0].set_visible(False)
                xticks[17].set_visible(False)
                ax.title.set_fontsize(30)
            
                ax.axhspan(0, self.femb_config.baseline_200_reject_min, color='red', alpha=self.femb_config.alpha, lw=0)
                ax.axhspan(self.femb_config.baseline_200_reject_min, self.femb_config.baseline_200_good_min, color='yellow', alpha=self.femb_config.alpha)
                ax.axhspan(self.femb_config.baseline_200_good_min, self.femb_config.baseline_200_good_max, color='green', alpha=self.femb_config.alpha, lw = 0)
                
                ax.axhspan(self.femb_config.baseline_200_good_max, self.femb_config.baseline_200_reject_max, color='yellow', alpha=self.femb_config.alpha)
                ax.axhspan(self.femb_config.baseline_200_reject_max, self.femb_config.baseline_900_reject_min, color='red', alpha=self.femb_config.alpha)
                ax.axhspan(self.femb_config.baseline_900_reject_min, self.femb_config.baseline_900_good_min, color='yellow', alpha=self.femb_config.alpha)
                
                ax.axhspan(self.femb_config.baseline_900_good_min, self.femb_config.baseline_900_good_max, color='green', alpha=self.femb_config.alpha)
                ax.axhspan(self.femb_config.baseline_900_good_max, self.femb_config.baseline_900_reject_max, color='yellow', alpha=self.femb_config.alpha)
                ax.axhspan(self.femb_config.baseline_900_reject_max, 1800, color='red', alpha=self.femb_config.alpha)
                save_file = (os.path.join(self.test_folder,"{}_Baseline Summary Plot.png".format(chip)))
                
                comment = "Gain = {}, Peaking Time = {}, Leakage = {}, Buffer= {}".format(gain,peak,leak,buff)
                ax.text(0.01,0.85,comment,transform=ax.transAxes, fontsize = 20)
    #                black_patch = mpatches.Patch(color='black', label='Buffer Off')
    #                blue_patch = mpatches.Patch(color='red', label='Buffer On')
    #                plt.legend(handles=[black_patch, blue_patch])
            
            fig_summary.savefig (save_file)
            plt.close(fig_summary)
        
        print ("Test--> Baseline data analyzed for Chip {}".format(chip))
        return overall_result, average, baselines
#        os.startfile(test_folder + "Baseline_Data.xlsx".format(base))
        
    def baseline_file(self, filepath):
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
            data_mv.append(data[i] * self.femb_config.bits_to_mv)
        
        if (self.ws_name == "_mean"):
            mean = np.mean(data_mv)
            value = mean
            response = self.baseline_analysis(value)
            
        elif (self.ws_name == "_std"):
            std = np.std(data_mv) / float(self.gain[:self.gain.find("m")]) / (1.6E-19) * (1E-15)
            std_mv = np.std(data_mv)
            value = std
            response = self.noise_analysis(value, mv = std_mv)
            
        if response != True:
            rejects_folder = os.path.join(self.test_folder,"Outside Range")
            if (os.path.exists(rejects_folder) == False):
                os.makedirs(rejects_folder)

            figure_data = self.plot.quickPlot(data_mv)
            ax = figure_data[0]
            ax.set_ylabel('mV')
            ax.set_title(self.filename)
            ax.title.set_fontsize(30)
            ax.text(0.01,0.95,response,transform=ax.transAxes, fontsize = 20)
            response = False
            for item in ([ax.xaxis.label, ax.yaxis.label] +ax.get_xticklabels() + ax.get_yticklabels()):
                item.set_fontsize(20)
            save_file = (os.path.join(rejects_folder,self.filename[:len(self.filename)-4] + self.ws_name + ".png"))
            figure_data[1].savefig (save_file)
            plt.close(figure_data[1])
                
        return value, response
        
    def baseline_analysis(self, value):
        value = int(value)
        if (self.base == "200mV"):
            if ((value >= self.femb_config.baseline_200_reject_max) or (value <= self.femb_config.baseline_200_reject_min)):
                return ("Baseline should be between {} and {}, but it was {:.2f} ".format(self.femb_config.baseline_200_reject_min, 
                        self.femb_config.baseline_200_reject_max, value))
            if ((value >= self.femb_config.baseline_200_acceptable_max) or (value <= self.femb_config.baseline_200_acceptable_min)):
                return ("Baseline should be between {} and {}, but it was {:.2f} ".format(self.femb_config.baseline_200_acceptable_min, 
                        self.femb_config.baseline_200_acceptable_max, value))
            if ((value <= self.femb_config.baseline_200_good_max) or (value >= self.femb_config.baseline_200_good_min)):
                return True
#            return True
                
        if (self.base == "900mV"):
            if ((value >= self.femb_config.baseline_900_reject_max) or (value <= self.femb_config.baseline_900_reject_min)):
                return ("Baseline should be between {} and {}, but it was {:.2f} ".format(self.femb_config.baseline_900_reject_min, 
                        self.femb_config.baseline_900_reject_max, value))
            if ((value >= self.femb_config.baseline_900_acceptable_max) or (value <= self.femb_config.baseline_900_acceptable_min)):
                return ("Baseline should be between {} and {}, but it was {:.2f} ".format(self.femb_config.baseline_900_acceptable_min, 
                        self.femb_config.baseline_900_acceptable_max, value))
            if ((value <= self.femb_config.baseline_900_good_max) or (value >= self.femb_config.baseline_900_good_min)):
                 return True
#            return True
            
#    def noise_analysis(self, value, mv):
#        #We only care about 14 mv or 25 mv case case
#        if ((self.gain == "14mV") or (self.gain == "25mV")):
#            if ((value >= self.noise_reject_max) or (value <= self.noise_reject_min)):
#                return ("Noise should be between {} and {}, but it was {:.2f} electrons ({:.2f} mV)".format(self.noise_reject_min, 
#                        self.noise_reject_max, value, mv))
#            if ((value >= self.noise_acceptable_max) or (value <= self.noise_acceptable_min)):
#                return ("Noise should be between {} and {}, but it was {:.2f} electrons ({:.2f} mV)".format(self.noise_acceptable_min, 
#                        self.noise_acceptable_max, value, mv))
#            if ((value <= self.noise_good_max) or (value >= self.noise_good_min)):
##                return True
#            
#        return True
    def alive_directory(self, directory, chip, datasubdir, tests, leaks):
        print("Test--> Analyzing 'Channel Alive' data for Chip {}...".format(chip))
        sys.stdout.flush()
        
        self.test_folder = os.path.join(directory,datasubdir)
        data_folder = os.path.join(self.test_folder,"Data")

        data_file_scheme = self.femb_config.Alive_Naming
        
        fig_summary = plt.figure(figsize=(16, 12), dpi=80)
        ax = fig_summary.add_subplot(1,1,1)
        ax.set_xlabel('Time (us)')
        for item in ([ax.xaxis.label, ax.yaxis.label] + ax.get_xticklabels() + ax.get_yticklabels()):
            item.set_fontsize(20)
            
        overall_result = True
        
        for i, test in enumerate(tests):
            for j, leak in enumerate([leaks]):
                 for chn in range(self.femb_config.channels):
                    self.filename = data_file_scheme.format(chn,leak,test)
                    sample_pulse, result = self.alive_file(os.path.join(data_folder,self.filename))
                    overall_result = overall_result and result
                    if (test == "test_off"):
                        plot_color = "green"
                    elif (test == "test_ext"):
                        plot_color = "red"
                    ax.plot(sample_pulse, color = plot_color)
        data_file_scheme = self.femb_config.Alive_Naming2
        for cycle in range(self.femb_config.power_cycles):
            self.filename = data_file_scheme.format(1,leak,test,cycle)
            sample_pulse, result = self.alive_file(os.path.join(data_folder,self.filename))
            overall_result = overall_result and result
            plot_color = "blue"
            ax.plot(sample_pulse, color = plot_color)
                    
        green_patch = mpatches.Patch(color='green', label='Input pin to FE')
        red_patch = mpatches.Patch(color='red', label='Test pin to FE')
        blue_patch = mpatches.Patch(color='blue', label='Pulses after power cycles')
        plt.legend(handles=[green_patch, red_patch, blue_patch])
                    
        ax.set_ylabel('mV')
        ax.set_title("Sample pulses for Chip {} Channel Alive Test".format(chip))
        ax.title.set_fontsize(30)
        save_file = os.path.join(self.test_folder,"Sample_Pulses.png")
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
            data_mv.append(data[i] * self.femb_config.bits_to_mv)
        
        failure = False
        peaks_index = detect_peaks(x = data_mv, mph = (self.femb_config.test_peak_min / 4), mpd=self.femb_config.test_TP_Period - 50) 
        peaks_value = []
        peaks_index_fix = []
        maximum = max(data_mv)
        for i in peaks_index :
            if (data_mv[i] > self.femb_config.test_peak_min) and (data_mv[i] > (maximum - self.femb_config.under_max)):
                peaks_value.append(data_mv[i])
                peaks_index_fix.append(i)
                
#        print ("Chip {}, Channel {} has peak values {}".format(chip, chn, peaks_value))
        #Check if the peak is in the wrong place (happens when it's not synced)
        response = "Good response, channel is alive"
        
        peak_num = len(peaks_index_fix)
        if ((peak_num <= self.femb_config.test_peaks_min) or (peak_num >= self.femb_config.test_peaks_max)):
            failure = "num"
            response = "Number of peaks should be between {} and {}, but it was {:.0f}.  Wanted peaks between {} and {}".format(self.femb_config.test_peaks_min,self.femb_config.test_peaks_max, peak_num, self.femb_config.test_peak_min, maximum - self.femb_config.under_max)

#        if (failure != False):
        rejects_folder = os.path.join(self.test_folder,"Plots")
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
        x_lim = ax.get_xlim()
        ax.set_xlim(0, x_lim[1])
        ax.text(0.01,0.95,response,transform=ax.transAxes, fontsize = 20)
        for item in ([ax.xaxis.label, ax.yaxis.label] +ax.get_xticklabels() + ax.get_yticklabels()):
            item.set_fontsize(20)
        save_file = os.path.join(rejects_folder,self.filename[:len(self.filename)-4] + ".png")
        figure_data[1].savefig (save_file)
        plt.close(figure_data[1])
                            
        plot_data = data_mv[500-self.femb_config.alive_plot_x_back : 500 + self.femb_config.alive_plot_x_forward]
        if (len(peaks_index_fix) >= 3):
            peak = peaks_index_fix[1]
            plot_data = data_mv[peak - self.femb_config.alive_plot_x_back : peak + self.femb_config.alive_plot_x_forward]
            
        return plot_data, not failure

#__INIT__#
    def __init__(self):       
        self.test_folder = None
        self.filename = None
        self.curr_analysis = None
        self.plot = plot_functions()
        self.femb_config = CONFIG()
        
#if __name__ == "__main__":
#    single_channels = []
#    for i in range (16):
#        single_channels.append("D:\Eric\Quad_Data_2017_09_26\\axestest\ch{}.dat".format(i))
#    
#    Data_Analysis().PlotSingles(single_channels)
    #Data_Analysis().UnpackData("D:\\nEXO\\2017_06_19\\" + "ped.dat")
    #Data_Analysis().Missing_Packet_Check("D:\\Eric\\Packets\\")
    #Data_Analysis().Seperate_Packets("D:\\Eric\\Packets\\", 4, 4)
