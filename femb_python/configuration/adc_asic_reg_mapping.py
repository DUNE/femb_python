#!/usr/bin/env python3

class ADC_ASIC_REG_MAPPING:

####sec_chn_reg only sets a channel register, the other registers remains as before
    def set_chn_reg(self, chip=0, chn=0, d=0, pcsr=1, pdsr=1, slp=0, tstin=0 ):
        chn_reg = ((d<<4)&0xF0) + ((pcsr&0x01)<<3) + ((pdsr&0x01)<<2) + \
                  ((slp&0x01)<<1) + ((slp&0x01)<<0)

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
            pos = (3-chip)*137 + ( 15 - chn) * 8
            regs_bool1_4[pos:pos+8] = chn_reg_bool
        elif ( chip < 8 ):
            pos = (7-chip)*137 + ( 15 - chn) * 8
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
    def set_chip_global(self, chip, res2 = 0, f1 = 0, clk0 = 0, clk1 = 1, 
                        frqc = 1, en_gr = 0, res1 = 0, f2 = 1, res0 = 0):
        global_reg = [True, False, True, False, True, True, False, False, True]
        global_reg[0] = (bool(res0)) 
        global_reg[1] = (bool(f2))
        global_reg[2] = (bool(res1)) 
        global_reg[3] = (bool(en_gr)) 
        global_reg[4] = (bool(frqc)) 
        global_reg[5] = (bool(clk1)) 
        global_reg[6] = (bool(clk0)) 
        global_reg[7] = (bool(f1)) 
        global_reg[8] = (bool(res2)) 

        regs_bool1_4 = []
        for i in self.REGS:
            for j in range(0,16,1):
                regs_bool1_4.append ( bool( (i>>j)%2 ) )

        regs_bool5_8 = []
        for i in self.REGS:
            for j in range(16,32,1):
                regs_bool5_8.append ( bool( (i>>j)%2 ) )

        if (chip < 4):
            pos = (3-chip)*137 + 128
            regs_bool1_4[pos:pos+9] = global_reg
        elif ( chip < 8 ):
            pos = (7-chip)*137 + 128
            regs_bool5_8[pos:pos+9] = global_reg
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
                 res2 = 1, f1 = 0, clk0 = 0, clk1 = 1, 
                 frqc = 1, en_gr = 0, res1 = 1, f2 = 0, res0 = 1):
        for chn in range(16):
            self.set_chn_reg(chip, chn, d, pcsr, pdsr, slp, tstin )     

        self.set_chip_global (chip, res2, f1, clk0, clk1, frqc, en_gr, res1, f2, res0)

