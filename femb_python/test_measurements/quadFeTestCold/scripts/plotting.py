# -*- coding: utf-8 -*-
"""
Created on Tue Jan 30 16:43:58 2018

@author: protoDUNE
"""

import os
import sys
import struct
from datetime import datetime
import matplotlib.pyplot as plt
plt.switch_backend('agg')
import pickle
import numpy as np
from femb_python.test_measurements.quadFeTestCold.user_settings import user_editable_settings
from openpyxl import Workbook
from openpyxl.styles import Border, Alignment, Font, Side, PatternFill
import matplotlib.patches as mpatches
from femb_python.test_measurements.quadFeTestCold.scripts.detect_peaks import detect_peaks
settings = user_editable_settings()

class plot_functions:

    def plot(self, data, plot_name, title_name):
        chip_num = data[0]

        time_x = []
        length = len(data[1])            
        
        for j in range(length):
            time_x.append(0.5 * j)

        fig = plt.figure(figsize=(16, 12), dpi=80)
        plt.title(title_name, fontsize = 20)
        overlay_ax = plt.gca()
        overlay_ax.spines['top'].set_color('none')
        overlay_ax.spines['bottom'].set_color('none')
        overlay_ax.spines['left'].set_color('none')
        overlay_ax.spines['right'].set_color('none')
        overlay_ax.tick_params(labelcolor='w', top='off', bottom='off', left='off', right='off')
        overlay_ax.set_xlabel('Time (us)')
        overlay_ax.set_ylabel('ADC Counts')
        overlay_ax.yaxis.set_label_coords(-0.035,0.5)
        ax1 = fig.add_subplot(16,1,16)
        
        plt.plot(time_x, data[1])
#        plt.setp(ax1.get_xticklabels(), fontsize=12)
        ax1.set_title("Channel 0")
        ax2 = ax1.twinx()
        ax2.set_ylabel("Channel 0", rotation = 0)
        ax2.spines['top'].set_color('none')
        ax2.spines['bottom'].set_color('none')
        ax2.spines['left'].set_color('none')
        ax2.spines['right'].set_color('none')
        ax2.tick_params(labelcolor='w', top='off', bottom='off', left='off', right='off')
        for j in range(15):
            time_x = []
            length = len(data[j+2])            
            
            for k in range(length):
                time_x.append(0.5 * k)
            ax = fig.add_subplot(16,1,15-j, sharex=ax1)
            plt.plot(time_x, data[j+2])
            for item in (ax.get_xticklabels()):
                item.set_fontsize(20)
            plt.setp(ax.get_xticklabels(), visible=False)
            
            ax2 = ax.twinx()
            ax2.set_ylabel("Channel " + str(j+1), rotation = 0)
#               ax2.spines['top'].set_color('none')
#               ax2.spines['bottom'].set_color('none')
#               ax2.spines['left'].set_color('none')
#               ax2.spines['right'].set_color('none')
            ax2.tick_params(labelcolor='w', top='off', bottom='off', left='off', right='off')
            pos1 = ax2.get_position() # get the original position 
            pos2 = [pos1.x0 + 0.025, pos1.y0 + 0.005,  pos1.width , pos1.height ] 
            ax2.set_position(pos2) # set a new position
            

        plt.subplots_adjust(wspace=0, hspace=0, top = 0.95, bottom = 0.05, right = 0.95, left = 0.05)
        
        plt.savefig (plot_name)  
        plt.close(fig)
        print("Plot--> Data Saved as " + plot_name + "_{}".format(chip_num))
        
    def quickPlot(self, data):
        
        time = []
        for i in range(len(data)):
            time.append(0.5 * i)
            
            
        fig = plt.figure(figsize=(16, 12), dpi=80)
        overlay_ax = fig.add_subplot(1,1,1)

        overlay_ax.set_xlabel('Time (us)')
        overlay_ax.set_ylabel('ADC Counts')
        overlay_ax.plot(time, data)
                
        #plt.show()
        
        return [overlay_ax, fig]
