#!/usr/bin/env python33

from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals
from __future__ import absolute_import
from builtins import range
from future import standard_library
standard_library.install_aliases()
from builtins import object
import string

class FE_ASIC_REG_MAPPING(object):

####sec_chn_reg only sets a channel register, the other registers remains as before
    def set_fechn_reg(self, chip=0, chn=0, sts=0, snc=0, sg=0, st=0, sdc=0, sdf=0 ):
        chn_reg = ((sts&0x01)<<7) + ((snc&0x01)<<6) + ((sg&0x03)<<4) +\
                  ((st&0x03)<<2)  + ((sdc&0x01)<<1) + ((sdf&0x01)<<0) 

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
            if ( self.INTDAC == 1 ):
                pos = (3-chip)*144 + ( 15 - chn) * 8
            else:
                pos = (3-chip)*136 + ( 15 - chn) * 8

            regs_bool1_4[pos:pos+8] = chn_reg_bool
        elif ( chip < 8 ):
            if ( self.INTDAC == 1 ):
                pos = (7-chip)*144 + ( 15 - chn) * 8
            else:
                pos = (7-chip)*136 + ( 15 - chn) * 8

            regs_bool5_8[pos:pos+8] = chn_reg_bool
        else:
            print("FE Chip Number exceeds the maximum value")

        length = len(regs_bool1_4)/16

        for i in range(length):
           m = 0
           for j in range(16):
               if ( regs_bool1_4[16*i + j] ): 
                   m = m + (1 << j)
               if ( regs_bool5_8[16*i + j] ): 
                   m = m + ((1 << j)<<16)
           self.REGS[i] = m


####sec_chip_global only sets a chip global register, the other registers remains as before
    def set_fechip_global(self, chip, slk0 = 0, stb = 0, s16=0, slk1=0, swdac=0, dac=0):
        global_reg = ((slk0&0x01)<<0) + ((stb&0x03)<<1) + ((s16&0x01)<<3) + \
                     ((slk1&0x01)<<4) + ((0&0x07)<<5)
        dac_reg = (((dac&0x01)//0x01)<<7)+(((dac&0x02)//0x02)<<6)+\
                  (((dac&0x04)//0x04)<<5)+(((dac&0x08)//0x08)<<4)+\
                  (((dac&0x10)//0x10)<<3)+(((dac&0x20)//0x20)<<2)+\
                  (((swdac&0x03))<<0) 

        global_reg_bool = []
        for j in range(8):
            global_reg_bool.append ( bool( (global_reg>>j)%2 ) )
        for j in range(8):
            global_reg_bool.append ( bool( (dac_reg>>j)%2 ) )

        regs_bool1_4 = []
        for i in self.REGS:
            for j in range(0,16,1):
                regs_bool1_4.append ( bool( (i>>j)%2 ) )

        regs_bool5_8 = []
        for i in self.REGS:
            for j in range(16,32,1):
                regs_bool5_8.append ( bool( (i>>j)%2 ) )

        if (chip < 4):
            if ( self.INTDAC == 1 ):
                pos = (3-chip)*144 + 128
                regs_bool1_4[pos:pos+16] = global_reg_bool
            else:
                pos = (3-chip)*136 + 128
                regs_bool1_4[pos:pos+8] = global_reg_bool[0:8]
        elif ( chip < 8 ):
            if ( self.INTDAC == 1 ):
                pos = (7-chip)*144 + 128
                regs_bool5_8[pos:pos+16] = global_reg_bool
            else:
                pos = (7-chip)*136 + 128
                regs_bool5_8[pos:pos+8] = global_reg_bool[0:8]
        else:
            print("Chip Number exceeds the maximum value")

        length = len(regs_bool1_4)/16

        for i in range(length):
           m = 0
           for j in range(16):
               if ( regs_bool1_4[16*i + j] ): 
                   m = m + (1 << j)
               if ( regs_bool5_8[16*i + j] ): 
                   m = m + ((1 << j)<<16)
           self.REGS[i] = m

####sec_chip sets registers of a whole chip, registers of the other chips remains as before
    def set_fechip(self, chip=0,
                 sts=0, snc=0, sg=0, st=0, sdc=0, sdf=0,
                 slk0=0, stb=0, s16=0, slk1=0, swdac=0, dac=0):
        for chn in range(16):
            self.set_fechn_reg(chip, chn, sts, snc, sg, st, sdc, sdf)     

        self.set_fechip_global (chip, slk0, stb, s16, slk1, swdac, dac)

####sec_sbnd_board sets registers of a whole board 
    def set_fe_sbnd_board(self, sts=0, snc=0, sg=0, st=0, sdc=0, sdf=0, 
                       slk0 = 0, stb = 0, s16=0, slk1=0, swdac=0, dac=0):
        for chip in range(8):
            self.set_fechip( chip, sts, snc, sg, st, sdc, sdf, slk0, stb, s16, slk1, swdac, dac)

    #__INIT__#
    def __init__(self):
	#declare board specific registers
        self.INTDAC = 0
        #self.INTDAC = 1
        if (self.INTDAC == 1 ):
            self.REGS =[ 0x00000000, 0x00000000, 0x00000000, 0x00000000,
                         0x00000000, 0x00000000, 0x00000000, 0x00000000,
                         0x00000000, 0x00000000, 0x00000000, 0x00000000,
                         0x00000000, 0x00000000, 0x00000000, 0x00000000,
                         0x00000000, 0x00000000, 0x00000000, 0x00000000,
                         0x00000000, 0x00000000, 0x00000000, 0x00000000,
                         0x00000000, 0x00000000, 0x00000000, 0x00000000,
                         0x00000000, 0x00000000, 0x00000000, 0x00000000,
                         0x00000000, 0x00000000, 0x00000000, 0x00000000,
                    ]
        else:
            self.REGS =[ 0x00000000, 0x00000000, 0x00000000, 0x00000000,
                         0x00000000, 0x00000000, 0x00000000, 0x00000000,
                         0x00000000, 0x00000000, 0x00000000, 0x00000000,
                         0x00000000, 0x00000000, 0x00000000, 0x00000000,
                         0x00000000, 0x00000000, 0x00000000, 0x00000000,
                         0x00000000, 0x00000000, 0x00000000, 0x00000000,
                         0x00000000, 0x00000000, 0x00000000, 0x00000000,
                         0x00000000, 0x00000000, 0x00000000, 0x00000000,
                         0x00000000, 0x00000000, 
                    ]

#a = FE_ASIC_REG_MAPPING()
#print a.REGS
#a.set_fe_sbnd_board(sts=1, slk0=1 )
##a.set_fe_sbnd_board(dac=0x3f)
##a.set_fechip (chip=4, sts=1, snc=0, sg=0 )
##a.set_fechip_global (chip=0, swdac=1, dac=20)
#for i in a.REGS:
#    print hex(i)
