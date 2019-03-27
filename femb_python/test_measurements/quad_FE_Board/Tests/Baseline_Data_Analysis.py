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
    
    #Puts the channel designations where they should be, as long as you know how many discrete sections there are and what the spacing between them is
    def setup_spreadsheet(self, ws, sections, rows, start):
        for i in range(sections):
            ws.cell(row = (rows * i) + start, column = 1).value = "Channel"
            for j in range(16):
                ws.cell(row = j + (rows * i) + start + 1, column = 1).value = "{}".format(j)
            
    def baseline_directory(self, directory, datasubdir, chip_name, chip_index, analysis):
          
        print("Baseline_Data_Analysis -->  Analyzing Baseline data for Chip {}({})...".format(chip_index, chip_name))
        self.data_folder = os.path.join(directory,datasubdir)
        analyses = []
        if "mean" in analysis:
            analyses.append("mean")
        if "std" in analysis:
            analyses.append("std")

        #TODO change here to change which base/peaks are analyzed
        self.gain = self.config["BASELINE_SETTINGS"]["BASELINE_GAIN"]
        self.shape = self.config["BASELINE_SETTINGS"]["BASELINE_PEAK"]
        self.leak = self.config["BASELINE_SETTINGS"]["BASELINE_LEAK"]
        self.buff = self.config["BASELINE_SETTINGS"]["BASELINE_BUFFER"]
            
        overall_result = True
        baselines_200 = []
        baselines_900 = []
        
        fig_summary = plt.figure(figsize=(16,12), dpi=80)
        ax = fig_summary.add_subplot(1,1,1)
        ax.set_xlabel('Channel')
        for item in ([ax.xaxis.label, ax.yaxis.label] + ax.get_xticklabels() + ax.get_yticklabels()):
            item.set_fontsize(20)
        for test in analyses:
            self.test = test
            print ("Baseline_Data_Analysis --> testing {}".format(test))
            for base in ["200mV", "900mV"]:
                self.base = base
                for chn in range(int(self.config["DEFAULT"]["NASICCH_MIN"]), int(self.config["DEFAULT"]["NASICCH_MAX"]) + 1, 1):
                    baseline_file_notation = self.config["FILENAMES"]["BASELINE_NAMING"]
                    self.filename = baseline_file_notation.format(chn,self.gain,self.shape,self.leak,base, self.buff)
                        
                    val, result = self.baseline_file(os.path.join(self.data_folder,self.filename))
                    overall_result = overall_result and result
                    
                    if (val != None):
                        if (base == "200mV"):
                            baselines_200.append(round(val,2))
                        elif (base == "900mV"):
                            baselines_900.append(round(val,2))
                        else:
                            print("Baseline_Data_Analysis --> Incorrect baseline test chosen!  Should be 200mV or 900mV, you have {}".format(base))
                    
                    ax.scatter(chn, val)
                if (self.test == "mean"):
                    ax.set_ylabel('mV')
                    ax.set_title("Baseline Summary for Chip {}".format(chip_name))
                    if (base == "200mV"):
                        y_pos = 0.8
                        self.average_200 = np.mean(baselines_200)
                        comment = "Average 200 mV baseline is {:.2f} mV".format(self.average_200)
                    elif (base == "900mV"):
                        y_pos = 0.9
                        self.average_900 = np.mean(baselines_900)
                        comment = "Average 900 mV baseline is {:.2f} mV".format(self.average_900)
                        
                    ax.text(0.01,y_pos,comment,transform=ax.transAxes, fontsize = 20)
                    chan = range(-1, 17)
                    ax.set_xticks(chan)
                    y_lim = ax.get_ylim()
                    ax.set_ylim(0, 1000 * float(self.config["DEFAULT"]["ADC_REF_VOLTAGE"]))
                    xticks = ax.xaxis.get_major_ticks()
                    xticks[0].set_visible(False)
                    xticks[17].set_visible(False)
                    ax.title.set_fontsize(30)
                
                    ax.axhspan(0, float(self.config["BASELINE_SETTINGS"]["BASELINE_200_GOOD_MIN"]), color=self.config["COLORS"]["RED"], alpha=float(self.config["COLORS"]["ALPHA"]), lw = 0)
                    ax.axhspan(float(self.config["BASELINE_SETTINGS"]["BASELINE_200_GOOD_MIN"]), float(self.config["BASELINE_SETTINGS"]["BASELINE_200_GOOD_MAX"]), 
                                     color=self.config["COLORS"]["GREEN"], alpha=float(self.config["COLORS"]["ALPHA"]), lw = 0)
                                     
                    ax.axhspan(float(self.config["BASELINE_SETTINGS"]["BASELINE_200_GOOD_MAX"]), float(self.config["BASELINE_SETTINGS"]["BASELINE_900_GOOD_MIN"]), 
                                     color=self.config["COLORS"]["RED"], alpha=float(self.config["COLORS"]["ALPHA"]), lw = 0)
                                     
                    ax.axhspan(float(self.config["BASELINE_SETTINGS"]["BASELINE_900_GOOD_MIN"]), float(self.config["BASELINE_SETTINGS"]["BASELINE_900_GOOD_MAX"]), 
                                     color=self.config["COLORS"]["GREEN"], alpha=float(self.config["COLORS"]["ALPHA"]), lw = 0)
                                     
                    ax.axhspan(float(self.config["BASELINE_SETTINGS"]["BASELINE_900_GOOD_MAX"]), 1000 * float(self.config["DEFAULT"]["ADC_REF_VOLTAGE"]), 
                                    color=self.config["COLORS"]["RED"], alpha=float(self.config["COLORS"]["ALPHA"]), lw = 0)
                    base_text = self.config["FILENAMES"]["BASELINE_LINK"]
                    save_file = (os.path.join(directory,base_text.format(chip_name)))
                    
                    comment = "Gain = {}, Peaking Time = {}, Leakage = {}, Buffer= {}".format(self.gain,self.shape,self.leak,self.buff)
                    ax.text(0.01,0.85,comment,transform=ax.transAxes, fontsize = 20)
                elif (self.test == "std"):
                    if (base == "200mV"):
                        comment = "Average noise is {:.2f} electrons".format(np.mean(average))
                    elif (base == "900mV"):
                        comment = "Average noise is {:.2f} electrons".format(np.mean(average))
                        
                    ax.set_ylabel('electrons')
                    ax.set_title("Noise Summary for Chip {}, baseline {}".format(chip_name, base))
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
        
                    ax.axhspan(0, float(self.config["BASELINE_SETTINGS"]["BASELINE_200_REJECT_MIN"]), color='red', alpha=self.femb_config.alpha, lw=0)
                    ax.axhspan(float(self.config["BASELINE_SETTINGS"]["BASELINE_200_REJECT_MIN"]), float(self.config["BASELINE_SETTINGS"]["BASELINE_200_REJECT_MIN"]), color='yellow', alpha=self.femb_config.alpha)
                    ax.axhspan(self.femb_config.noise_good_min, self.femb_config.noise_good_max, color='green', alpha=self.femb_config.alpha, lw = 0)
                    ax.axhspan(self.femb_config.noise_good_max, self.femb_config.noise_reject_max, color='yellow', alpha=self.femb_config.alpha)
                    ax.axhspan(self.femb_config.noise_reject_max, y_lim[1], color='red', alpha=self.femb_config.alpha)
        
                    save_file = (os.path.join(directory,"{}_Noise Summary Plot_{}.png".format(chip_name, base)))
                    fig_summary.savefig (save_file)
                    plt.close(fig_summary)
                    fig_summary = plt.figure(figsize=(16, 12), dpi=80)
                    ax = fig_summary.add_subplot(1,1,1)
                    ax.set_xlabel('Channel')
                    for item in ([ax.xaxis.label, ax.yaxis.label] + ax.get_xticklabels() + ax.get_yticklabels()):
                        item.set_fontsize(20)
                    
                fig_summary.savefig (save_file)
                plt.close(fig_summary)
        
        print ("Baseline_Data_Analysis--> Baseline data analyzed for Chip {}({})".format(chip_index, chip_name))
        return overall_result, self.average_200, self.average_900, baselines_200, baselines_900
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
            ADC_voltage = float(self.config["DEFAULT"]["ADC_REF_VOLTAGE"]) * 1000
            num_bits = int(self.config["DEFAULT"]["ADC_FULL_SCALE"], 16)
            bits_to_mv = ADC_voltage/num_bits
            data_mv.append(data[i] * bits_to_mv)
        
        if (self.test == "mean"):
            mean = np.mean(data_mv)
            value = mean
            response = self.baseline_analysis(value)
            
        elif (self.test == "std"):
            std = np.std(data_mv) / int(self.gain[:self.gain.find("m")]) / (1.6E-19) * (1E-15)
            std_mv = np.std(data_mv)
            value = std
            response = self.noise_analysis(value, mv = std_mv)
            
        if response != True:
            rejects_folder = os.path.join(self.data_folder,"Outside Range")
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
            save_file = (os.path.join(rejects_folder,self.filename[:len(self.filename)-4] + self.test + ".png"))
            figure_data[1].savefig (save_file)
            plt.close(figure_data[1])
                
        return value, response
        
    def baseline_analysis(self, value):
        value = int(value)
        if (self.base == "200mV"):
            if ((value <= float(self.config["BASELINE_SETTINGS"]["BASELINE_200_GOOD_MAX"])) or (value >= float(self.config["BASELINE_SETTINGS"]["BASELINE_200_GOOD_MIN"]))):
                return True
            else:
                return ("Baseline should be between {} and {}, but it was {:.2f} ".format(self.config["BASELINE_SETTINGS"]["BASELINE_200_GOOD_MIN"], 
                        self.config["BASELINE_SETTINGS"]["BASELINE_200_GOOD_MAX"], value))
                
        if (self.base == "900mV"):
            if ((value <= float(self.config["BASELINE_SETTINGS"]["BASELINE_900_GOOD_MAX"])) or (value >= float(self.config["BASELINE_SETTINGS"]["BASELINE_900_GOOD_MIN"]))):
                return True
            else:
                return ("Baseline should be between {} and {}, but it was {:.2f} ".format(self.config["BASELINE_SETTINGS"]["BASELINE_900_GOOD_MIN"], 
                        self.config["BASELINE_SETTINGS"]["BASELINE_900_GOOD_MAX"], value))
            
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
    