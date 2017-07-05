#!/usr/bin/env python33

"""
Just like quadFeAsic, just with self.COLD = True
"""

from femb_python.configuration.configs import quadFeAsic

class FEMB_CONFIG(quadFeAsic.FEMB_CONFIG):
    def __init__(self):
        super().__init__()
        self.COLD = True

        #COLD VERSION
        
        #add ADC clock phases/shifts here for now, not ideal
        #FE ASIC 0 Data shifts
        shiftRegNum = int(65)
        self.femb.write_reg_bits( shiftRegNum , 0, 0x3, 0x1 ) #ADC 0
        self.femb.write_reg_bits( shiftRegNum , 2, 0x3, 0x1 ) #ADC 1
        self.femb.write_reg_bits( shiftRegNum , 4, 0x3, 0x1 ) #ADC 2
        self.femb.write_reg_bits( shiftRegNum , 6, 0x3, 0x1 ) #ADC 3
        self.femb.write_reg_bits( shiftRegNum , 8, 0x3, 0x1 ) #ADC 4
        self.femb.write_reg_bits( shiftRegNum , 10, 0x3, 0x1 ) #ADC 5
        self.femb.write_reg_bits( shiftRegNum , 12, 0x3, 0x0 ) #ADC 6
        self.femb.write_reg_bits( shiftRegNum , 14, 0x3, 0x1 ) #ADC 7
        self.femb.write_reg_bits( shiftRegNum , 16, 0x3, 0x1 ) #ADC 8
        self.femb.write_reg_bits( shiftRegNum , 18, 0x3, 0x1 ) #ADC 9
        self.femb.write_reg_bits( shiftRegNum , 20, 0x3, 0x1 ) #ADC 10
        self.femb.write_reg_bits( shiftRegNum , 22, 0x3, 0x0 ) #ADC 11
        self.femb.write_reg_bits( shiftRegNum , 24, 0x3, 0x1 ) #ADC 12
        self.femb.write_reg_bits( shiftRegNum , 26, 0x3, 0x1 ) #ADC 13
        self.femb.write_reg_bits( shiftRegNum , 28, 0x3, 0x1 ) #ADC 14
        self.femb.write_reg_bits( shiftRegNum , 30, 0x3, 0x1 ) #ADC 15

        #FE ASIC 1 Data shifts
        shiftRegNum = int(66)
        self.femb.write_reg_bits( shiftRegNum , 0, 0x3, 0x1 ) #ADC 0
        self.femb.write_reg_bits( shiftRegNum , 2, 0x3, 0x1 ) #ADC 1
        self.femb.write_reg_bits( shiftRegNum , 4, 0x3, 0x1 ) #ADC 2
        self.femb.write_reg_bits( shiftRegNum , 6, 0x3, 0x1 ) #ADC 3
        self.femb.write_reg_bits( shiftRegNum , 8, 0x3, 0x1 ) #ADC 4
        self.femb.write_reg_bits( shiftRegNum , 10, 0x3, 0x1 ) #ADC 5
        self.femb.write_reg_bits( shiftRegNum , 12, 0x3, 0x1 ) #ADC 6
        self.femb.write_reg_bits( shiftRegNum , 14, 0x3, 0x1 ) #ADC 7
        self.femb.write_reg_bits( shiftRegNum , 16, 0x3, 0x1 ) #ADC 8
        self.femb.write_reg_bits( shiftRegNum , 18, 0x3, 0x1 ) #ADC 9
        self.femb.write_reg_bits( shiftRegNum , 20, 0x3, 0x1 ) #ADC 10
        self.femb.write_reg_bits( shiftRegNum , 22, 0x3, 0x1 ) #ADC 11
        self.femb.write_reg_bits( shiftRegNum , 24, 0x3, 0x1 ) #ADC 12
        self.femb.write_reg_bits( shiftRegNum , 26, 0x3, 0x1 ) #ADC 13
        self.femb.write_reg_bits( shiftRegNum , 28, 0x3, 0x1 ) #ADC 14
        self.femb.write_reg_bits( shiftRegNum , 30, 0x3, 0x1 ) #ADC 15

        #FE ASIC 2 Data shifts
        shiftRegNum = int(67)
        self.femb.write_reg_bits( shiftRegNum , 0, 0x3, 0x1 ) #ADC 0
        self.femb.write_reg_bits( shiftRegNum , 2, 0x3, 0x1 ) #ADC 1
        self.femb.write_reg_bits( shiftRegNum , 4, 0x3, 0x1 ) #ADC 2
        self.femb.write_reg_bits( shiftRegNum , 6, 0x3, 0x1 ) #ADC 3
        self.femb.write_reg_bits( shiftRegNum , 8, 0x3, 0x1 ) #ADC 4
        self.femb.write_reg_bits( shiftRegNum , 10, 0x3, 0x1 ) #ADC 5
        self.femb.write_reg_bits( shiftRegNum , 12, 0x3, 0x1 ) #ADC 6
        self.femb.write_reg_bits( shiftRegNum , 14, 0x3, 0x1 ) #ADC 7
        self.femb.write_reg_bits( shiftRegNum , 16, 0x3, 0x1 ) #ADC 8
        self.femb.write_reg_bits( shiftRegNum , 18, 0x3, 0x1 ) #ADC 9
        self.femb.write_reg_bits( shiftRegNum , 20, 0x3, 0x1 ) #ADC 10
        self.femb.write_reg_bits( shiftRegNum , 22, 0x3, 0x1 ) #ADC 11
        self.femb.write_reg_bits( shiftRegNum , 24, 0x3, 0x1 ) #ADC 12
        self.femb.write_reg_bits( shiftRegNum , 26, 0x3, 0x1 ) #ADC 13
        self.femb.write_reg_bits( shiftRegNum , 28, 0x3, 0x1 ) #ADC 14
        self.femb.write_reg_bits( shiftRegNum , 30, 0x3, 0x1 ) #ADC 15

        #FE ASIC 3 Data shifts
        shiftRegNum = int(68)
        self.femb.write_reg_bits( shiftRegNum , 0, 0x3, 0x1 ) #ADC 0
        self.femb.write_reg_bits( shiftRegNum , 2, 0x3, 0x1 ) #ADC 1
        self.femb.write_reg_bits( shiftRegNum , 4, 0x3, 0x0 ) #ADC 2
        self.femb.write_reg_bits( shiftRegNum , 6, 0x3, 0x1 ) #ADC 3
        self.femb.write_reg_bits( shiftRegNum , 8, 0x3, 0x1 ) #ADC 4
        self.femb.write_reg_bits( shiftRegNum , 10, 0x3, 0x1 ) #ADC 5
        self.femb.write_reg_bits( shiftRegNum , 12, 0x3, 0x1 ) #ADC 6
        self.femb.write_reg_bits( shiftRegNum , 14, 0x3, 0x1 ) #ADC 7
        self.femb.write_reg_bits( shiftRegNum , 16, 0x3, 0x1 ) #ADC 8
        self.femb.write_reg_bits( shiftRegNum , 18, 0x3, 0x1 ) #ADC 9
        self.femb.write_reg_bits( shiftRegNum , 20, 0x3, 0x1 ) #ADC 10
        self.femb.write_reg_bits( shiftRegNum , 22, 0x3, 0x1 ) #ADC 11
        self.femb.write_reg_bits( shiftRegNum , 24, 0x3, 0x1 ) #ADC 12
        self.femb.write_reg_bits( shiftRegNum , 26, 0x3, 0x1 ) #ADC 13
        self.femb.write_reg_bits( shiftRegNum , 28, 0x3, 0x1 ) #ADC 14
        self.femb.write_reg_bits( shiftRegNum , 30, 0x3, 0x1 ) #ADC 15

        #FE ASIC 0 phase shifts
        shiftRegNum = int(69)
        self.femb.write_reg_bits( shiftRegNum , 0, 0x3, 0x0 ) #ADC 0
        self.femb.write_reg_bits( shiftRegNum , 2, 0x3, 0x0 ) #ADC 1
        self.femb.write_reg_bits( shiftRegNum , 4, 0x3, 0x0 ) #ADC 2
        self.femb.write_reg_bits( shiftRegNum , 6, 0x3, 0x0 ) #ADC 3
        self.femb.write_reg_bits( shiftRegNum , 8, 0x3, 0x0) #ADC 4
        self.femb.write_reg_bits( shiftRegNum , 10, 0x3, 0x0 ) #ADC 5
        self.femb.write_reg_bits( shiftRegNum , 12, 0x3, 0x1 ) #ADC 6
        self.femb.write_reg_bits( shiftRegNum , 14, 0x3, 0x0 ) #ADC 7
        self.femb.write_reg_bits( shiftRegNum , 16, 0x3, 0x0 ) #ADC 8
        self.femb.write_reg_bits( shiftRegNum , 18, 0x3, 0x0 ) #ADC 9
        self.femb.write_reg_bits( shiftRegNum , 20, 0x3, 0x0 ) #ADC 10
        self.femb.write_reg_bits( shiftRegNum , 22, 0x3, 0x1 ) #ADC 11
        self.femb.write_reg_bits( shiftRegNum , 24, 0x3, 0x0 ) #ADC 12
        self.femb.write_reg_bits( shiftRegNum , 26, 0x3, 0x0 ) #ADC 13
        self.femb.write_reg_bits( shiftRegNum , 28, 0x3, 0x0 ) #ADC 14
        self.femb.write_reg_bits( shiftRegNum , 30, 0x3, 0x0 ) #ADC 15

        #FE ASIC 1 phase shifts
        shiftRegNum = int(70)
        self.femb.write_reg_bits( shiftRegNum , 0, 0x3, 0x0 ) #ADC 0
        self.femb.write_reg_bits( shiftRegNum , 2, 0x3, 0x0 ) #ADC 1
        self.femb.write_reg_bits( shiftRegNum , 4, 0x3, 0x0 ) #ADC 2
        self.femb.write_reg_bits( shiftRegNum , 6, 0x3, 0x0 ) #ADC 3
        self.femb.write_reg_bits( shiftRegNum , 8, 0x3, 0x0 ) #ADC 4
        self.femb.write_reg_bits( shiftRegNum , 10, 0x3, 0x0 ) #ADC 5
        self.femb.write_reg_bits( shiftRegNum , 12, 0x3, 0x0 ) #ADC 6
        self.femb.write_reg_bits( shiftRegNum , 14, 0x3, 0x0 ) #ADC 7
        self.femb.write_reg_bits( shiftRegNum , 16, 0x3, 0x0 ) #ADC 8
        self.femb.write_reg_bits( shiftRegNum , 18, 0x3, 0x0 ) #ADC 9
        self.femb.write_reg_bits( shiftRegNum , 20, 0x3, 0x0 ) #ADC 10
        self.femb.write_reg_bits( shiftRegNum , 22, 0x3, 0x0 ) #ADC 11
        self.femb.write_reg_bits( shiftRegNum , 24, 0x3, 0x0 ) #ADC 12
        self.femb.write_reg_bits( shiftRegNum , 26, 0x3, 0x0 ) #ADC 13
        self.femb.write_reg_bits( shiftRegNum , 28, 0x3, 0x0 ) #ADC 14
        self.femb.write_reg_bits( shiftRegNum , 30, 0x3, 0x0 ) #ADC 15

        #FE ASIC 2 phase shifts
        shiftRegNum = int(71)
        self.femb.write_reg_bits( shiftRegNum , 0, 0x3, 0x0 ) #ADC 0
        self.femb.write_reg_bits( shiftRegNum , 2, 0x3, 0x0 ) #ADC 1
        self.femb.write_reg_bits( shiftRegNum , 4, 0x3, 0x0 ) #ADC 2
        self.femb.write_reg_bits( shiftRegNum , 6, 0x3, 0x0 ) #ADC 3
        self.femb.write_reg_bits( shiftRegNum , 8, 0x3, 0x0 ) #ADC 4
        self.femb.write_reg_bits( shiftRegNum , 10, 0x3, 0x0 ) #ADC 5
        self.femb.write_reg_bits( shiftRegNum , 12, 0x3, 0x0 ) #ADC 6
        self.femb.write_reg_bits( shiftRegNum , 14, 0x3, 0x0 ) #ADC 7
        self.femb.write_reg_bits( shiftRegNum , 16, 0x3, 0x0 ) #ADC 8
        self.femb.write_reg_bits( shiftRegNum , 18, 0x3, 0x0 ) #ADC 9
        self.femb.write_reg_bits( shiftRegNum , 20, 0x3, 0x0 ) #ADC 10
        self.femb.write_reg_bits( shiftRegNum , 22, 0x3, 0x0 ) #ADC 11
        self.femb.write_reg_bits( shiftRegNum , 24, 0x3, 0x0 ) #ADC 12
        self.femb.write_reg_bits( shiftRegNum , 26, 0x3, 0x0 ) #ADC 13
        self.femb.write_reg_bits( shiftRegNum , 28, 0x3, 0x0 ) #ADC 14
        self.femb.write_reg_bits( shiftRegNum , 30, 0x3, 0x0 ) #ADC 15

        #FE ASIC 3 phase shifts
        shiftRegNum = int(72)
        self.femb.write_reg_bits( shiftRegNum , 0, 0x3, 0x0 ) #ADC 0
        self.femb.write_reg_bits( shiftRegNum , 2, 0x3, 0x0 ) #ADC 1
        self.femb.write_reg_bits( shiftRegNum , 4, 0x3, 0x1 ) #ADC 2
        self.femb.write_reg_bits( shiftRegNum , 6, 0x3, 0x0 ) #ADC 3
        self.femb.write_reg_bits( shiftRegNum , 8, 0x3, 0x0 ) #ADC 4
        self.femb.write_reg_bits( shiftRegNum , 10, 0x3, 0x0 ) #ADC 5
        self.femb.write_reg_bits( shiftRegNum , 12, 0x3, 0x0 ) #ADC 6
        self.femb.write_reg_bits( shiftRegNum , 14, 0x3, 0x0 ) #ADC 7
        self.femb.write_reg_bits( shiftRegNum , 16, 0x3, 0x0 ) #ADC 8
        self.femb.write_reg_bits( shiftRegNum , 18, 0x3, 0x0 ) #ADC 9
        self.femb.write_reg_bits( shiftRegNum , 20, 0x3, 0x0 ) #ADC 10
        self.femb.write_reg_bits( shiftRegNum , 22, 0x3, 0x0 ) #ADC 11
        self.femb.write_reg_bits( shiftRegNum , 24, 0x3, 0x0 ) #ADC 12
        self.femb.write_reg_bits( shiftRegNum , 26, 0x3, 0x0 ) #ADC 13
        self.femb.write_reg_bits( shiftRegNum , 28, 0x3, 0x0 ) #ADC 14
        self.femb.write_reg_bits( shiftRegNum , 30, 0x3, 0x0 ) #ADC 15


        """
        #Warm values
        #add ADC clock phases/shifts here for now, not ideal
        #FE ASIC 0 Data shifts
        shiftRegNum = int(65)
        self.femb.write_reg_bits( shiftRegNum , 0, 0x3, 0x0 ) #ADC 0
        self.femb.write_reg_bits( shiftRegNum , 2, 0x3, 0x0 ) #ADC 1
        self.femb.write_reg_bits( shiftRegNum , 4, 0x3, 0x0 ) #ADC 2
        self.femb.write_reg_bits( shiftRegNum , 6, 0x3, 0x0 ) #ADC 3
        self.femb.write_reg_bits( shiftRegNum , 8, 0x3, 0x0 ) #ADC 4
        self.femb.write_reg_bits( shiftRegNum , 10, 0x3, 0x0 ) #ADC 5
        self.femb.write_reg_bits( shiftRegNum , 12, 0x3, 0x0 ) #ADC 6
        self.femb.write_reg_bits( shiftRegNum , 14, 0x3, 0x0 ) #ADC 7
        self.femb.write_reg_bits( shiftRegNum , 16, 0x3, 0x0 ) #ADC 8
        self.femb.write_reg_bits( shiftRegNum , 18, 0x3, 0x0 ) #ADC 9
        self.femb.write_reg_bits( shiftRegNum , 20, 0x3, 0x0 ) #ADC 10
        self.femb.write_reg_bits( shiftRegNum , 22, 0x3, 0x0 ) #ADC 11
        self.femb.write_reg_bits( shiftRegNum , 24, 0x3, 0x0 ) #ADC 12
        self.femb.write_reg_bits( shiftRegNum , 26, 0x3, 0x0 ) #ADC 13
        self.femb.write_reg_bits( shiftRegNum , 28, 0x3, 0x0 ) #ADC 14
        self.femb.write_reg_bits( shiftRegNum , 30, 0x3, 0x0 ) #ADC 15

        #FE ASIC 1 Data shifts
        shiftRegNum = int(66)
        self.femb.write_reg_bits( shiftRegNum , 0, 0x3, 0x0 ) #ADC 0
        self.femb.write_reg_bits( shiftRegNum , 2, 0x3, 0x0 ) #ADC 1
        self.femb.write_reg_bits( shiftRegNum , 4, 0x3, 0x0 ) #ADC 2
        self.femb.write_reg_bits( shiftRegNum , 6, 0x3, 0x0 ) #ADC 3
        self.femb.write_reg_bits( shiftRegNum , 8, 0x3, 0x0 ) #ADC 4
        self.femb.write_reg_bits( shiftRegNum , 10, 0x3, 0x0 ) #ADC 5
        self.femb.write_reg_bits( shiftRegNum , 12, 0x3, 0x0 ) #ADC 6
        self.femb.write_reg_bits( shiftRegNum , 14, 0x3, 0x0 ) #ADC 7
        self.femb.write_reg_bits( shiftRegNum , 16, 0x3, 0x0 ) #ADC 8
        self.femb.write_reg_bits( shiftRegNum , 18, 0x3, 0x0 ) #ADC 9
        self.femb.write_reg_bits( shiftRegNum , 20, 0x3, 0x0 ) #ADC 10
        self.femb.write_reg_bits( shiftRegNum , 22, 0x3, 0x0 ) #ADC 11
        self.femb.write_reg_bits( shiftRegNum , 24, 0x3, 0x0 ) #ADC 12
        self.femb.write_reg_bits( shiftRegNum , 26, 0x3, 0x0 ) #ADC 13
        self.femb.write_reg_bits( shiftRegNum , 28, 0x3, 0x0 ) #ADC 14
        self.femb.write_reg_bits( shiftRegNum , 30, 0x3, 0x0 ) #ADC 15

        #FE ASIC 2 Data shifts
        shiftRegNum = int(67)
        self.femb.write_reg_bits( shiftRegNum , 0, 0x3, 0x0 ) #ADC 0
        self.femb.write_reg_bits( shiftRegNum , 2, 0x3, 0x0 ) #ADC 1
        self.femb.write_reg_bits( shiftRegNum , 4, 0x3, 0x0 ) #ADC 2
        self.femb.write_reg_bits( shiftRegNum , 6, 0x3, 0x0 ) #ADC 3
        self.femb.write_reg_bits( shiftRegNum , 8, 0x3, 0x0 ) #ADC 4
        self.femb.write_reg_bits( shiftRegNum , 10, 0x3, 0x0 ) #ADC 5
        self.femb.write_reg_bits( shiftRegNum , 12, 0x3, 0x0 ) #ADC 6
        self.femb.write_reg_bits( shiftRegNum , 14, 0x3, 0x0 ) #ADC 7
        self.femb.write_reg_bits( shiftRegNum , 16, 0x3, 0x0 ) #ADC 8
        self.femb.write_reg_bits( shiftRegNum , 18, 0x3, 0x0 ) #ADC 9
        self.femb.write_reg_bits( shiftRegNum , 20, 0x3, 0x0 ) #ADC 10
        self.femb.write_reg_bits( shiftRegNum , 22, 0x3, 0x0 ) #ADC 11
        self.femb.write_reg_bits( shiftRegNum , 24, 0x3, 0x0 ) #ADC 12
        self.femb.write_reg_bits( shiftRegNum , 26, 0x3, 0x0 ) #ADC 13
        self.femb.write_reg_bits( shiftRegNum , 28, 0x3, 0x0 ) #ADC 14
        self.femb.write_reg_bits( shiftRegNum , 30, 0x3, 0x0 ) #ADC 15

        #FE ASIC 3 Data shifts
        shiftRegNum = int(68)
        self.femb.write_reg_bits( shiftRegNum , 0, 0x3, 0x0 ) #ADC 0
        self.femb.write_reg_bits( shiftRegNum , 2, 0x3, 0x0 ) #ADC 1
        self.femb.write_reg_bits( shiftRegNum , 4, 0x3, 0x0 ) #ADC 2
        self.femb.write_reg_bits( shiftRegNum , 6, 0x3, 0x0 ) #ADC 3
        self.femb.write_reg_bits( shiftRegNum , 8, 0x3, 0x0 ) #ADC 4
        self.femb.write_reg_bits( shiftRegNum , 10, 0x3, 0x0 ) #ADC 5
        self.femb.write_reg_bits( shiftRegNum , 12, 0x3, 0x0 ) #ADC 6
        self.femb.write_reg_bits( shiftRegNum , 14, 0x3, 0x0 ) #ADC 7
        self.femb.write_reg_bits( shiftRegNum , 16, 0x3, 0x0 ) #ADC 8
        self.femb.write_reg_bits( shiftRegNum , 18, 0x3, 0x0 ) #ADC 9
        self.femb.write_reg_bits( shiftRegNum , 20, 0x3, 0x0 ) #ADC 10
        self.femb.write_reg_bits( shiftRegNum , 22, 0x3, 0x0 ) #ADC 11
        self.femb.write_reg_bits( shiftRegNum , 24, 0x3, 0x0 ) #ADC 12
        self.femb.write_reg_bits( shiftRegNum , 26, 0x3, 0x0 ) #ADC 13
        self.femb.write_reg_bits( shiftRegNum , 28, 0x3, 0x0 ) #ADC 14
        self.femb.write_reg_bits( shiftRegNum , 30, 0x3, 0x0 ) #ADC 15

        #FE ASIC 0 phase shifts
        shiftRegNum = int(69)
        self.femb.write_reg_bits( shiftRegNum , 0, 0x3, 0x0 ) #ADC 0
        self.femb.write_reg_bits( shiftRegNum , 2, 0x3, 0x0 ) #ADC 1
        self.femb.write_reg_bits( shiftRegNum , 4, 0x3, 0x0 ) #ADC 2
        self.femb.write_reg_bits( shiftRegNum , 6, 0x3, 0x0 ) #ADC 3
        self.femb.write_reg_bits( shiftRegNum , 8, 0x3, 0x0 ) #ADC 4
        self.femb.write_reg_bits( shiftRegNum , 10, 0x3, 0x0 ) #ADC 5
        self.femb.write_reg_bits( shiftRegNum , 12, 0x3, 0x0 ) #ADC 6
        self.femb.write_reg_bits( shiftRegNum , 14, 0x3, 0x0 ) #ADC 7
        self.femb.write_reg_bits( shiftRegNum , 16, 0x3, 0x0 ) #ADC 8
        self.femb.write_reg_bits( shiftRegNum , 18, 0x3, 0x0 ) #ADC 9
        self.femb.write_reg_bits( shiftRegNum , 20, 0x3, 0x0 ) #ADC 10
        self.femb.write_reg_bits( shiftRegNum , 22, 0x3, 0x0 ) #ADC 11
        self.femb.write_reg_bits( shiftRegNum , 24, 0x3, 0x0 ) #ADC 12
        self.femb.write_reg_bits( shiftRegNum , 26, 0x3, 0x0 ) #ADC 13
        self.femb.write_reg_bits( shiftRegNum , 28, 0x3, 0x0 ) #ADC 14
        self.femb.write_reg_bits( shiftRegNum , 30, 0x3, 0x0 ) #ADC 15

        #FE ASIC 1 phase shifts
        shiftRegNum = int(70)
        self.femb.write_reg_bits( shiftRegNum , 0, 0x3, 0x0 ) #ADC 0
        self.femb.write_reg_bits( shiftRegNum , 2, 0x3, 0x0 ) #ADC 1
        self.femb.write_reg_bits( shiftRegNum , 4, 0x3, 0x0 ) #ADC 2
        self.femb.write_reg_bits( shiftRegNum , 6, 0x3, 0x0 ) #ADC 3
        self.femb.write_reg_bits( shiftRegNum , 8, 0x3, 0x0 ) #ADC 4
        self.femb.write_reg_bits( shiftRegNum , 10, 0x3, 0x0 ) #ADC 5
        self.femb.write_reg_bits( shiftRegNum , 12, 0x3, 0x1 ) #ADC 6
        self.femb.write_reg_bits( shiftRegNum , 14, 0x3, 0x0 ) #ADC 7
        self.femb.write_reg_bits( shiftRegNum , 16, 0x3, 0x0 ) #ADC 8
        self.femb.write_reg_bits( shiftRegNum , 18, 0x3, 0x0 ) #ADC 9
        self.femb.write_reg_bits( shiftRegNum , 20, 0x3, 0x0 ) #ADC 10
        self.femb.write_reg_bits( shiftRegNum , 22, 0x3, 0x0 ) #ADC 11
        self.femb.write_reg_bits( shiftRegNum , 24, 0x3, 0x0 ) #ADC 12
        self.femb.write_reg_bits( shiftRegNum , 26, 0x3, 0x0 ) #ADC 13
        self.femb.write_reg_bits( shiftRegNum , 28, 0x3, 0x0 ) #ADC 14
        self.femb.write_reg_bits( shiftRegNum , 30, 0x3, 0x0 ) #ADC 15

        #FE ASIC 2 phase shifts
        shiftRegNum = int(71)
        self.femb.write_reg_bits( shiftRegNum , 0, 0x3, 0x1 ) #ADC 0
        self.femb.write_reg_bits( shiftRegNum , 2, 0x3, 0x1 ) #ADC 1
        self.femb.write_reg_bits( shiftRegNum , 4, 0x3, 0x1 ) #ADC 2
        self.femb.write_reg_bits( shiftRegNum , 6, 0x3, 0x1 ) #ADC 3
        self.femb.write_reg_bits( shiftRegNum , 8, 0x3, 0x1 ) #ADC 4
        self.femb.write_reg_bits( shiftRegNum , 10, 0x3, 0x1 ) #ADC 5
        self.femb.write_reg_bits( shiftRegNum , 12, 0x3, 0x1 ) #ADC 6
        self.femb.write_reg_bits( shiftRegNum , 14, 0x3, 0x1 ) #ADC 7
        self.femb.write_reg_bits( shiftRegNum , 16, 0x3, 0x1 ) #ADC 8
        self.femb.write_reg_bits( shiftRegNum , 18, 0x3, 0x1 ) #ADC 9
        self.femb.write_reg_bits( shiftRegNum , 20, 0x3, 0x1 ) #ADC 10
        self.femb.write_reg_bits( shiftRegNum , 22, 0x3, 0x1 ) #ADC 11
        self.femb.write_reg_bits( shiftRegNum , 24, 0x3, 0x1 ) #ADC 12
        self.femb.write_reg_bits( shiftRegNum , 26, 0x3, 0x1 ) #ADC 13
        self.femb.write_reg_bits( shiftRegNum , 28, 0x3, 0x1 ) #ADC 14
        self.femb.write_reg_bits( shiftRegNum , 30, 0x3, 0x1 ) #ADC 15

        #FE ASIC 3 phase shifts
        shiftRegNum = int(72)
        self.femb.write_reg_bits( shiftRegNum , 0, 0x3, 0x0 ) #ADC 0
        self.femb.write_reg_bits( shiftRegNum , 2, 0x3, 0x0 ) #ADC 1
        self.femb.write_reg_bits( shiftRegNum , 4, 0x3, 0x0 ) #ADC 2
        self.femb.write_reg_bits( shiftRegNum , 6, 0x3, 0x0 ) #ADC 3
        self.femb.write_reg_bits( shiftRegNum , 8, 0x3, 0x0 ) #ADC 4
        self.femb.write_reg_bits( shiftRegNum , 10, 0x3, 0x0 ) #ADC 5
        self.femb.write_reg_bits( shiftRegNum , 12, 0x3, 0x0 ) #ADC 6
        self.femb.write_reg_bits( shiftRegNum , 14, 0x3, 0x0 ) #ADC 7
        self.femb.write_reg_bits( shiftRegNum , 16, 0x3, 0x0 ) #ADC 8
        self.femb.write_reg_bits( shiftRegNum , 18, 0x3, 0x0 ) #ADC 9
        self.femb.write_reg_bits( shiftRegNum , 20, 0x3, 0x0 ) #ADC 10
        self.femb.write_reg_bits( shiftRegNum , 22, 0x3, 0x0 ) #ADC 11
        self.femb.write_reg_bits( shiftRegNum , 24, 0x3, 0x0 ) #ADC 12
        self.femb.write_reg_bits( shiftRegNum , 26, 0x3, 0x0 ) #ADC 13
        self.femb.write_reg_bits( shiftRegNum , 28, 0x3, 0x0 ) #ADC 14
        self.femb.write_reg_bits( shiftRegNum , 30, 0x3, 0x0 ) #ADC 15
        """
