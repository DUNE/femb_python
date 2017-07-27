#!/usr/bin/env python33

"""
Register mapping for P1 ADC. This is if the register 
interface only wants one at a time, as in the quad ADC 
tester.

5 32-bit registers

Each ASIC channel is 8 bits and ASIC globals are 16 bits
Each ASIC total 144 bits = 16 * 8bits + 16 bits
This is 4.5  32-bit registers

channel data is packed in from 15 to down to 0, with the 
last register half filled with the globals and half empty.
"""

from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals
from __future__ import absolute_import
from builtins import range
from future import standard_library
standard_library.install_aliases()
from builtins import object
import string

class ADC_ASIC_REG_MAPPING(object):

####sec_chn_reg only sets a channel register, the other registers remains as before
    def set_chn_reg(self, chn=0, d=0, pcsr=0, pdsr=0, slp=0, tstin=0 ):

        chn_reg = ((d<<4)&0xF0) + ((pcsr&0x01)<<3) + ((pdsr&0x01)<<2) + \
                  ((slp&0x01)<<1) + ((tstin&0x01)<<0)

        regNum = 3 - chn // 4
        posInReg = 3 - chn % 4
        shift = posInReg*8
        mask = 0xFF << shift
        
        oldReg = self.REGS[regNum]
        newReg = (oldReg & (~mask)) | ((chn_reg << shift) & mask)
        self.REGS[regNum] = newReg

####sec_chip_global only sets a chip global register, the other registers remains as before
    def set_chip_global(self, clk0 = 0, clk1 = 0, frqc = 0, en_gr = 0,
                        f0=0, f1=0, f2=0,f3=0, f4=0, f5=0,
                        slsb=0, res0=0, res1=0, res2=0, res3=0, res4=0):
        #print("globals: clk0: {} clk1: {} frqc: {} en_gr: {} \n     f0: {} f1: {} f2: {} f3: {} f4: {} f5: {} \n     res0: {} res1: {} res2: {} res3: {} res4: {}".format(clk0, clk1, frqc, en_gr, f0, f1, f2, f3, f4,  f5, res0, res1, res2, res3, res4))
        global_reg = [False]*16
        global_reg[0] = (bool(res4)) 
        global_reg[1] = (bool(res3))
        global_reg[2] = (bool(res2)) 
        global_reg[3] = (bool(res1)) 
        global_reg[4] = (bool(res0)) 
        global_reg[5] = (bool(slsb)) 
        global_reg[6] = (bool(f5)) 
        global_reg[7] = (bool(f4)) 
        global_reg[8] = (bool(f3)) 
        global_reg[9] = (bool(f2)) 
        global_reg[10] = (bool(f1)) 
        global_reg[11] = (bool(f0)) 
        global_reg[12] = (bool(en_gr)) 
        global_reg[13] = (bool(frqc)) 
        global_reg[14] = (bool(clk1)) 
        global_reg[15] = (bool(clk0)) 

        reg = 0
        for iBit, bitFlag in enumerate(global_reg):
            if bitFlag:
                reg = reg | (1 << iBit)
        self.REGS[4] = reg

####sec_chip sets registers of a whole chip, registers of the other chips remains as before
    def set_chip(self,
                d=0, pcsr=0, pdsr=0, slp=0, tstin=0,
                clk0 = 0, clk1 = 0, frqc = 0, en_gr = 0,
                f0=0, f1=0, f2=0,f3=0, f4=0, f5=0,
                slsb=0, res0=0, res1=0, res2=0, res3=0, res4=0):
        for chn in range(16):
            self.set_chn_reg(chn, d, pcsr, pdsr, slp, tstin )     

        self.set_chip_global(clk0, clk1, frqc, en_gr,
                        f0, f1, f2,f3, f4, f5,
                        slsb, res0, res1, res2, res3, res4)

    #__INIT__#
    def __init__(self):
        #declare board specific registers
        self.REGS = [0]*5

#a = ADC_ASIC_REG_MAPPING()
#for i in a.REGS:
#    #print("{:#010x}".format(i))
#    print("{:#033b}".format(i))
#print()
#a.set_chip(d=1,f0=1)
#for i in a.REGS:
#    print("{:#033b}".format(i))
#print()
