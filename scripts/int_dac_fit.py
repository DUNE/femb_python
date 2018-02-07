# -*- coding: utf-8 -*-
"""
File Name: read_mean.py
Author: GSS
Mail: gao.hillhill@gmail.com
Description: 
Created Time: 3/9/2016 7:12:33 PM
Last modified: 9/8/2016 5:30:46 PM
"""

#defaut setting for scientific caculation
#import numpy
#import scipy
#from numpy import *
#import numpy as np
#import scipy as sp
#import pylab as pl

import openpyxl as px
import numpy as np
import statsmodels.api as sm
#import matplotlib.pyplot as plt

def int_dac_fit(env=0):
    a = []
    for i in range(65):
        a.append(i-1)
    dacbins = np.array(a)

    if ( env == 0 ): #RT
        amp = np.array( [0.005, 0.025,0.025,0.025,0.041,0.059,0.078,0.096,0.115,
                         0.133,0.152,0.171,0.189,0.208,0.227,0.245,0.264,
                         0.282,0.301,0.319,0.338,0.356,0.375,0.394,0.412,
                         0.431,0.450,0.468,0.487,0.505,0.524,0.542,0.561,
                         0.579,0.598,0.616,0.635,0.653,0.672,0.691,0.709,
                         0.728,0.746,0.765,0.784,0.802,0.821,0.840,0.858,
                         0.877,0.896,0.914,0.933,0.951,0.970,0.988,1.007,
                         1.026,1.044,1.062,1.081,1.100,1.118,1.137,1.155
                        ] )
    else: #LN2
        amp = np.array( [ 0.001,0.015 ,0.019 ,0.029 ,0.047 ,0.063 ,0.081 ,0.099 ,0.116 ,
                          0.134,0.152 ,0.170 ,0.188 ,0.206 ,0.224 ,0.241 ,0.259 ,
                          0.277,0.295 ,0.312 ,0.330 ,0.348 ,0.366 ,0.384 ,0.402 ,
                          0.420,0.438 ,0.456 ,0.474 ,0.492 ,0.509 ,0.527 ,0.545 ,
                          0.562,0.580 ,0.598 ,0.615 ,0.633 ,0.652 ,0.669 ,0.687 ,
                          0.705,0.723 ,0.741 ,0.759 ,0.777 ,0.795 ,0.813 ,0.830 ,
                          0.848,0.866 ,0.883 ,0.901 ,0.917 ,0.934 ,0.951 ,0.969 ,
                          0.989,1.009 ,1.029 ,1.048 ,1.065 ,1.083 ,1.101 ,1.119
                        ] )
   
    cresults = sm.OLS(amp[3:65],sm.add_constant(dacbins[3:65])).fit()
    cslope = cresults.params[1]
    cconstant = cresults.params[0]
#    if ( env == 0 ):
#        with open ("./rt_dac_fit.txt","w") as f:
#            a = str(cresults.summary())
#            f.write(a)        
#    else:
#        with open ("./ln2_dac_fit.txt","w") as f:
#            a = str(cresults.summary())
#            f.write(a)        

    return cslope

#int_dac_fit(1)



