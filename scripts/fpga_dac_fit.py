# -*- coding: utf-8 -*-
"""
File Name: read_mean.py
Author: GSS
Mail: gao.hillhill@gmail.com
Description: 
Created Time: 3/9/2016 7:12:33 PM
Last modified: 10/12/2016 11:19:54 AM
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
import matplotlib.pyplot as plt
import sys

def fpga_dac_fit(path,ideal_flg=1):
    vW = px.load_workbook(path, read_only = True)
    vp = vW.get_sheet_by_name(name = 'Sheet1')
    
    va=[]
    vi = 0
    for row in vp.iter_rows():
        for k in row:
            va.append(float(k.internal_value))
        vi = vi + 1
    
    # convert list a to matrix (for example 16*6)
    vaa= np.resize(va, [vi, 3 ])
    
    cacu = vaa[:,1]
    meas = vaa[:,2]

    delta_cacu = []
    for i in cacu:
        delta_cacu.append(i - cacu[0]) 

    delta_meas = []
    for i in meas:
        delta_meas.append(i - meas[0]) 

    cacu_len = len(delta_cacu)
    cx = np.arange(cacu_len)
    delta_cacu_np = np.array(delta_cacu)
    cresults = sm.OLS(delta_cacu_np,sm.add_constant(cx)).fit()
    cslope = cresults.params[1]
    cconstant = cresults.params[0]
    with open ("voltage_fit.txt","w") as f:
        a = str(cresults.summary())
        f.write(a)        


    plt.scatter(cx, delta_cacu_np,c='r',marker='o')
    cx_plot = np.linspace(0,max(cx))

    plt.ylabel("Voltage / V")
    plt.xlabel("Steps")
    k = len(cx_plot)
    m = max(delta_cacu_np)
    plt.text(0.0,1.0*m,"Y = (%f) * X + (%f)"%(cslope,cconstant) )
    plt.title("Linear fit by Caculation" )
    plt.plot(cx_plot, cx_plot*cslope + cconstant, 'r')
    plt.savefig(".\\cacu_voltage.jpg")
    plt.close()


    meas_len = len(delta_meas)
    mx = np.arange(meas_len)
    delta_meas_np = np.array(delta_meas)
    mresults = sm.OLS(delta_meas_np ,sm.add_constant(mx)).fit()
    mslope = mresults.params[1]
    mconstant = mresults.params[0]
    with open ("fpgadac_fit.txt","w") as f:
        a = str(mresults.summary())
        f.write(a)        

    plt.scatter(mx, delta_meas_np,c='b',marker='*')
    mx_plot = np.linspace(0,max(mx))

    plt.ylabel("Voltage / V")
    plt.xlabel("Steps")
    k = len(mx_plot)
    m = max(delta_meas_np)
    plt.text(0.0,1.0*m,"Y = (%f) * X + (%f)"%(mslope,mconstant) )
    plt.title("Linear fit by Measurement" )
    plt.plot(mx_plot, mx_plot*mslope + mconstant, 'b')
    plt.savefig(".\\meas_voltage.jpg")

    plt.close()


    if(ideal_flg):
        vtmp = delta_cacu
        slope = cslope
    else:
        vtmp = delta_meas
        slope = mslope
    
    vtmp_np = np.array(vtmp)
    return slope


#fpga_dac_fit(path = "./R32_16_8_4_2_1_77iii_stength.xlsx")
