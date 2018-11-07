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
import math
import copy
from scipy import stats
import sys
import warnings


####################################################################################################################################################

def linear_fit(chip_id,chn_id, adc_np,vlt_slope): 
    np.set_printoptions(threshold=np.inf)
    units = []

    for i in (range(len(adc_np))):
        units.append( vlt_slope * ( i*(185) ) )

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
            if ( (adc_np[i] - adc_np[0]) > 70 ) and (adc_np[i] > 275):
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
                if (adc_np[i] > (max(adc_np)-100)) or (adc_np[i] > adc_np[i+3]) :
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
        if (math.isnan(slope)):
            slope = 0
    return slope,constant, adc_np, units
