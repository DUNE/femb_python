#!/usr/bin/env python33

"""
Register mapping for P1 ADC
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
    def set_chn_reg(self, chip=0, chn=0, d=0, pcsr=1, pdsr=1, slp=0, tstin=0 ):
        chn_reg = ((d<<4)&0xF0) + ((pcsr&0x01)<<3) + ((pdsr&0x01)<<2) + \
                  ((slp&0x01)<<1) + ((tstin&0x01)<<0)

        chn_reg_bool = []
        for j in range(8):
            chn_reg_bool.append ( bool( (chn_reg>>j)%2 ) )

        regs_bool1_4 = []
        for i in self.REGS:
            for j in range(0,16,1):
                regs_bool1_4.append ( bool( (i>>j)%2 ) )

        regs_bool5_8 = []
        for i in self.REGS:
            for j in range(16,32,1):
                regs_bool5_8.append ( bool( (i>>j)%2 ) )

        if (chip < 4):
            pos = (3-chip)*144 + ( 15 - chn) * 8
            regs_bool1_4[pos:pos+8] = chn_reg_bool
        elif ( chip < 8 ):
            pos = (7-chip)*144 + ( 15 - chn) * 8
            regs_bool5_8[pos:pos+8] = chn_reg_bool
        else:
            print("Chip Number exceeds the maximum value")

        length = len(regs_bool1_4)//16

        for i in range(length):
           m = 0
           for j in range(16):
               if ( regs_bool1_4[16*i + j] ): 
                   m = m + (1 << j)
               if ( regs_bool5_8[16*i + j] ): 
                   m = m + ((1 << j)<<16)
           self.REGS[i] = m


####sec_chip_global only sets a chip global register, the other registers remains as before
    def set_chip_global(self, chip, clk0 = 0, clk1 = 0, frqc = 0, en_gr = 0,
                        f0=0, f1=0, f2=0,f3=0, f4=0, f5=0,
                        slsb=0, res0=0, res1=0, res2=0, res3=0, res4=0):
        print("globals: clk0: {} clk1: {} frqc: {} en_gr: {} \n     f0: {} f1: {} f2: {} f3: {} f4: {} f5: {} \n     res0: {} res1: {} res2: {} res3: {} res4: {}".format(clk0, clk1, frqc, en_gr, f0, f1, f2, f3, f4,  f5, res0, res1, res2, res3, res4))
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

        regs_bool1_4 = []
        for i in self.REGS:
            for j in range(0,16,1):
                regs_bool1_4.append ( bool( (i>>j)%2 ) )

        regs_bool5_8 = []
        for i in self.REGS:
            for j in range(16,32,1):
                regs_bool5_8.append ( bool( (i>>j)%2 ) )

        if (chip < 4):
            pos = (3-chip)*144 + 128
            regs_bool1_4[pos:pos+16] = global_reg
        elif ( chip < 8 ):
            pos = (7-chip)*144 + 128
            regs_bool5_8[pos:pos+16] = global_reg
        else:
            print("Chip Number exceeds the maximum value")

        length = len(regs_bool1_4)//16

        for i in range(length):
           m = 0
           for j in range(16):
               if ( regs_bool1_4[16*i + j] ): 
                   m = m + (1 << j)
               if ( regs_bool5_8[16*i + j] ): 
                   m = m + ((1 << j)<<16)
           self.REGS[i] = m

####sec_chip sets registers of a whole chip, registers of the other chips remains as before
    def set_chip(self, chip=0,
                d=0, pcsr=1, pdsr=1, slp=0, tstin=0,
                clk0 = 0, clk1 = 0, frqc = 0, en_gr = 0,
                f0=0, f1=0, f2=0,f3=0, f4=0, f5=0,
                slsb=0, res0=0, res1=0, res2=0, res3=0, res4=0):
        for chn in range(16):
            self.set_chn_reg(chip, chn, d, pcsr, pdsr, slp, tstin )     

        self.set_chip_global(chip, clk0, clk1, frqc, en_gr,
                        f0, f1, f2,f3, f4, f5,
                        slsb, res0, res1, res2, res3, res4)

####sec_sbnd_board sets registers of a whole board 
    def set_sbnd_board(self,  
                d=0, pcsr=1, pdsr=1, slp=0, tstin=0,
                clk0 = 0, clk1 = 0, frqc = 0, en_gr = 0,
                f0=0, f1=0, f2=0,f3=0, f4=0, f5=0,
                slsb=0, res0=0, res1=0, res2=0, res3=0, res4=0):
        for chip in range(8):
                self.set_chip_global(chip, clk0, clk1, frqc, en_gr,
                                f0, f1, f2,f3, f4, f5,
                                slsb, res0, res1, res2, res3, res4)

    #__INIT__#
    def __init__(self):
        #declare board specific registers
        self.REGS = [0]*36

#a = ADC_ASIC_REG_MAPPING()
#print a.REGS
#a.set_sbnd_board(pcsr=0,pdsr=0, frqc=0)
#for i in a.REGS:
#    print hex(i)
