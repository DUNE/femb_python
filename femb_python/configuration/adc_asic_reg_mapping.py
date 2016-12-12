#!/usr/bin/env python3
"""
Maps ADC register names to bits
"""
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import absolute_import

from builtins import range
from builtins import str
from future import standard_library
standard_library.install_aliases()
from builtins import object
from .asic_reg_packing import ASIC_REG_PACKING
import math

class ADC_ASIC_REG_MAPPING(object):
    """
    Maps ADC register names to bits
    """

    def __init__(self,version):
        """
        Give the ADC numerical version, e.g. 6 for V*
        """
        self.version=version
        self.global_bit_len = 9
        self.channel_bit_len = 8
        if version == 7:
          self.global_bit_len = 16
        nRegs = math.ceil((self.global_bit_len*8+self.channel_bit_len*8*16)/32.)
        allzeroRegs = [0x0 for i in range(nRegs)]
        self.reg_packing = ASIC_REG_PACKING(self.global_bit_len,self.channel_bit_len,allzeroRegs)

    def getREGS(self):
        return self.reg_packing.getREGS()

    def set_chn_reg(self, chip, chn, D=0x0,PCSR=0x0, PDSR=0x0, SLP=0x0, TSTIN=0x0):
        """
        Sets channel registers all other registers remain as before
        chip is int chip number (start from 0)
        chn is int channel number (start from 0)

        All registers must be referred to as keyword argumetns, upper case.
        """
        for x in [PCSR,PDSR,SLP,TSTIN]:
            if x > 1 or x < 0:
                raise Exception("PCSR, PDSR, SLP, TSTIN must all be single bits (0 or 1)")
        if D >= 16 or D < 0:
            raise Exception("D must be 4 bits (0-15)")
        thisRegister = 0x0
        thisRegister = thisRegister | (D << 4)
        thisRegister = thisRegister | (PCSR << 3)
        thisRegister = thisRegister | (PDSR << 2)
        thisRegister = thisRegister | (SLP << 1)
        thisRegister = thisRegister | (TSTIN << 0)
        print("D: {:#06b} PCSR: {:#03b} PDSR: {:#03b} SLP: {:#03b}  TSTIN: {:#03b} Register: {:#010b}".format(D,PCSR,PDSR,SLP,TSTIN,thisRegister))
        self.reg_packing.set_chn_reg(chip,chn,thisRegister)

    def set_chip_global(self, chip, **kwargs):
        """
        Sets channel registers all other registers remain as before
        chip is int chip number (start from 0)

        All registers must be referred to as keyword argumetns, upper case.
        """
        
        bits= {
            "F1":7,
            "CLK":5,
            "FRQC":4,
            "EN_GR":3,
            "F2":1,
        }
        widths = {
            "CLK": 2,
        }
        if self.version == 7:
            bits= {
                "sLSB": 5,
                "F5": 6,
                "F4": 7,
                "F3": 8,
                "F2": 9,
                "F1": 10,
                "F0": 11,
                "EN_GR": 12,
                "FRQC": 13,
                "CLK": 14,
            }
            widths = {
                "CLK": 2,
            }

        thisRegister = 0x0
        debugstr = ""
        for name in bits:
            x = None
            try:
                x = kwargs[name]
            except:
                raise Exception("ADC set_chip_global: {} keyword argument required for ADC ASIC v {}".format(name,self.version))
            width = 1
            try:
                width = widths[name]
            except:
                pass
            if x >= 2**width or x < 0:
                raise Exception("{} is {} bits, so must be between 0 and {}".format(name,width,2**width-1))
            thisRegister = thisRegister | (x << bits[name])
            debugstr += ("{}: {:#0"+str(width+2)+"b} ").format(name,x)
        debugstr += ("Register: {:#018b} ").format(thisRegister)
        print(debugstr)
        self.reg_packing.set_chip_global(chip,thisRegister)

    def set_chip(self,chip,**kwargs):
        """
        Sets globals in chip and all channels to given bits
        """
        chipDict = {}
        for chipkey in ["D","PCSR","PDSR","SLP","TSTIN"]:
            chipval = None
            try:
                chipval = kwargs.pop(chipkey)
            except:
                raise Exception("ADC set_chip: '{}' channel register value keyword argument is required".format(chipkey))
            else:
                chipDict[chipkey] = chipval
        self.set_chip_global(chip,**kwargs)
        for iChan in range(16):
            self.set_chn_reg(chip,iChan,**chipDict)
        
    def set_board(self,**kwargs):
        """
        Sets globals in chip and all channels to given bits for all chips
        """
        for iChip in range(8):
            self.set_chip(iChip,**kwargs)

if __name__=="__main__":
    aarm = ADC_ASIC_REG_MAPPING(6)
    aarm.set_chn_reg(0,0)
    aarm = ADC_ASIC_REG_MAPPING(6)
    aarm.set_chip_global(0,F1=1,CLK=0b10,FRQC=1,EN_GR=0,F2=0)
    aarm = ADC_ASIC_REG_MAPPING(7)
    aarm.set_chip_global(0,F0=0,F1=0,F2=0,F3=0,F4=1,F5=0,CLK=0b10,FRQC=0,EN_GR=1,sLSB=1)
    print()
    aarm.set_chip(0,F0=0,F1=0,F2=0,F3=0,F4=1,F5=0,CLK=0b10,FRQC=0,EN_GR=1,sLSB=1,D=0,PCSR=0,PDSR=0,SLP=0,TSTIN=0)
    print()
    aarm.set_chip(0,F0=0,F1=0,F2=0,F3=0,F4=1,F5=0,CLK=0b10,FRQC=0,EN_GR=1,sLSB=1,D=0,PCSR=1,PDSR=0,SLP=1,TSTIN=0)

    print("Set board:")
    aarm.set_board(F0=0,F1=0,F2=0,F3=0,F4=1,F5=0,CLK=0b10,FRQC=0,EN_GR=1,sLSB=1,D=0,PCSR=1,PDSR=0,SLP=1,TSTIN=0)

