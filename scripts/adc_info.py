# -*- coding: utf-8 -*-
"""
Created on Tue May 16 14:55:49 2017

@author: vlsilab2
"""

from tabulate import tabulate

class ADC_INFO:
        
    def adc_chip_status(self,chip=0,status="sent"):
        
        if (status == "sent"):
            adc_regs = self.adc_regs_sent
            if (adc_regs == None):
                print ("No registers have been written to the board yet")
        elif (status == "to send"):
            adc_regs = self.adc_regs_sw
        else:
            print ("Incorrect status, do you want to see the registers that are 'to send'?  Or the ones 'sent'?")
            return
        
        
        headers = ["Channel", "Off Curr", "Steer Curr", "Int Steer Curr", "Status", "Test Input", ]
        registers=[["0"],["1"],["2"],["3"],["4"],["5"],["6"],["7"],["8"],["9"],["10"],["11"],["12"],["13"],["14"],["15"],]
                   
        for chn in range(16):
            spot = (18*(chip%4) + (chn + 2))
            tuple_num = 35 - (spot // 2)
            if (spot%2 == 0):
                if (chip < 4):
                    bitshift = 8
                else:
                    bitshift = 24
            else:
                if (chip < 4):
                    bitshift = 0
                else:
                    bitshift = 16
        #now we have bitmasks assigned for each position, so we can easily isolate the two hex letters we want
            find_mask = (0xFF << bitshift)
            existing_settings = ((adc_regs[tuple_num] & find_mask) >> bitshift)
            
            d_setting = (existing_settings & 0xf0)
            d_digit1 = (d_setting & 0x80) >> 7
            d_digit2 = (d_setting & 0x40) >> 5
            d_digit3 = (d_setting & 0x20) >> 3
            d_digit4 = (d_setting & 0x10) >> 1
            d_setting = d_digit1 + d_digit2 + d_digit3 + d_digit4

            registers[chn].append(str(d_setting))
            
            if ((existing_settings & 0x08)>>3 == 1):
                registers[chn].append("External")
            else:
                registers[chn].append("Internal")
    
            if ((existing_settings & 0x04)>>2 == 1):
                registers[chn].append("Disabled")
            else:
                registers[chn].append("Enabled")
                
            if ((existing_settings & 0x02)>>1 == 1):
                registers[chn].append("Sleeping")
            else:
                registers[chn].append("Awake")
                
            if ((existing_settings & 0x01) == 1):
                registers[chn].append("On")
            else:
                registers[chn].append("Off")
                
        print ("Channel Registers for ADC chip " + str(chip) + " are:")
        print (tabulate(registers,headers,tablefmt="grid"))
        print ("\n")
        
        headers = ["Clocks", "Freq", "Off Curr", "IDL", "F1", "Sig Gen", "F3", "Test", "Test", "Curr" ]
        registers=[[]]

        tuple_num = (9*(4 - (chip % 4))) -1
        
        if (chip < 4):
            bitshift = 0
        else:
            bitshift = 16
                
        find_mask = (0xFFFF << bitshift)
        existing_settings = ((adc_regs[tuple_num] & find_mask) >> bitshift)

        if ((existing_settings & 0xc000)>>14 == 1):
            registers[0].append("Ext")
        elif ((existing_settings & 0xc000)>>14 == 2):
            registers[0].append("Mono")
        else:
            registers[0].append("Int")
        
        if ((existing_settings & 0x2000)>>13 == 1):
            registers[0].append("1 MHz")
        else:
            registers[0].append("2 MHz")
    
        if ((existing_settings & 0x1000)>>12 == 1):
            registers[0].append("En")
        else:
            registers[0].append("Dis")
             
        if ((existing_settings & 0x0800)>>11 == 0):
           registers[0].append("Int")
        else:
            registers[0].append("Ext")
           
        if ((existing_settings & 0x0400)>>10 == 0):
           registers[0].append("N/A")
        else:
            registers[0].append("N/A")
            
        if ((existing_settings & 0x0200)>>9 == 0):
           registers[0].append("On")
        else:
            registers[0].append("Off")
            
        if ((existing_settings & 0x0100)>>8 == 0):
           registers[0].append("Def")
        else:
            registers[0].append("1 CLK")
            
        if ((existing_settings & 0x0080)>>7 == 0):
           registers[0].append("Int")
        else:
            registers[0].append("Ext")
            
        if ((existing_settings & 0x0040)>>6 == 0):
           registers[0].append("Off")
        else:
            registers[0].append("On")
            
        if ((existing_settings & 0x0020)>>5 == 0):
           registers[0].append("Full")
        else:
            registers[0].append("Partial")

        print ("Global Registers for ADC chip " + str(chip) + " are:")
        print (tabulate(registers,headers,tablefmt="grid"))
        print ("\n")
        
    def adc_channel(self,chip=0,chn=0,d=-1,pcsr=-1,pdsr=-1,slp=-1,tstin=-1,show = "FALSE"):
        self.adc_reg.set_adc_chn(chip,chn,d,pcsr,pdsr,slp,tstin,show)
        self.adc_chip_status(chip)
        
    def adc_global(self,chip=0,clk=-1,frqc=-1,en_gr=-1,f0=-1,f1=-1,f2=-1,f3=-1,f4=-1,f5=-1,slsb=-1,show="FALSE"):
        self.adc_reg.set_adc_global(chip,clk,frqc,en_gr,f0,f1,f2,f3,f4,f5,slsb,show)
        self.adc_chip_status(chip)
        
    def adc_chip(self,chip=0,d=0,pcsr=1,pdsr=1,slp=0,tstin=0,clk=0,frqc=0,en_gr=0,f0=0,f1=0,f2=0,f3=0,f4=0,f5=0,slsb=0,show="FALSE"):
        self.adc_reg.set_adc_chip(chip,d,pcsr,pdsr,slp,tstin,clk,frqc,en_gr,f0,f1,f2,f3,f4,f5,slsb,show)
        self.adc_chip_status(chip)
        
    def adc_reset(self):
        self.adc_reg.set_adc_board()
        
    def __init__(self):
        self.adc_regs_sw = None
        self.adc_regs_sent = None