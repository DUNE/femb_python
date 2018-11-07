# -*- coding: utf-8 -*-
"""
Created on Tue May 16 14:55:49 2017

@author: vlsilab2
"""
import sys
#from tabulate import tabulate

class FE_INFO:
    
    def fe_chip_status(self,chip=0,status="sent"):
        
        if (status == "sent"):
            fe_regs = self.fe_regs_sent
            if (fe_regs == None):
                print ("No registers have been written to the board yet")
                return
        elif (status == "to send"):
            fe_regs = self.fe_regs_sw
                
        else:
            print ("Incorrect status, do you want to see the registers that are 'to send'?  Or the ones 'sent'?")
            return
            
        headers = ["Channel", "Test Cap", "Baseline", "Gain", "Peaking Time", "Monitor", "Buffer", ]
        registers=[["0"],["1"],["2"],["3"],["4"],["5"],["6"],["7"],["8"],["9"],["10"],["11"],["12"],["13"],["14"],["15"],]

        for chn in range(16):
            spot = ((20*chip) + (15 - chn))
            tuple_num = (spot // 4)
            if (chn%4 == 0):
                bitshift = 24
            elif (chn%4 == 1):
                bitshift = 16
            elif (chn%4 == 2):
                bitshift = 8
            elif (chn%4 == 3):
                bitshift = 0
        #now we have bitmasks assigned for each position, so we can easily isolate the two hex letters we want
            find_mask = (0xFF << bitshift)
            existing_settings = ((fe_regs[tuple_num] & find_mask) >> bitshift)
            
            if ((existing_settings & 0x80)>>7 == 1):
                registers[chn].append("On")
            else:
                registers[chn].append("Off")
    
            if ((existing_settings & 0x40)>>6 == 1):
                registers[chn].append("200 mV")
            else:
                registers[chn].append("900 mV")
                
            if ((existing_settings & 0x30)>>4 == 0):
                registers[chn].append("4.7 mV/fC")
            elif ((existing_settings & 0x30)>>4 == 1):
                registers[chn].append("14 mV/fC")
            elif ((existing_settings & 0x30)>>4 == 2):
                registers[chn].append("7.8 mV/fC")
            else:
                registers[chn].append("25 mV/fC")
                
            if ((existing_settings & 0x0c)>>2 == 0):
                registers[chn].append("1 us")
            elif ((existing_settings & 0x0c)>>2 == 1):
                registers[chn].append("3 us")
            elif ((existing_settings & 0x0c)>>2 == 2):
                registers[chn].append("0.5 us")
            else:
                registers[chn].append("2 us")
                
            if ((existing_settings & 0x02)>>1 == 1):
                registers[chn].append("On")
            else:
                registers[chn].append("")
                
            if ((existing_settings & 0x01) == 1):
                registers[chn].append("On")
            else:
                registers[chn].append("Off")
                
        print ("Channel Registers for Front End chip " + str(chip) + " are:")
        print (tabulate(registers,headers,tablefmt="grid"))
        print ("\n")
        
        headers = ["DAC Value", "SDACSW1", "SDACSW2", "Coupling", "Leakage", "Ch16 Filter", "Ch1 Output" ]
        registers=[[]]

        tuple_num = (chip * 5) + 4
                
        find_mask = (0xFFFF)
        existing_settings = ((fe_regs[tuple_num] & find_mask) >> bitshift)
        
        dac_setting = (existing_settings & 0xfc00)
        dac_digit1 = (dac_setting & 0x8000) >> 15
        dac_digit2 = (dac_setting & 0x4000) >> 13
        dac_digit3 = (dac_setting & 0x2000) >> 11
        dac_digit4 = (dac_setting & 0x1000) >> 9
        dac_digit5 = (dac_setting & 0x0800) >> 7
        dac_digit6 = (dac_setting & 0x0400) >> 5
        dac_setting = dac_digit1 + dac_digit2 + dac_digit3 + dac_digit4 + dac_digit5 + dac_digit6

        registers[0].append(str(dac_setting))
        
        if ((existing_settings & 0x0200)>>9 == 1):
            registers[0].append("Closed")
        else:
            registers[0].append("Open")
    
        if ((existing_settings & 0x0100)>>8 == 1):
            registers[0].append("Closed")
        else:
            registers[0].append("Open")
             
        if ((existing_settings & 0x0020)>>5 == 0):
           registers[0].append("DC")
        else:
            registers[0].append("AC")
                
        if (((existing_settings & 0x0010)>>3) + ((existing_settings & 0x0001)) == 0):
            registers[0].append("500 pA")
        elif (((existing_settings & 0x0010)>>3) + ((existing_settings & 0x0001)) == 1):
            registers[0].append("100 pA")
        elif (((existing_settings & 0x0010)>>3) + ((existing_settings & 0x0001)) == 2):
            registers[0].append("5 nA")
        else:
           registers[0].append("1 nA")
           
        if ((existing_settings & 0x0008)>>3 == 0):
           registers[0].append("Disconnected")
        else:
            registers[0].append("Connected")
                
        if (((existing_settings & 0x0006)>>1) == 2):
            registers[0].append("Temperature")
        elif (((existing_settings & 0x0006)>>1) == 3):
            registers[0].append("Bandgap")
        else:
           registers[0].append("Normal output")

        print ("Global Registers for Front End chip " + str(chip) + " are:")
        print (tabulate(registers,headers,tablefmt="grid"))
        print ("\n")
        
    def fe_channel(self,chip=0,chn=0,sts=-1,snc=-1,sg=-1,st=-1,smn=-1,sbf=-1,show="FALSE"):
        self.fe_reg.set_fe_chn(chip,chn,sts,snc,sg,st,smn,sbf,show)
        self.fe_chip_status(chip)
        
    def fe_global(self,chip=0,slk=-1,stb=-1,s16=-1,sdc=-1,slkh=-1,sdacsw2=-1,sdacsw1=-1,sdac=-1,show="FALSE"):
        self.fe_reg.set_fe_global(chip,slk,stb,s16,sdc,slkh,sdacsw2,sdacsw1,sdac,show)
        self.fe_chip_status(chip)
        
    def fe_chip(self,chip=0,sts=0,snc=1,sg=0,st=0,smn=0,sbf=0,slk=0,stb=0,s16=0,slkh=0,sdc=0,sdacsw2=0,sdacsw1=0,sdac=0,show="FALSE"):
        self.fe_reg.set_fe_chip(chip,sts,snc,sg,st,smn,sbf,slk,stb,s16,slkh,sdc,sdacsw2,sdacsw1,sdac,show)
        self.fe_chip_status(chip)
        
    def fe_reset(self):
        self.fe_reg.set_fe_board()
        
    def __init__(self):
        self.fe_regs_sw = None
        self.fe_regs_sent = None