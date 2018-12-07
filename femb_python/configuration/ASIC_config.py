# -*- coding: utf-8 -*-
"""
Created on Tue Dec  4 17:25:33 2018

@author: eraguzin
"""
class FE_CONFIG(object):
    def __init__(self, chip_num, chn_num):
        self.chip_num = chip_num
        self.chn_num = chn_num
        self.REGS = [0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
                     0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
                     0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,
                     0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000,]
    def set_fe_chn(self, chip, chn, sts=-1, snc=-1, sg=-1, st=-1, smn=-1, sbf=-1):

        #to find which array the channel/chip combination belongs in, then the specific byte of the array for the chip
        tuple_num = ((15 - chn) // 4) + (5 * chip)
        
        if (chn%4 == 3):
            bitshift = 0
            and_mask = 0xFFFFFF00
            
        elif (chn%4 == 2):
            bitshift = 8
            and_mask = 0xFFFF00FF
            
        elif (chn%4 == 1):
            bitshift = 16
            and_mask = 0xFF00FFFF
            
        elif (chn%4 == 0):
            bitshift = 24
            and_mask = 0x00FFFFFF
            
        else:
            print ("FE_ASIC_REG_MAPPING--> Error: incorrect chip or channel")
                
        #now we have bitmasks assigned for each position, so we can easily isolate the two hex letters we want
        
        find_mask = (0xFF << bitshift)
        existing_settings = ((self.REGS[tuple_num] & find_mask) >> bitshift)
        
        #now existing_settings is simply the two hex letters that already exist for this channel before anything has been done
        
        #if the bit is not being changed, we can just keep the existing settings
        if (sts != -1):
            sts_bit = ((sts&0x01)<<7)
        else:
            sts_bit = (existing_settings & 0x80)
            
        if (snc != -1):
            snc_bit = ((snc&0x01)<<6)
        else:
            snc_bit = (existing_settings & 0x40)
            
        if (sg != -1):
            sg_bit = ((sg&0x03)<<4)
        else:
            sg_bit = (existing_settings & 0x30)
            
        if (st != -1):
            st_bit = ((st&0x03)<<2)
        else:
            st_bit = (existing_settings & 0x0c)
            
        if (smn != -1):
            smn_bit = ((smn&0x01)<<1)
        else:
            smn_bit = (existing_settings & 0x02)
            
        if (sbf != -1):
            sbf_bit = ((sbf&0x01)<<0)
        else:
            sbf_bit = (existing_settings & 0x01)
            
        chn_reg = sts_bit + snc_bit + sg_bit + st_bit  + smn_bit + sbf_bit

        or_mask = (chn_reg << bitshift)

        self.REGS[tuple_num] = self.REGS[tuple_num] & (and_mask)
        
        self.REGS[tuple_num] = self.REGS[tuple_num] | (or_mask)

####sec_chip_global only sets a chip global register, the other registers remains as before
    def set_fe_global(self, chip, slk = -1, stb = -1, s16=-1, slkh=-1, sdc=-1, sdacsw2=-1, sdacsw1=-1, sdac=-1):

        tuple_num = (5 * chip) + 4
        existing_settings = self.REGS[tuple_num]
        
        if (sdac != -1):
            sdac_bit = (((sdac&0x01)//0x01)<<15)+(((sdac&0x02)//0x02)<<14)+\
                       (((sdac&0x04)//0x04)<<13)+(((sdac&0x08)//0x08)<<12)+\
                       (((sdac&0x10)//0x10)<<11)+(((sdac&0x20)//0x20)<<10)
        else:
            sdac_bit = (existing_settings & 0xfc00)
            
        if (sdacsw1 != -1):
            sdacsw1_bit = (((sdacsw1&0x01))<<9)
        else:
            sdacsw1_bit = (existing_settings & 0x0200)
            
        if (sdacsw2 != -1):
            sdacsw2_bit = (((sdacsw2&0x01))<<8)
        else:
            sdacsw2_bit = (existing_settings & 0x0100)
            
        if (sdc != -1):
            sdc_bit = (((sdc&0x01))<<5)
        else:
            sdc_bit = (existing_settings & 0x0020)
            
        if (slkh != -1):
            slkh_bit = ((slkh&0x01)<<4)
        else:
            slkh_bit = (existing_settings & 0x0010)
            
        if (s16 != -1):
            s16_bit = ((s16&0x01)<<3)
        else:
            s16_bit = (existing_settings & 0x0008)
            
        if (stb != -1):
            stb_bit = ((stb&0x03)<<1)
        else:
            stb_bit = (existing_settings & 0x0006)
            
        if (slk != -1):
            slk_bit = ((slk&0x01)<<0)
        else:
            slk_bit = (existing_settings & 0x0001)
            
        glo_reg = sdac_bit + sdacsw1_bit + sdacsw2_bit + sdc_bit + slkh_bit + s16_bit + stb_bit + slk_bit

        self.REGS[tuple_num] = glo_reg

####sec_chip sets registers of a whole chip, registers of the other chips remains as before
    def set_fe_chip(self, chip,
                 sts=0, snc=0, sg=0, st=0, smn=0, sbf=0,
                 slk=0, stb=0, s16=0, slkh=0, sdc=0, sdacsw2=0, sdacsw1=0, sdac=0):
        for chn in range(self.chn_num):
            self.set_fe_chn(chip, chn, sts, snc, sg, st, smn, sbf)     

        self.set_fe_global (chip, slk, stb, s16, slkh, sdc, sdacsw2, sdacsw1, sdac)

####sec_sbnd_board sets registers of a whole board 
    def set_fe_board(self, sts=0, snc=0, sg=0, st=0, smn=0, sbf=0, 
                       slk = 0, stb = 0, s16=0, slkh=0, sdc=0, sdacsw2=0, sdacsw1=0, sdac=0):
        for chip in range (self.chip_num):
            self.set_fe_chip(chip, sts, snc, sg, st, smn, sbf, slk, stb, s16, slkh, sdc, sdacsw2, sdacsw1, sdac)
            
        return self.REGS
        