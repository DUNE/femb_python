class ADC_ASIC_REG_MAPPING:

####sec_chn_reg only sets a channel register, the other registers remains as before
    def set_adc_chn(self, chip=0, chn=0, d=-1, pcsr=-1, pdsr=-1, slp=-1, tstin=-1):
        print ("\t ADC_ASIC_REG --> set_adc_chn() --")

        tuple_num = 5 * chip + ((15 - chn) // 4)
        #print ("----------------------------------------------------------------")
        #print ("Chip {}, Channel {} will choose tuple {}".format(chip,chn,tuple_num))
        #print ("Settings of d={}, pcsr={},pdsr={},slp={},tstin={}".format(d,pcsr,pdsr,slp,tstin))
        #print ("Original Tuple {} is {}".format(tuple_num, hex(self.REGS[tuple_num])))
        
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
            print ("\tADC_ASIC_REG_MAPPING-->Error: incorrect chip or channel")
                
        #now we have bitmasks assigned for each position, so we can easily isolate the two hex letters we want
        
        find_mask = (0xFF << bitshift)
        
        existing_settings = ((self.REGS[tuple_num] & find_mask) >> bitshift)
    
        #now existing_settings is simply the two hex letters that already exist for this channel before anything has been done
        
        #if the bit is not being changed, we can just keep the existing settings
        if (d != -1):
            d_bit = (((d&0x01)//0x01)<<7)+(((d&0x02)//0x02)<<6)+(((d&0x04)//0x04)<<5)+(((d&0x08)//0x08)<<4)
        else:
            d_bit = (existing_settings & 0xF0)
            
        if (pcsr != -1):
            pcsr_bit = ((pcsr&0x01)<<3)
        else:
            pcsr_bit = (existing_settings & 0x08)
            
        if (pdsr != -1):
            pdsr_bit = ((pdsr&0x01)<<2)
        else:
            pdsr_bit = (existing_settings & 0x04)
            
        if (slp != -1):
            slp_bit = ((slp&0x01)<<1)
        else:
            slp_bit = (existing_settings & 0x02)
            
        if (tstin != -1):
            tstin_bit = ((tstin&0x01)<<0)
        else:
            tstin_bit = (existing_settings & 0x00)
            
            
        chn_reg = d_bit + pcsr_bit + pdsr_bit + slp_bit  + tstin_bit

        or_mask = (chn_reg << bitshift) #holds the 8 bits we care about - tuple 3 => ch12,13,14,15
        
        self.REGS[tuple_num] = self.REGS[tuple_num] & (and_mask)                
        self.REGS[tuple_num] = self.REGS[tuple_num] | (or_mask)        
        
            
        if(0):
            flup10 = self.REGS[tuple_num]
            flup11 = flup10 & (and_mask)
            flup12 = flup11 | (or_mask)
            print( "\n\t\t---- chn {} ----\n".format(chn))
            print( "\t\t MAPPING --> and_mask     = [~]                           /* {} */ ".format(format(and_mask,'#034b')))
            print( "\t\t MAPPING --> find_mask    = [0xFF << bitshift]            /* {} */".format(format(find_mask,'#034b')))
            print( "\t\t MAPPING --> REGS         = [initially random]            /* {} */".format(format(flup10,'#034b')))
            print( "\t\t MAPPING --> existing_set = [REG & find_mask >> bitshift] /* {} */".format(format(existing_settings,'#034b')))
            
            print( "\t\t MAPPING --> d_bit        = [~]                           /* {} */ ".format(format(d_bit,'#034b')))
            print( "\t\t MAPPING --> pcsr_bit     = [~]                           /* {} */ ".format(format(pcsr_bit,'#034b')))
            print( "\t\t MAPPING --> pdsr_bit     = [~]                           /* {} */ ".format(format(pdsr_bit,'#034b')))
            print( "\t\t MAPPING --> slp_bit      = [~]                           /* {} */ ".format(format(slp_bit,'#034b')))
            print( "\t\t MAPPING --> tstin_bit    = [~]                           /* {} */ ".format(format(tstin_bit,'#034b')))
            print( "\t\t MAPPING --> chn_reg      = [d+pcsr+pdsr+slp+tstin]       /* {} */ ".format(format(chn_reg,'#034b')))
            print( "\t\t MAPPING --> or_mask      = [chn_reg << bitshift]         /* {} */ ".format(format(or_mask,'#034b')))
            print( "\t\t MAPPING --> REGS[{}]      = [previous REG & (and_mask)]   /* {} */".format(tuple_num,format(flup11,'#034b')))
            print( "\t\t MAPPING --> REGS[{}]      = [previous REG | (or_mask)]    /* {} */".format(tuple_num,format(flup12,'#034b')))
            print( "\n")

        print ("ASIC_REG_MAPPING --> set_adc_chn {} -> New Tuple {} is /* {} */".format(chn,tuple_num,format(self.REGS[tuple_num],'#034b')))

####sec_chip_global only sets a chip global register, the other registers remains as before
    def set_adc_global(self, chip = 0,  clk = -1, frqc = -1, en_gr = -1, f0 = -1, f1 = -1, f2 = -1, f3 = -1,
                        f4 = -1, f5 = -1, slsb = -1, res4 = 0, res3 = 0, res2 = 0, res1 = 0, res0 = 0):
        
        tuple_num = ((chip + 1) * 5) - 1
        
        #print ("----------------------------------------------------------------")
        #print ("Chip {} global will choose tuple {}".format(chip,tuple_num))
        #print ("Settings of clk={}, frqc={},en_gr={},f0={},f1={},f2={},f3={},f4={},f5={},slsb={}".format(
        #clk,frqc,en_gr,f0,f1,f2,f3,f4,f5,slsb))
        #print ("Original Tuple {} is {}".format(tuple_num, hex(self.REGS[tuple_num])))

        existing_settings = self.REGS[tuple_num]
        
        if (clk != -1):
            clk_bit = ((clk&0x03)<<14)
        else:
            clk_bit = (existing_settings & 0xc000)
            
        if (frqc != -1):
            frqc_bit = ((frqc&0x01)<<13)
        else:
            frqc_bit = (existing_settings & 0x2000)
            
        if (en_gr != -1):
            en_gr_bit = ((en_gr&0x01)<<12)
        else:
            en_gr_bit = (existing_settings & 0x1000)
            
        if (f0 != -1):
            f0_bit = ((f0&0x01)<<11)
        else:
            f0_bit = (existing_settings & 0x0800)
            
        if (f1 != -1):
            f1_bit = ((f1&0x01)<<10)
        else:
            f1_bit = (existing_settings & 0x0400)
            
        if (f2 != -1):
            f2_bit = ((f2&0x01)<<9)
        else:
            f2_bit = (existing_settings & 0x0200)
            
        if (f3 != -1):
            f3_bit = ((f3&0x01)<<8)
        else:
            f3_bit = (existing_settings & 0x0100)
            
        if (f4 != -1):
            f4_bit = ((f4&0x01)<<7)
        else:
            f4_bit = (existing_settings & 0x0080)
            
        if (f5 != -1):
            f5_bit = ((f5&0x01)<<6)
        else:
            f5_bit = (existing_settings & 0x0040)
            
        if (slsb != -1):
            slsb_bit = ((slsb&0x01)<<5)
        else:
            slsb_bit = (existing_settings & 0x0020)
            
        glo_reg = clk_bit + frqc_bit + en_gr_bit + f0_bit + f1_bit + f2_bit + f3_bit + f4_bit + f5_bit + slsb_bit
        
        self.REGS[tuple_num] = glo_reg

        print ("\t ASIC_REG_MAPPING --> set_adc_global() -> New Tuple {} is {}\n".format(tuple_num,format(self.REGS[tuple_num],'#034b')))

####sec_chip sets registers of a whole chip, registers of the other chips remains as before
    def set_adc_chip(self, chip=0,
                 d=0, pcsr=1, pdsr=1, slp=0, tstin=0,
                 clk = 0, frqc = 0, en_gr = 0, f0 = 0, f1 = 0, 
                 f2 = 0, f3 = 0, f4 = 0, f5 = 1, slsb = 0): #set f5 = 1 1/30/18 cp
        for chn in range(16):
            self.set_adc_chn(chip, chn, d, pcsr, pdsr, slp, tstin )

        self.set_adc_global (chip, clk, frqc, en_gr, f0, f1, f2, f3, f4, f5, slsb)

####sec_sbnd_board sets registers of a whole board 
    def set_adc_board(self,  
                 d=0, pcsr=1, pdsr=1, slp=0, tstin=0,
                 clk = 0, frqc = 0, en_gr = 0, f0 = 0, f1 = 0, 
                 f2 = 0, f3 = 0, f4 = 0, f5 = 0, slsb = 0):
        asic = 1
        for chip in range(asic):
            self.set_adc_chip( chip, d, pcsr, pdsr, slp, tstin,
                 clk, frqc, en_gr, f0, f1, f2, f3, f4, f5, slsb)
                 
        

    #__INIT__#
    def __init__(self):
	#declare board specific registers
#        self.REGS =[0x08080808, 0x08080808, 0x08080808, 0x08080808,
#                    0x000000C0,
#                    0x08080808, 0x08080808, 0x08080808, 0x08080808,
#                    0x000000C0,
#                    0x08080808, 0x08080808, 0x08080808, 0x08080808,
#                    0x000000C0,
#                    0x08080808, 0x08080808, 0x08080808, 0x08080808,
#                    0x000000C0,
#                    ]
                    
        self.REGS =[0x08080808, 0x08080808, 0x08080808, 0x08080808,
                    0x000000C0]