####sec_sbnd_board sets registers of a whole board 
    def set_sbnd_board(self,  
                 d=0, pcsr=1, pdsr=1, slp=0, tstin=0,
                 res2 = 1, f1 = 0, clk0 = 0, clk1 = 1, 
                 frqc = 1, en_gr = 0, res1 = 1, f2 = 0, res0 = 1):
        for chip in range(8):
            self.set_chip( chip, d, pcsr, pdsr, slp, tstin,
                 res2, f1, clk0, clk1, frqc, en_gr, res1, f2, res0)

    def __str__(self):
        """
        If you print a ADC_ASIC_REG_MAPPING object, this will be called
        """
        nPerRow = 4
        outString = ""
        for iReg in range(len(self.REGS)):
            if iReg % nPerRow == 0:
                outString += "\n"
            outString += "{:#010x} ".format(self.REGS[iReg])
        return outString

    def printBinary(self,register=-1):
        """
        Prints out registers in binary
        """
        outString = ""
        if register >= 0:
            outString += "{:#034b}\n".format(self.REGS[register])
        else:
          for iReg in range(len(self.REGS)):
            outString += "{:#034b}\n".format(self.REGS[iReg])
        print(outString)

    def printDecode(self):
        outString = ""
        decoded = self.decode()
        for chip in range(8):
            outString += "Chip {}\n".format(chip)
            outString += "  Global: "
            for i in decoded['global'][chip]:
                if i:
                  outString += "1 "
                else:
                  outString += "0 "
            outString += "\n"
            for chn in range(16):
                outString += "  Channel {:2}: ".format(chn)
                for i in decoded['channel'][chip][chn]:
                    if i:
                      outString += "1 "
                    else:
                      outString += "0 "
                outString += "\n"
        print(outString)

    def decode(self):
        """
        Returns a dictionary of decoded registers. The format is:

        result['global'][iChip]
        result['channel'][iChip][iChan]

        Each of those are lists of bools with configuration bits
        """
        result = {}
        result['global'] = []
        result['channel'] = []

        regs_bool1_4 = []
        for i in self.REGS:
            for j in range(0,16,1):
                regs_bool1_4.append ( bool( (i>>j)%2 ) )

        regs_bool5_8 = []
        for i in self.REGS:
            for j in range(16,32,1):
                regs_bool5_8.append ( bool( (i>>j)%2 ) )

        for chip in range(8):
            if (chip < 4):
                pos = (3-chip)*137 + 128
                result['global'].append(reversed(regs_bool1_4[pos:pos+9]))
            elif ( chip < 8 ):
                pos = (7-chip)*137 + 128
                result['global'].append(reversed(regs_bool5_8[pos:pos+9]))
            result['channel'].append([])
            for chn in range(16):
                if (chip < 4):
                    pos = (3-chip)*137 + ( 15 - chn) * 8
                    result['channel'][chip].append(reversed(regs_bool1_4[pos:pos+8]))
                elif ( chip < 8 ):
                    pos = (7-chip)*137 + ( 15 - chn) * 8
                    result['channel'][chip].append(reversed(regs_bool5_8[pos:pos+8]))
        return result

    def getREGS(self):
        return self.REGS

    #__INIT__#
    def __init__(self, regs=None):
	#declare board specific registers
        if regs:
          self.REGS = regs
        else:
          self.REGS =[ 0x0c0c0c0c, 0x0c0c0c0c, 0x0c0c0c0c, 0x0c0c0c0c, 
                       0x0c0c0c0c, 0x0c0c0c0c, 0x0c0c0c0c, 0x0c0c0c0c, 
                       0x18321832, 0x18181818, 0x18181818, 0x18181818,
                       0x18181818, 0x18181818, 0x18181818, 0x18181818,
                       0x64186418, 0x30303030, 0x30303030, 0x30303030,
                       0x30303030, 0x30303030, 0x30303030, 0x30303030,
                       0x30303030, 0x60C860C8, 0x60606060, 0x60606060,
                       0x60606060, 0x60606060, 0x60606060, 0x60606060,
                       0x60606060, 0x90609060, 0x00010001 ]

if __name__ == "__main__":
    a = ADC_ASIC_REG_MAPPING()
    print("Default:")
    print(a)
    print()
    a.printDecode()
    a.set_sbnd_board(d=0, pcsr=1, pdsr=0, slp=0, tstin=0,
                 res2 = 0, f1 = 0, clk0 = 0, clk1 = 0, 
                 frqc = 0, en_gr = 0, res1 = 0, f2 = 0, res0 = 0)
    print(a)
    a.printDecode()
