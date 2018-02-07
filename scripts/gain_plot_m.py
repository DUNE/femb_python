# -*- coding: utf-8 -*-
"""
File Name: read_mean.py
Author: GSS
Mail: gao.hillhill@gmail.com
Description: 
Created Time: 3/9/2016 7:12:33 PM
Last modified: 9/4/2016 2:20:10 PM
"""

#defaut setting for scientific caculation
#import numpy
#import scipy
#from numpy import *
import numpy as np
#import scipy as sp
#import pylab as pl
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

def gain_plot(slope_np, sheetname, env, DACused, tp_set, gain_set, save_path):
   
    ylim_value = 1000 
    plt.figure(figsize=(10,6)) 
    chips = 8
    for i in range(chips):
#    for i in [3,5,7]:
        slope_chip_np = slope_np[i,:]
        channel_id_np = np.arange(16*i,16*(i+1),1)
        plt.scatter(channel_id_np, slope_chip_np, color = 'b')
        plt.plot(channel_id_np, slope_chip_np, color = 'b')
        plt.text(16*i+2,ylim_value*0.7,"ASIC%d"%(i+1))
        plt.vlines(16*i,0, ylim_value*0.75, color = 'b')
        
    red_patch = mpatches.Patch(color='b', label=env + "  " + DACused)
    plt.legend(handles=[red_patch])
    plt.text(48,ylim_value*0.85,"Mean=%d"%(slope_np[0:3].mean()))
    plt.text(48,ylim_value*0.80,"std=%d"%( slope_np[0:3].std() ))
#    plt.text(80,ylim_value*0.85,"Mean=%d"%(slope_np[5].mean()))
#    plt.text(80,ylim_value*0.80,"std=%d"%( slope_np[5].std() ))
    plt.text(112,ylim_value*0.85,"Mean=%d"%(slope_np[4:7].mean()))
    plt.text(112,ylim_value*0.80,"std=%d"%( slope_np[4:7].std() ))

    plt.ylabel("Gain /  (e-)/(ADC bin)")
    plt.xlabel("Channel")
    plt.ylim([0,ylim_value*1.0])
    plt.xlim([0,128])
    plt.text(15, ylim_value*0.9, "Peaking time = " + tp_set)
    plt.text(15, ylim_value*0.85, "Gain = " + gain_set )
    plt.title("Gain distribution" )
   
    plt.savefig(save_path+ "\\" + sheetname +"_gain.jpg")
    plt.close()

    slope_all_np = []
    for i in range(chips):
#    for i in [3,5,7]:
#    for i in range(4,8,1):
        if (i == 0) :
            slope_all_np = slope_np[i,:]
        else:
            slope_all_np =np.append(slope_all_np, slope_np[i,:])
    plt.hist(slope_all_np)
    plt.title("Gain Histrogram" )
    plt.xlabel("Gain / (e-/ADCbin)")
    plt.ylabel("channel counts")
    plt.savefig(save_path+ "\\" + sheetname +"_gainhist.jpg")
    plt.close()


