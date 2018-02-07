# -*- coding: utf-8 -*-
"""
File Name: read_mean.py
Author: GSS
Mail: gao.hillhill@gmail.com
Description: 
Created Time: 3/9/2016 7:12:33 PM
Last modified: 10/12/2016 11:16:42 AM
"""

#defaut setting for scientific caculation
#import numpy
#import scipy
#from numpy import *
#import numpy as np
#import scipy as sp
#import pylab as pl

import numpy as np
import statsmodels.api as sm
import matplotlib.pyplot as plt
import math
import copy
from scipy import stats
import sys
import warnings


####################################################################################################################################################
#Takes in the chip and channel for the error messages.  Takes in the y-data and the slope that will turn "DAC steps" into the
#desired unit.  Also takes in a variable that tells it whether to run for electrons (charge injection) or mv (which gives the
#estimated preamplifier voltage output at the time of sampling.  This requires the last parameter, gain.
def linear_fit(chip_id,chn_id, adc_np,vlt_slope,eorv,gain): 
    np.set_printoptions(threshold=np.inf)
    units = []
#if 1, measured in electrons.  If 0, measured in mV
    if (eorv == 1):
        for i in (range(len(adc_np))):
            
#vlt slope tells you how large of a voltage step that DAC number corresponds to.  The result is the injected charge using
#Q=CV, where V is the voltage step, C is the test capacitor (which must be known, here's it's 185 fF), and then it divides
#by q to go from coulombs to electrons
            units.append( vlt_slope * ( (i*(1.85E-13))/(1.60217646E-19) ) )
    elif (eorv == 0):
        for i in (range(len(adc_np))):

#After finding the injected charge in fC, it multiplies by the preamp gain (e.g. 7.8 mV/fC) to give an estimate of what the
#Preamp output must have been in millivolts
            units.append( vlt_slope * i * 1.85E-13 * 1E15 * gain)
            
    
    else:
        sys.exit("Weird error here in linear_fit_m, the eorv condition")

#because math.isnan(None) can't be evaluated

    for i in range(len(adc_np)):
        try:
            if (adc_np[i] == None):
                adc_np[i] = 0
            elif (math.isnan(adc_np[i])):
                adc_np[i] = 0
                
        except TypeError:
            print ("linear_fit_m--> Error with number type")
            print (adc_np)
            print (i)
            print (adc_np[i])
            print (type(adc_np[i]))
            print (adc_np[i] == None)
            print (math.isnan(adc_np[i]))

#Finds where the lowest valid min is for slope analysis . It must be more than 200 ADC counts over the lowest value and over
#800 ADC counts overall

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)

        i = 0
        for i in range(len(adc_np)):
            if ( (adc_np[i] - adc_np[0]) > 200 ) and (adc_np[i] > 800):
                break
        valid_min = i
    
    #Since the first couple of steps are invalid for the internal DAC, this makes sure they aren't chosen
        if (valid_min -2 <  0 ):
            valid_min = 2
    
        valid_max = valid_min + 1
    
    #Finds where the highest valid max is for slope analysis.  It must be within 300 ADC counts of the max and more than the point
    #3 dac steps below it
        i = 0
        for i in range(len(adc_np)-3):
            if i < valid_min :
                continue
            else:
                if (adc_np[i] > (max(adc_np)-300)) or (adc_np[i] > adc_np[i+3]) :
                    break
    
        valid_max  = i - 1
    
        if (valid_min > valid_max):
            print ("Chip {}, Channel {} does NOT have valid points to fit".format(chip_id, chn_id))
            valid_min = valid_max - 1
    
        if ((valid_max - valid_min) <5):
            print ("Chip {}, Channel {} has less than 5 valid points to fit".format(chip_id, chn_id))
    
    #Create new x and y variables that are only in the valid range
        y = copy.deepcopy(adc_np[valid_min:valid_max])
        for i in range(len(y)):
            y[i] = int(y[i])
    
        x = copy.deepcopy(units[valid_min:valid_max])
        for i in range(len(x)):
            x[i] = int(x[i])

#Do a linear analysis(we only want the slope and y-intercept).  The previous method didn't worth (OSE something...?) so I used
#The stats library
    
        try:
            slope, constant, r_value, p_value, std_err = stats.linregress(x,y)
        except:
            slope = 0
            constant=0
    return slope,constant, adc_np, units