#    a.set_sbnd_board()
#    print("set_sbnd_board:")
#    print(a)
#    a.REGS = [0 for reg in a.REGS]
#    print("All 0:")
#    print(a)
#    a.set_chip_global(3, res2 = 0, f1 = 0, clk0 = 0, clk1 = 0, 
#                        frqc = 0, en_gr = 0, res1 = 0, f2 = 0, res0 = 1)
#    print("Set chip 3 global regs res0=1 only:")
#    print(a)
#
#    a.REGS = [0 for reg in a.REGS]
#    a.set_chip_global(3, res2 = 0, f1 = 0, clk0 = 0, clk1 = 0, 
#                        frqc = 0, en_gr = 0, res1 = 0, f2 = 1, res0 = 0)
#    print("Set chip 3 global regs f2=1 only:")
#    print(a)
#
#    a.REGS = [0 for reg in a.REGS]
#    a.set_chip_global(3, res2 = 0, f1 = 0, clk0 = 0, clk1 = 0, 
#                        frqc = 0, en_gr = 0, res1 = 1, f2 = 0, res0 = 0)
#    print("Set chip 3 global regs res1=1 only:")
#    print(a)
#
#    a.REGS = [0 for reg in a.REGS]
#    a.set_chip_global(3, res2 = 0, f1 = 1, clk0 = 0, clk1 = 0, 
#                        frqc = 0, en_gr = 0, res1 = 0, f2 = 0, res0 = 0)
#    print("Set chip 3 global regs f1=1 only:")
#    print(a)
#
#    a.REGS = [0 for reg in a.REGS]
#    a.set_chip_global(3, res2 = 1, f1 = 0, clk0 = 0, clk1 = 0, 
#                        frqc = 0, en_gr = 0, res1 = 0, f2 = 0, res0 = 0)
#    print("Set chip 3 global regs res2=1 only:")
#    print(a)
#
#
#    a.REGS = [0 for reg in a.REGS]
#    a.set_chn_reg(chip=7, chn=15, d=0b1111, pcsr=0, pdsr=0, slp=0, tstin=0 )
#    print("Set chip 7 channel 15 D0=0b1111 only:")
#    print(a)
#    a.printBinary(0)
#
#    a.REGS = [0 for reg in a.REGS]
#    a.set_chn_reg(chip=7, chn=14, d=0, pcsr=0, pdsr=1, slp=0, tstin=0 )
#    print("Set chip 7 channel 14 pdsr=1 only:")
#    print(a)
#    a.printBinary(0)
#
#    a.REGS = [0 for reg in a.REGS]
#    a.set_chip_global(7, res2 = 0, f1 = 0, clk0 = 0, clk1 = 0, 
#                        frqc = 0, en_gr = 0, res1 = 0, f2 = 1, res0 = 0)
#    print("Set chip 7 global regs f2=1 only:")
#    print(a)
#    a.printBinary(0)
#
#    a.REGS = [0 for reg in a.REGS]
#    a.set_chn_reg(chip=3, chn=15, d=0b1111, pcsr=0, pdsr=0, slp=0, tstin=0 )
#    print("Set chip 3 channel 15 D0=0b1111 only:")
#    print(a)
#    a.printBinary(0)
#
#    a.REGS = [0 for reg in a.REGS]
#    a.set_chn_reg(chip=3, chn=12, d=0, pcsr=0, pdsr=1, slp=0, tstin=0 )
#    print("Set chip 3 channel 12 pdsr=1 only:")
#    print(a)
#    a.printBinary(1)
#
#    a.REGS = [0 for reg in a.REGS]
#    a.set_chip_global(3, res2 = 0, f1 = 0, clk0 = 0, clk1 = 0, 
#                        frqc = 0, en_gr = 0, res1 = 0, f2 = 1, res0 = 0)
#    print("Set chip 3 global regs f2=1 only:")
#    print(a)
#    a.printBinary(0)
#
#    a.REGS = [0 for reg in a.REGS]
#    a.set_chn_reg(chip=6, chn=15, d=0, pcsr=0, pdsr=1, slp=0, tstin=0 )
#    print("Set chip 6 channel 15 pdsr=1 only:")
#    print(a)
#    a.printBinary(8)
#
#    a.REGS = [0 for reg in a.REGS]
#    a.set_chn_reg(chip=6, chn=14, d=0, pcsr=0, pdsr=1, slp=0, tstin=0 )
#    print("Set chip 6 channel 14 pdsr=1 only:")
#    print(a)
#    a.printBinary(9)
#
#    a.REGS = [0 for reg in a.REGS]
#    a.set_chn_reg(chip=6, chn=0, d=0, pcsr=0, pdsr=1, slp=0, tstin=0 )
#    print("Set chip 6 channel 0 pdsr=1 only:")
#    print(a)
#    a.printBinary(16)
#
#    a.REGS = [0 for reg in a.REGS]
#    a.set_chip_global(6, res2 = 0, f1 = 0, clk0 = 0, clk1 = 0, 
#                        frqc = 0, en_gr = 0, res1 = 0, f2 = 1, res0 = 0)
#    print("Set chip 6 global regs f2=1 only:")
#    print(a)
#    a.printBinary(16)
#
#    a.REGS = [0 for reg in a.REGS]
#    a.set_chip_global(6, res2 = 0, f1 = 1, clk0 = 0, clk1 = 0, 
#                        frqc = 0, en_gr = 0, res1 = 0, f2 = 0, res0 = 0)
#    print("Set chip 6 global regs f1=1 only:")
#    print(a)
#    a.printBinary(17)
#
#    a.REGS = [0 for reg in a.REGS]
#    a.set_chn_reg(chip=5, chn=15, d=0, pcsr=0, pdsr=1, slp=0, tstin=0 )
#    print("Set chip 5 channel 15 pdsr=1 only:")
#    print(a)
#    a.printBinary(17)
#
#    a.REGS = [0 for reg in a.REGS]
#    a.set_chn_reg(chip=5, chn=14, d=0, pcsr=0, pdsr=1, slp=0, tstin=0 )
#    print("Set chip 5 channel 14 pdsr=1 only:")
#    print(a)
#    a.printBinary(17)
#
#    a.REGS = [0 for reg in a.REGS]
#    a.set_chn_reg(chip=5, chn=13, d=0, pcsr=0, pdsr=1, slp=0, tstin=0 )
#    print("Set chip 5 channel 13 pdsr=1 only:")
#    print(a)
#    a.printBinary(16)
#
#    a.REGS = [0 for reg in a.REGS]
#    a.set_chn_reg(chip=5, chn=12, d=0, pcsr=0, pdsr=1, slp=0, tstin=0 )
#    print("Set chip 5 channel 12 pdsr=1 only:")
#    print(a)
#    a.printBinary(16)
#
#    a.REGS = [0 for reg in a.REGS]
#    a.set_chip_global(5, res2 = 0, f1 = 1, clk0 = 0, clk1 = 0, 
#                        frqc = 0, en_gr = 0, res1 = 0, f2 = 0, res0 = 0)
#    print("Set chip 5 global regs f1=1 only:")
#    print(a)
#    a.printBinary(25)
#
#    a.REGS = [0 for reg in a.REGS]
#    a.set_chn_reg(chip=4, chn=15, d=0, pcsr=0, pdsr=1, slp=0, tstin=0 )
#    print("Set chip 4 channel 15 pdsr=1 only:")
#    print(a)
#    a.printBinary(25)
#
#    a.REGS = [0 for reg in a.REGS]
#    a.set_chn_reg(chip=4, chn=14, d=0, pcsr=0, pdsr=1, slp=0, tstin=0 )
#    print("Set chip 4 channel 14 pdsr=1 only:")
#    print(a)
#    a.printBinary(26)
#
#    a.REGS = [0 for reg in a.REGS]
#    a.set_chn_reg(chip=4, chn=13, d=0, pcsr=0, pdsr=1, slp=0, tstin=0 )
#    print("Set chip 4 channel 13 pdsr=1 only:")
#    print(a)
#    a.printBinary(26)
#
#    a.REGS = [0 for reg in a.REGS]
#    a.set_chn_reg(chip=4, chn=0, d=0, pcsr=0, pdsr=1, slp=0, tstin=0 )
#    print("Set chip 4 channel 0 pdsr=1 only:")
#    print(a)
#    a.printBinary(33)
#
#    a.REGS = [0 for reg in a.REGS]
#    a.set_chip_global(4, res2 = 0, f1 = 0, clk0 = 0, clk1 = 0, 
#                        frqc = 0, en_gr = 0, res1 = 0, f2 = 1, res0 = 0)
#    print("Set chip 4 global regs f2=1 only:")
#    print(a)
#    a.printBinary(33)
#
#
#    a.REGS = [0 for reg in a.REGS]
#    a.set_chip_global(4, res2 = 0, f1 = 1, clk0 = 0, clk1 = 0, 
#                        frqc = 0, en_gr = 0, res1 = 0, f2 = 0, res0 = 0)
#    print("Set chip 4 global regs f1=1 only:")
#    print(a)
#    a.printBinary(34)

