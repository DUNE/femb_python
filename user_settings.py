from datetime import datetime
class user_editable_settings:
    def __init__(self):
        """
        % CALIBRATION SETTINGS:
        % 	The temp you're saying the run was at.  
        % 	This affects how the analysis looks at the test pulses.
        %	Since both DACs give slightly different values at different-
        %	temperatures.
        """
        self.temp       = "RT"
#        self.extended = True
        self.extended = False #Whether you're using the extended board or not
        self.Quick = False    #Quick sequence that doesn't split the channels and plot.
        self.path = "/home/foodisgood/Developer/Python/single_socket" #Store data
        # Default synchronization settings.  
        # Used in re-sync.
        self.LATCHLOC_reg = 4
        self.CLKPHASE_reg = 6
        if (self.extended == True):
            #cold values
            self.LATCHLOC_data = 0x6060604
            self.CLKPHASE_data = 0x1
            
            #warm values
            #self.LATCHLOC_data = 0x6060606
            #self.CLKPHASE_data = 0x4
        else:
            self.LATCHLOC_data = 0x6050604      # First 2 bits determine shift
            self.CLKPHASE_data = 0x15
        
#       self.chips_to_use = [2,3]
        self.chips_to_use = [0]
        
        """
        % GENERAL SETTINGS:
        """
        #False for regular quad board, True for extended board
        self.chip_num = 0  # maximum number of chips
        self.chn_num = 16  # maximum number of channels 
        #Which IP addresses you gave those 4 sockets
#       self.PC_IP = '192.168.121.20' #WINDOWS PC
        self.PC_IP = '192.168.121.50' #WINDOWS PC
#       self.PC_IP = '10.2.248.66' #MAC LINUX
        self.FPGA_IP = "192.168.121.1"
#        self.FEMB_VER = "Quad Chip Tester with v0x108 Firmware"
        self.FEMB_VER = "Single Socket Chip Tester with v0x108 Firmware"

        self.frame_size = 0x0efb #
    
        self.frequency = .1      # hertz
        self.amplitude = 1.8     # volts
        self.offset = 0.7        # volts
        self.phase_start = 180   # degrees
        
        self.reg10_value = [] # frame size
        self.reg10_value.append(self.frame_size)
        
        """
        % CLOCk:
        % 	setup clock settings.
        """

        self.reg21_value = []

        self.reg22_value = []
        self.reg23_value = []
        self.reg24_value = []
        self.reg25_value = []
        self.reg26_value = []
        self.reg27_value = []
        self.reg28_value = []
        self.reg29_value = []
        self.reg30_value = []
        self.reg31_value = []
        self.reg32_value = []
        self.reg33_value = []

        self.reg34_value = []
        self.reg35_value = []
        self.reg36_value = []

        # Single Socket Board Socket 1
        
        #Course clock settings - definitions
        self.reg21_value.append(1) # INV_RST     <= reg21_p(0)
        self.reg21_value.append(0) # INV_READ    <= reg21_p(1)
        self.reg21_value.append(0) # INV_IDXM    <= reg21_p(2)
        self.reg21_value.append(0) # INV_IDXL    <= reg21_p(3)
        self.reg21_value.append(0) # INV_IDL     <= reg21_p(4)
        self.reg21_value.append(0) # EXT_CLK_DIS <= reg21_p(5)

        self.reg22_value.append(0x00000000) # RESET Offset<= reg22
        self.reg23_value.append(0x00000032) # RESET Width <= reg23
        
        self.reg24_value.append(0x000001d6) # READ Offset <= reg24
        self.reg25_value.append(0x0000000f) # READ Width  <= reg25
        
        self.reg26_value.append(0x000000dc) # IDXM Offset <= reg26
        self.reg27_value.append(0x00000109) # IDXM Width  <= reg27
        
        self.reg28_value.append(0x000001d6) # IDXL Offset <= reg28
        self.reg29_value.append(0x0000000f) # IDXL Width  <= reg29
        
        self.reg30_value.append(0x00000023) # IDL1 Offset <= reg30
        self.reg31_value.append(0x000000b9) # IDL1 Width  <= reg31
        
        self.reg32_value.append(0x000001d1) # IDL2 Offset <= reg32
        self.reg33_value.append(0x0000000f) # IDL2 Width  <= reg33

        self.reg34_value.append(0x0014000D) # pll_STEP0_L <= reg34 (C0 & C1 fine clock control)
        self.reg35_value.append(0x00090012) # pll_STEP1_L <= reg35 (C2 & C3 fine clock control)
        self.reg36_value.append(0x80190004) # pll_STEP2_L <= reg36 (C4 & inversion controls)

        # Quad Board Socket 1
        
