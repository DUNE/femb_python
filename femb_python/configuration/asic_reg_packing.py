#!/usr/bin/env python3

class ASIC_REG_PACKING:

####sec_chn_reg only sets a channel register, the other registers remains as before
    def set_chn_reg(self, chip, chn, chn_reg_bits):
        """
        chn_reg_bits is a list of bits (0 or 1)
        """
        if chn_reg_bits >= 2**self.chn_reg_len:
            raise Exception("{} is too large, only {} bits allowed".format(chn_reg_bits,self.chn_reg_len))
        chn_reg_bool = []
        for j in range(self.chn_reg_len):
            chn_reg_bool.append ( bool( (chn_reg_bits>>j)%2 ) )

        regs_bool1_4 = []
        for i in self.REGS:
            for j in range(0,16,1):
                regs_bool1_4.append ( bool( (i>>j)%2 ) )

        regs_bool5_8 = []
        for i in self.REGS:
            for j in range(16,32,1):
                regs_bool5_8.append ( bool( (i>>j)%2 ) )

        if (chip < 4):
            pos = (3-chip)*self.chipbits + ( 15 - chn) * self.chn_reg_len
            regs_bool1_4[pos:pos+self.chn_reg_len] = chn_reg_bool
        elif ( chip < 8 ):
            pos = (7-chip)*self.chipbits + ( 15 - chn) * self.chn_reg_len
            regs_bool5_8[pos:pos+self.chn_reg_len] = chn_reg_bool
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
    def set_chip_global(self, chip, gbl_reg_bits):
        """
        gbl_reg_bits is a list of bits (0 or 1)
        """
        if gbl_reg_bits >= 2**self.gbl_reg_len:
            raise Exception("{} is too large, only {} bits allowed".format(gbl_reg_bits,self.gbl_reg_len))
        global_reg = []
        for j in range(self.gbl_reg_len):
            global_reg.append ( bool( (gbl_reg_bits>>j)%2 ) )

        regs_bool1_4 = []
        for i in self.REGS:
            for j in range(0,16,1):
                regs_bool1_4.append ( bool( (i>>j)%2 ) )

        regs_bool5_8 = []
        for i in self.REGS:
            for j in range(16,32,1):
                regs_bool5_8.append ( bool( (i>>j)%2 ) )

        if (chip < 4):
            pos = (3-chip)*self.chipbits + 16 * self.chn_reg_len
            regs_bool1_4[pos:pos+self.gbl_reg_len] = global_reg
        elif ( chip < 8 ):
            pos = (7-chip)*self.chipbits + 16 * self.chn_reg_len
            regs_bool5_8[pos:pos+self.gbl_reg_len] = global_reg
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
    def set_chip(self, chip,global_bits,channel_bits):
        for chn in range(16):
            self.set_chn_reg(chip, chn, channel_bits)     

        self.set_chip_global(chip, global_bits)

####sec_board sets registers of a whole board 
    def set_board(self,global_bits,channel_bits):
        for chip in range(8):
            self.set_chip( chip, global_bits, channel_bits)

    def __str__(self):
        """
        If you print a ASIC_REG_PACKING object, this will be called
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
                pos = (3-chip)*self.chipbits + 16 * self.chn_reg_len
                result['global'].append(reversed(regs_bool1_4[pos:pos+9]))
            elif ( chip < 8 ):
                pos = (7-chip)*self.chipbits + 16 * self.chn_reg_len
                result['global'].append(reversed(regs_bool5_8[pos:pos+9]))
            result['channel'].append([])
            for chn in range(16):
                if (chip < 4):
                    pos = (3-chip)*self.chipbits  + ( 15 - chn) * self.chn_reg_len
                    result['channel'][chip].append(reversed(regs_bool1_4[pos:pos+8]))
                elif ( chip < 8 ):
                    pos = (7-chip)*self.chipbits   + ( 15 - chn) * self.chn_reg_len
                    result['channel'][chip].append(reversed(regs_bool5_8[pos:pos+8]))
        return result

    def getREGS(self):
        return self.REGS

    #__INIT__#
    def __init__(self,global_bit_len=9,channel_bit_len=8,regs=[ 
                       0x0c0c0c0c, 0x0c0c0c0c, 0x0c0c0c0c, 0x0c0c0c0c, 
                       0x0c0c0c0c, 0x0c0c0c0c, 0x0c0c0c0c, 0x0c0c0c0c, 
                       0x18321832, 0x18181818, 0x18181818, 0x18181818,
                       0x18181818, 0x18181818, 0x18181818, 0x18181818,
                       0x64186418, 0x30303030, 0x30303030, 0x30303030,
                       0x30303030, 0x30303030, 0x30303030, 0x30303030,
                       0x30303030, 0x60C860C8, 0x60606060, 0x60606060,
                       0x60606060, 0x60606060, 0x60606060, 0x60606060,
                       0x60606060, 0x90609060, 0x00010001 ]
                ):
	#declare board specific registers
        self.chn_reg_len = channel_bit_len
        self.gbl_reg_len = global_bit_len
        self.chipbits = self.gbl_reg_len + 16*self.chn_reg_len
        self.REGS = regs

if __name__ == "__main__":
    a = ASIC_REG_PACKING()
    print("Default:")
    print(a)
    a.printDecode()
    #a.set_board(0b0000101,0b10000100)
    #print(a)
    print()
    a.printDecode()

    print("This is the working set of bits:")
    x = [0xC0C0C0C,
        0xC0C0C0C,
        0xC0C0C0C,
        0xC0C0C0C,
        0xC0C0C0C,
        0xC0C0C0C,
        0xC0C0C0C,
        0xC0C0C0C,
        0x18321832,
        0x18181818,
         0x18181818,
         0x18181818,
         0x18181818,
         0x18181818,
         0x18181818,
         0x18181818,
         0x64186418,
         0x30303030,
         0x30303030,
         0x30303030,
         0x30303030,
         0x30303030,
         0x30303030,
         0x30303030,
         0x30303030,
         0x60c868c8,
         0x60606868,
         0x60606868,
         0x60606868,
         0x60606868,
         0x60606868,
         0x60606868,
         0x60606868,
         0x9060A868,
         0x10001]
    a.REGS = x
    print(a)
    a.printDecode()