#        self.reg10_value.append(0x3030301)
#        self.reg11_value.append(0x90000)
#        self.reg12_value.append(0x3005E)
#        self.reg13_value.append(0x35002C)
#        self.reg14_value.append(0x3005D)
#        self.reg15_value.append(0x12000C)
#        self.reg16_value.append(0x3005D)
#        self.reg17_value.append(0x12000C)
#        self.reg18_value.append(0x6000D)
#        self.reg19_value.append(0x180004)

        # Quad Board Socket 2
        
#        self.reg10_value.append(0x3030301)
#        self.reg11_value.append(0x90000)
#        self.reg12_value.append(0x3005E)
#        self.reg13_value.append(0x35002C)
#        self.reg14_value.append(0x3005D)
#        self.reg15_value.append(0x12000C)
#        self.reg16_value.append(0x3005D)
#        self.reg17_value.append(0x12000C)
#        self.reg18_value.append(0x6000D)
#        self.reg19_value.append(0x180004)
        
        # Quad Board Socket 3
        
#        self.reg10_value.append(0x3030303)
#        self.reg11_value.append(0x90000)
#        self.reg12_value.append(0x3005E)
#        self.reg13_value.append(0x35002C)
#        self.reg14_value.append(0x3005E)
#        self.reg15_value.append(0x250008)
#        self.reg16_value.append(0x3005D)
#        self.reg17_value.append(0x80017)
#        self.reg18_value.append(0x170015)
#        self.reg19_value.append(0x100006)
        
        # Quad Board Socket 4
#        self.reg10_value.append(0x3030303)
#        self.reg11_value.append(0x90000)
#        self.reg12_value.append(0x3005E)
#        self.reg13_value.append(0x35002C)
#        self.reg14_value.append(0x3005E)
#        self.reg15_value.append(0x250007)
#        self.reg16_value.append(0x3005E)
#        self.reg17_value.append(0x170017)
#        self.reg18_value.append(0x6000E)
#        self.reg19_value.append(0x180017)
        
        #Extended Quad Board Socket 1
#        self.reg10_value.append(0x3030303)
#        self.reg11_value.append(0x90000)
#        self.reg12_value.append(0x3005E)
#        self.reg13_value.append(0x35002C)
#        self.reg14_value.append(0x3005E)
#        self.reg15_value.append(0x250008)
#        self.reg16_value.append(0x3005D)
#        self.reg17_value.append(0x180011)
#        self.reg18_value.append(0x180010)
#        self.reg19_value.append(0x100006)
        
        #Extended Quad Board Socket 2
#        self.reg10_value.append(0x3030301)
#        self.reg11_value.append(0x90000)
#        self.reg12_value.append(0x3005E)
#        self.reg13_value.append(0x35002C)
#        self.reg14_value.append(0x3005E)
#        self.reg15_value.append(0x250007)
#        self.reg16_value.append(0x3005D)
#        self.reg17_value.append(0x12000C)
#        self.reg18_value.append(0x6000D)
#        self.reg19_value.append(0x180004)
        
        #Extended Quad Board Socket 3
#        self.reg10_value.append(0x3030303)
#        self.reg11_value.append(0x90000)
#        self.reg12_value.append(0x3005E)
#        self.reg13_value.append(0x35002C)
#        self.reg14_value.append(0x3005E)
#        self.reg15_value.append(0x250008)
#        self.reg16_value.append(0x3005E)
#        self.reg17_value.append(0xD0008)
#        self.reg18_value.append(0x40005)
#        self.reg19_value.append(0x1D0004)
        
        #Extended Quad Board Socket 4        
#        self.reg10_value.append(0x3030303)
#        self.reg11_value.append(0x90000)
#        self.reg12_value.append(0x3005E)
#        self.reg13_value.append(0x35002C)
#        self.reg14_value.append(0x3005E)
#        self.reg15_value.append(0x250008)
#        self.reg16_value.append(0x3005E)
#        self.reg17_value.append(0x90004)
#        self.reg18_value.append(0x5000B)
#        self.reg19_value.append(0x1C0005)
        
        
        self.DLL_LOCATION = "C:\\Users\\protoDUNE\\Desktop\\read_socket\\x64\\Release\\read_socket.dll" #?
        
        
