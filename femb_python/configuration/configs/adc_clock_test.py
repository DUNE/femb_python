#!/usr/bin/env python33

import sys 
import time
import visa
from visa import VisaIOError
from femb_python.test_measurements.adc_clock_test.scripts.femb_udp_cmdline import FEMB_UDP
from femb_python.test_measurements.adc_clock_test.scripts.adc_asic_reg_mapping import ADC_ASIC_REG_MAPPING
from femb_python.test_measurements.adc_clock_test.scripts.fe_asic_reg_mapping import FE_ASIC_REG_MAPPING
from femb_python.test_measurements.adc_clock_test.user_settings import user_editable_settings
settings = user_editable_settings()

class FEMB_CONFIG:

    def __init__(self):
        #declare board specific registers
        self.REG_RESET = 0
        self.REG_ASIC_RESET = 1
        self.REG_ASIC_SPIPROG = 2
        self.REG_ADCSPI_BASE = 0x200        #512 Dec
        self.REG_ADCSPI_RDBACK_BASE = 0x250 #592 Dec
        self.REG_HS = 17
#        self.REG_TEST_PULSE = 5
#        self.REG_TEST_PULSE_FREQ = 500
#        self.REG_TEST_PULSE_DLY = 80
#        self.REG_TEST_PULSE_AMPL = 0 % 32
        self.REG_EN_CALI = 16
        self.ADC_TESTPATTERN=[0x12,0x345,0x678,0xf1f,0xad,0xc01,0x234,0x567,0x89d,0xeca,0xff0,0x123,0x456,0x789,0xabc,0xdef]

        #initialize FEMB UDP object
        self.femb = FEMB_UDP()
        self.adc_reg = ADC_ASIC_REG_MAPPING()
        self.fe_reg = FE_ASIC_REG_MAPPING() 
        
        self.REG_LATCHLOC1_4_data = settings.LATCHLOC_data
        self.REG_CLKPHASE_data = settings.CLKPHASE_data
        
        self.WIB_RESET = 1
        
        self.BPS = 13 #Bytes per sample
        self.selected_chip = 0
        self.selected_chn = None

    def resetFEMBBoard(self): #cp 1/17/18
        #
        #   resetFEMBBoard()
        #       sends a 1 to register 1 for "instantaneous" ASIC reset.
        #       sends a 0 to register 1 to ensure reset is not locked in.
        #
        #       procedure:
        #           line 29: FPGA to ASIC reset
        #           line 30: wait 5 ms
        #           line 31: FPGA to ASIC disable reset
        #
        
        print (" FEMB_CONFIG--> Reset FEMB (10 seconds) --")
        #Reset FEMB system
        self.femb.write_reg ( self.REG_RESET, 1)
        time.sleep(5.)
        self.femb.write_reg ( self.REG_RESET, 0)
        time.sleep(2.)
        print (" FEMB_CONFIG--> Reset FEMB is DONE\n")
        

    def initBoard(self):
        """
        % initBoard()
        % 	set up default registers. 
        % 	first wave in setting clock settings.
        """
        
        print ("FEMB_CONFIG--> initBoard() -> Initialize FEMB --")
        
        # Frame size is multiple of 13, so 0xFACE is consistently the first 2 bytes.
        frame_size = settings.frame_size
        if (frame_size%13 != 0):
            frame_size = 13 * (frame_size//13)
            
        self.femb.write_reg(10, frame_size)
        time.sleep(0.1)
    
        if (self.femb.read_reg(10) != frame_size):
            sys.exit("FEMB_CONFIG--> initBoard() -> Frame Size not set correctly, something wrong with FPGA communication")
        
        print ("FEMB_CONFIG--> initBoard() -> Chip tester version {}".format(hex(self.femb.read_reg(0x101))))

        # Set to WIB Mode and start by reading out chip 1
        # Channel Setting is irrelevant in WIB mode
        self.femb.write_reg(8, 0x80000001)                  # WIB_MODE   <= reg8_p(0)
        self.femb.write_reg(7, 0x80000000)                  # CHN_select <= reg7_p(7 downto 0)

        """ SHIFT DATA BUS """
        # LATCH_LOC_0 <= reg4_p(7 downto 0)
        self.femb.write_reg(settings.LATCHLOC_reg, settings.LATCHLOC_data)
        
        """ SHIFT DATA BUS """
        # CLK_selectx <= reg6_p(7 downto 0)
        self.femb.write_reg(settings.CLKPHASE_reg, settings.CLKPHASE_data)
        
#        self.femb.write_reg( 9, 0)

        # Write Coarse Clock Control
        self.femb.write_reg(21, settings.reg21_value[0])
        self.femb.write_reg(21, settings.reg21_value[1])
        self.femb.write_reg(21, settings.reg21_value[2])
        self.femb.write_reg(21, settings.reg21_value[3])
        self.femb.write_reg(21, settings.reg21_value[4])
        self.femb.write_reg(21, settings.reg21_value[5])

        self.femb.write_reg(22, settings.reg22_value[0])    # RESET Offset      
        self.femb.write_reg(23, settings.reg23_value[0])    # RESET Width
        
        self.femb.write_reg(24, settings.reg24_value[0])    # READ Offset
        self.femb.write_reg(25, settings.reg25_value[0])    # READ Width
        
        self.femb.write_reg(26, settings.reg26_value[0])    # IDXM Offset
        self.femb.write_reg(27, settings.reg27_value[0])    # IDXM Width
        
        self.femb.write_reg(28, settings.reg28_value[0])    # IDXL Offset
        self.femb.write_reg(29, settings.reg29_value[0])    # IDXL Width
        
        self.femb.write_reg(30, settings.reg30_value[0])    # IDL1 Offset
        self.femb.write_reg(31, settings.reg31_value[0])    # IDL1 Width
                                                            
        self.femb.write_reg(32, settings.reg32_value[0])    # IDL2 Offset
        self.femb.write_reg(33, settings.reg33_value[0])    # IDL2 Width

        #Fine Control
        self.femb.write_reg(34, settings.reg34_value[0])    # C0 & C1 fine clock settings   
        self.femb.write_reg(35, settings.reg35_value[0])    # C2 & C3 fine clock settings
        self.femb.write_reg(36, settings.reg36_value[0])    # C2 & C3 fine clock settings

        #set default value to FEMB ADCs
        #clk = 2 is external
        #clk = 0 is internal
        self.adc_reg.set_adc_board( d=0, pcsr=0, pdsr=0, slp=0, tstin=1,
                 clk = 0, frqc = 1, en_gr = 0, f0 = 0, f1 = 0, 
                 f2 = 0, f3 = 0, f4 = 0, f5 = 1, slsb = 0) # set to internal 1/31/18 cp
                 
        self.femb.write_reg ( self.REG_ASIC_SPIPROG, 0x30)
        self.femb.write_reg ( self.REG_ASIC_SPIPROG, 0)
        self.configAdcAsic()
        
        print (" FEMB_CONFIG--> initBOARD() -> Initialize FEMB is DONE\n")
        
    def syncADC(self):
        #
        #   syncADC()
        #
        #       procedures:
        #           1.  set channel/global registers ensure F5=1, so
        #               test data is selected and pipelined. Just as 
        #               in labview. 
        #           2.  configure ADC ASIC 
        #           3.
        #
        
        print ("\n FEMB_CONFIG--> Start sync ADC--")


        self.select_chn(1) # channel 0 & write clocks
        self.select_chn(3) # channel 0 & write clocks
        self.adc_reg.set_adc_global(chip = settings.chip_num, f5 = 1) # Test DATA
        self.configAdcAsic()
            
        print (" FEMB_CONFIG --> syncADC() -> Test ADC {}".format(settings.chip_num))
        print (" FEMB_CONFIG --> syncADC() -> self.adc_reg.set_adc_global() \n")
#        for i in range(10,20,1):
#        print ("Register {} {}".format(i, hex(self.femb.read_reg(i))))
            
        unsync = self.testUnsyncNew(settings.chip_num)
        if unsync != True:
            print (" FEMB_CONFIG --> ADC {} not synced, try to fix".format(settings.chip_num))
            response = self.fixUnsyncNew(a)
            if (response != True):
                sys.exit (" FEMB_CONFIG --> ADC {} could not sync".format(settings.chip_num))
        elif (unsync == True):
            print ("FEMB_CONFIG--> ADC {} synced!".format(settings.chip_num))
                
            self.adc_reg.set_adc_global(chip = settings.chip_num, f5 = 1)
            self.configAdcAsic()
            
        self.REG_LATCHLOC1_4_data = self.femb.read_reg( settings.LATCHLOC_reg) 
        self.REG_CLKPHASE_data    = self.femb.read_reg( settings.CLKPHASE_reg)
        print ("FEMB_CONFIG--> Final Latch latency " + str(hex(self.REG_LATCHLOC1_4_data)))
        print ("FEMB_CONFIG--> Final Phase Shift " + str(hex(self.REG_CLKPHASE_data)))
        self.FinalSyncCheck()
        print ("FEMB_CONFIG--> ADC passed Sync Test!")

    def initFunctionGenerator(self):
        rm = visa.ResourceManager()
        """
        try:
            #keysight = rm.open_resource('USB0::0x0957::0x5707::MY53802435::0::INSTR')
            keysight = rm.open_resource(u'USB0::2391::22279::MY53802422::0::INSTR')
            print ("Keysight Initialize--> Instrument Connected")
        except VisaIOError:
            print ("Keysight Initialize--> Exact system name not found")
            keysight = rm.open_resource(rm.list_resources()[0])
        
        #Sets the self.instrument object in "GPIB_FUNCTIONS" to the 
        #connected instrument, this makes it very easy to reference later
        time.sleep(0.1)
        keysight.write("Source1:Apply:Triangle {},{},{}".format(settings.frequency,settings.amplitude,settings.offset))
        keysight.write("Output1:Load 50")
        #keysight.write("Output1:Load INFINITY")
        keysight.write("Source1:Burst:Mode Triggered")
        keysight.write("Source1:Burst:Ncycles 1")
        keysight.write("Source1:Burst:Phase {}".format(settings.phase_start))
        keysight.write("Source1:Burst:State ON")
        keysight.write("Initiate1:Continuous OFF")
        
        return keysight
        """
    def configAdcAsic(self): #cp 1/29/18 #helper
        """
        config()
        
        """   
        print("FEMB_CONFIG -> configAdcAsic() --")    
    
        Adcasic_regs = self.adc_reg.REGS
        #ADC ASIC SPI registers
        self.femb.write_reg ( self.REG_ASIC_SPIPROG, 0x40)
        self.femb.write_reg ( self.REG_ASIC_SPIPROG, 0)
        time.sleep(0.01)
        self.femb.write_reg ( self.REG_ASIC_SPIPROG, 0x20)
        self.femb.write_reg ( self.REG_ASIC_SPIPROG, 0)
        time.sleep(0.01)
        self.femb.write_reg ( self.REG_ASIC_SPIPROG, 0x40)
        self.femb.write_reg ( self.REG_ASIC_SPIPROG, 0)
        time.sleep(0.01)

        for k in range(10):            
            i = 0
            for regNum in range(self.REG_ADCSPI_BASE,self.REG_ADCSPI_BASE+len(Adcasic_regs),1):
                    self.femb.write_reg( regNum, Adcasic_regs[i])
                    i = i + 1
                    
            # Program ADC ASIC SPI
            self.femb.write_reg ( self.REG_ASIC_SPIPROG, 0)
            time.sleep(.05)
            self.femb.write_reg ( self.REG_ASIC_SPIPROG, 1)
            time.sleep(.05)
            self.femb.write_reg ( self.REG_ASIC_SPIPROG, 1)
            time.sleep(.05)
            #self.femb.write_reg ( self.REG_ASIC_SPIPROG, 0)

            # Check ADC ASIC SPI
            readback_regs = []
            i = 0
            for regNum in range(self.REG_ADCSPI_RDBACK_BASE,self.REG_ADCSPI_RDBACK_BASE+len(Adcasic_regs),1):
                readback_regs.append(self.femb.read_reg(regNum))
                #print ( "femb_config_sbnd.py -> configAdcAsic() -> readback reg: " + str(hex(regNum)) + " from base: " + str(hex(Adcasic_regs[i])))
                i = i + 1
            
            i=0
            for i in range (0,len(readback_regs),1): #Why is this reading out extra adc asic registers?
                if (Adcasic_regs[i] != readback_regs[i]):
                    print ("\t FEMB_CONFIG --> CONFIG() ERROR -> configAdcAsic() -> Sent Adcasic_reg not correct = " + str(hex(Adcasic_regs[i])) + " , rb_reg = " + str(hex(readback_regs[i])) )
                else:
                    continue
                    #print ("femb_config_sbnd.py -> configAdcAsic() -> Adcasic_reg correct = " + str(hex(Adcasic_regs[i])) + " , rb_reg = " + str(hex(readback_regs[i])) )
            
#            val = self.femb.read_reg ( self.REG_ASIC_SPIPROG ) 
            wrong = False
#
#            if (((val & 0x10000) >> 16) != 1):
#                #print ("FEMB_CONFIG--> Something went wrong when programming ADC 1")
#                wrong = True
                
#            if (((val & 0x40000) >> 18) != 1):
#                #print ("FEMB_CONFIG--> Something went wrong when programming ADC 2")
#                wrong = True
                
#            if (((val & 0x100000) >> 20) != 1):
#                #print ("FEMB_CONFIG--> Something went wrong when programming ADC 3")
#                wrong = True
                
#            if (((val & 0x400000) >> 22) != 1):
#                #print ("FEMB_CONFIG--> Something went wrong when programming ADC 4")
#                wrong = True

            if (wrong == True and k == 9):
                print ("\tFEMB_CONFIG--> CONFIG() -> SPI_Status")
                print (hex(val))
                sys.exit("\tFEMB_CONFIG--> CONFIG() -> femb_config_femb : Wrong readback. ADC SPI failed")
                return
                
            elif (wrong == 0): 
                print ("\tFEMB_CONFIG--> CONFIG() -> ADC ASIC SPI is OK")
                break
            #else:
                #print ("FEMB_CONFIG--> Try {}, since SPI response was {}".format(k + 2, hex(val)))

    def FinalSyncCheck(self):
        #
        #   FinalSyncCheck()
        #
        #       procedures:   
        #           line 337: set chip [determine which chip is being sync'd]
        #           line 339: set global register [send test data from PC to FPGA (where is this data going?)  F5=1  
        #           line 340: write SPI (wtf is SPI?)
        
        print ("FEMB_CONFIG--> Final sync check to make sure")
        for a in settings.chips_to_use:
            
            self.adc_reg.set_adc_global(chip = a, f5 = 1)
            self.configAdcAsic()
            
            # quad board settings:
            #self.select_chip(chip = a)
            
            # single board settings:
            #select_chip is not necessary

            badSync = 0
            for ch in range(0,16,1):
                for test in range(0,100,1):
                    data = self.get_data_chipXchnX(chip = a, chn = ch, packets = 1)
                    if (len(data) == 0):
                        print ("FEMB_CONFIG--> Sync response bad.  Exiting...")
                        return 1
                    for samp in data[0:len(data)]:
                        if samp != self.ADC_TESTPATTERN[ch]:
                            badSync = 1 
                            print ("FEMB_CONFIG--> Chip {} chn {} looking for {} but found {}".format(
                                    a, ch, hex(self.ADC_TESTPATTERN[ch]), hex(samp)))
                        if badSync == 1:
                                break
                    #print("time after checking the sample {}".format(time.time()))
                    if badSync == 1:
                        break
                #print("time after checking 100 samples {}".format(time.time()))
                if badSync == 1:
                    self.femb.write_reg( 9, 1)
                    sys.exit("FEMB_CONFIG--> Failed final check looking at channel test values")

            self.configAdcAsic()
            print ("FEMB_CONFIG--> Chip {} recieved the correct test values!".format(a))
        
            resp = self.testUnsyncNew(a)
            if (resp == False):
                self.femb.write_reg(9, 1)
                sys.exit("FEMB_CONFIG--> Sync failed in the final check")                
                
        self.adc_reg.set_adc_global(chip = a, f5 = 0)
#        for i in range (100):
#            sync_status = self.femb.read_reg(self.REG_ASIC_SPIPROG) >> 24
#            if ((sync_status & 0x3F) != 0):
#
#                if (i == 99):
#                    print ("FEMB_CONFIG--> Register 2 giving back a sync error")
#                    print ("Sync status is {}".format(hex(sync_status)))
#                    sys.exit("Done with trying")
#
#                self.configAdcAsic(False)
#                
#            else:
#                print ("FEMB_CONFIG--> No Sync error through Register 2 check: ({})!".format(hex(sync_status)))
#                break
            
    def testUnsyncNew(self, chip):

        print("\n FEMB_CONFIG --> testUnsyncNew() -> chip = {} --".format(chip))        
        
        adcNum = int(chip)
        if (adcNum < 0 ) or (adcNum > 3 ):
            print (" FEMB_CONFIG --> testUnsyncNew() -> Invalid asic number, must be between 0 and 3")
            return
            
        for j in range(100):    #reset sync error
            self.femb.write_reg(11, 1) # ERROR_RESET <= reg11_p(0)
            time.sleep(0.01)
            self.femb.write_reg(11, 0) # ERROR_RESET <= reg11_p(0)
            time.sleep(0.01)
            
            if (chip == 0):
                conv_error = self.femb.read_reg(12)     # reg12_i => x"" & CONV_ERROR 
                header_error = self.femb.read_reg(13)   # reg13_i => HDR2_ERROR & HDR1_ERROR 
                
#            elif (chip == 1):
#                conv_error = self.femb.read_reg(50)    # reg50_i => x"0000" & CONV_ERROR_1
#                header_error = self.femb.read_reg(51)  # reg51_i => HDR2_ERROR_2 & HDR1_ERROR_2
#            elif (chip == 2):
#                conv_error = self.femb.read_reg(52)
#                header_error = self.femb.read_reg(53)
#            elif (chip == 3):
#                conv_error = self.femb.read_reg(54)
#                header_error = self.femb.read_reg(55)
            
            error = False
            
            if (conv_error != 0): # CONV_ERROR exists
                print (" FEMB_CONFIG --> testUnsyncNew() -> Convert error({})!  Trial {}".format(hex(conv_error),j))
                error = True
            else:
                print (" FEMB_CONFIG --> testUnsyncNew() -> No Convert Error ({})  Trial {}!".format(hex(conv_error),j)) #convert = 0
                
            if (header_error != 0): # HEADER_ERROR exists
                print (" FEMB_CONFIG --> testUnsyncNew() -> Header error ({})!".format(hex(header_error)))
                error = True
            else:
                print (" FEMB_CONFIG --> testUnsyncNew() -> No Header Error({})!  Trial {}".format(hex(header_error),j)) #not finding header
                
            if (error == False): #break loop if no error found
                print (" FEMB_CONFIG --> testUnsyncNew() -> Correct on Loop {}  Trial {}".format(j,j))
                break
                #return True
            elif (j > 30):
                print (" FEMB_CONFIG --> testUnsyncNew() -> Convert error({})!  Trial {}".format(hex(conv_error),j))
                print (" FEMB_CONFIG --> testUnsyncNew() -> Header error ({})!  Trial {}".format(hex(header_error),j))
                #sync_status = self.femb.read_reg(self.REG_ASIC_SPIPROG) >> 24
                #print ("FEMB_CONFIG--> Register 2 Sync status is {}".format(hex(sync_status)))
                return False
            else:
                self.configAdcAsic(False)
                #print ("Loop {}".format(j))
           
        for ch in range(0,16,1):
            for test in range(0,200,1):
                data = self.get_data_chipXchnX(chip = adcNum, chn = ch, packets = 1)#issue here?
                #print("unsyncNew data -> {}".format(data))
                if (len(data) == 0):
                    print (" FEMB_CONFIG--> testUnsyncNew() -> Sync response didn't come in")
                    return False
                for samp in data[0:len(data)]:
                    if samp != self.ADC_TESTPATTERN[ch]:
                        print (" FEMB_CONFIG --> testUnsyncNew() -> Chip {} chn {} looking for {} but found {}".format(
                                adcNum, ch, hex(self.ADC_TESTPATTERN[ch]), hex(samp)))
                        return False
                        
        return True

            
    def fixUnsyncNew(self, adc):

        print("\n femb_config_sbnd.py -> fixUnsyncNew() -> adc = " + str(adc) + "\n")        
        
        adcNum = int(adc)
        if (adcNum < 0) or (adcNum > 3):
                print ("FEMB_CONFIG--> femb_config_femb : testLink - invalid asic number")
                return

        initLATCH1_4 = self.femb.read_reg( settings.LATCHLOC_reg)
        initPHASE = self.femb.read_reg( settings.CLKPHASE_reg)
        
        #loop through sync parameters
        shiftMask = (0xFF << 8*adcNum)
        initSetting = (initLATCH1_4 & shiftMask) >> (8*adcNum)
        print ("FEMB_CONFIG--> First testing around default value of {}".format(initSetting))
        for phase in range(0,4,1):
            clkMask = (0x3 << (adcNum * 2))
            testPhase = ( (initPHASE & ~(clkMask)) | (phase << (adcNum * 2)) ) 
            self.femb.write_reg( settings.CLKPHASE_reg, testPhase)
            #print ("Init Setting is {}".format(hex(initSetting)))
            #print ("Will test {}, {}, and {}".format(initSetting - 1, initSetting, initSetting + 1))
            for shift in range(initSetting - 1,initSetting + 2,1):
                print ("\n\tfemb_config_sbnd.py -> fixUnsyncNew -> This time, we're testing {}\n".format(shift))
                testShift = ( (initLATCH1_4 & ~(shiftMask)) | (shift << 8*adcNum) )
                self.femb.write_reg( settings.LATCHLOC_reg, testShift)
                print ("FEMB_CONFIG--> Trying to sync Chip {} with Latch Lock:{} and Phase:{}".format(adcNum, 
                       hex(testShift), hex(testPhase)))
                       
                #test link
                unsync = self.testUnsyncNew(adcNum)
                if unsync == True :
                    print ("FEMB_CONFIG--> ADC {} synchronized".format(adc))
                    self.REG_LATCHLOC1_4_data = testShift
                    self.REG_CLKPHASE_data = testPhase
                    return True
            #Then try all settings
        print ("FEMB_CONFIG--> Now testing the rest of them")
        for phase in range(0,4,1):
            clkMask = (0x3 << (adcNum * 2))
            testPhase = ( (initPHASE & ~(clkMask)) | (phase << (adcNum * 2)) ) 
            self.femb.write_reg( settings.CLKPHASE_reg, testPhase)
            #First test latch lock settings close to default values
            shiftMask = (0xFF << 8*adcNum)
            initSetting = initLATCH1_4 & shiftMask
            for shift in range(0,16,1):
                testShift = ( (initLATCH1_4 & ~(shiftMask)) | (shift << 8*adcNum) )
                self.femb.write_reg( settings.LATCHLOC_reg, testShift)
                print ("FEMB_CONFIG--> Trying to sync Chip {} with Latch Lock:{} and Phase:{}".format(adcNum, 
                       hex(testShift), hex(testPhase)))
                       
                #test link
                unsync = self.testUnsyncNew(adcNum)
                if unsync == True :
                    print ("FEMB_CONFIG--> ADC {} synchronized".format(adc))
                    self.REG_LATCHLOC1_4_data = testShift
                    self.REG_CLKPHASE_data = testPhase
                    return True
        #if program reaches here, sync has failed
        print ("FEMB_CONFIG--> ADC SYNC process failed for ADC # " + str(adc))
        return False
    
    def select_chn(self, chn): 
        """
        % select_chn()
        %       This function is used in sending instructions to fpga to select chip.
        %       There is not an option to select a chip for single socket boards. 
        %       This function is mostly relevent for using on quad board.
        %       This function is used to output the desired clock settings correlated to the    
        %       'selected chip'
        %       Assume 16 channels
        %
        %       [quad board:]
        %           clock reg values [10-43]   
        % 
        %       [single board:]
        %           clock reg values [21-33]
        """
        print("\t FEMB_CONFIG//select_chn()")
        if (chn < 0 ) or (chn > settings.chn_num):
            print ("\t FEMB_CONFIG//select_chn()//Error: Chn must be between 0 and {}".format(self.chn_num))
            return
        """ quad board remains...
        self.femb.write_reg(9, 1)		  # STOP_ADC <= reg9_p (quad board)
        time.sleep(0.01)                          # WAIT
        self.femb.write_reg(3, 0x80000001 + chip) # CHP_SELECT <= reg3_p(7 downto 0) (quad board) 
        time.sleep(0.01)                          # WAIT
        self.femb.write_reg(9, 0)		  # STOP_ADC <= reg9_p (quad board)
        time.sleep(0.01)                          # WAIT
        self.femb.write_reg(47, 1)                # ERROR_RESET <= reg47_p (quad board)
        time.sleep(0.01)                          # WAIT
        self.femb.write_reg(47, 0)                # ERROR_RESET <= reg47_p (quad board)
        """
        # STOP ADC: TRUE ???
        time.sleep(0.01)                         # WAIT
        self.femb.write_reg(7, 0x00000001 + chn) # CHN_SELECT <= reg7(7 downto 0)
        time.sleep(0.01)                         # WAIT
	# STOP ADC: FALSE ???
	# WAIT
        self.femb.write_reg(11, 1)               # CHN_SELECT <= reg11(0)
        time.sleep(0.01)                         # WAIT
        self.femb.write_reg(11, 0)               # CHN_SELECT <= reg11(0)

        self.selected_chn = chn # originally self.selected_chip?? what is it used for?
        if (self.femb.read_reg(7) != 0x00000001 + chn):
            print ("\t FEMB CONFIG --> select_chn() -> Error - chip not chosen correctly!")
            print ("\t Should be ".format(hex(0x00000001 + chn)))
            print ("\t It is {}".format(hex(self.femb.read_reg(7))))
            
        to_add = 0
        """ quad board remains...
        if (settings.extended == True):
            to_add = 4

        self.femb.write_reg(10, settings.reg10_value[chip + to_add]) #INV_RST_ADC1 <= reg10_p(0)
							             #INV_READ_ADC1<= reg10_p(1)
        #Course Control Quad Board
        self.femb.write_reg(11, settings.reg11_value[chip + to_add])
        self.femb.write_reg(12, settings.reg12_value[chip + to_add])
        self.femb.write_reg(13, settings.reg13_value[chip + to_add])
        self.femb.write_reg(14, settings.reg14_value[chip + to_add])
        self.femb.write_reg(15, settings.reg15_value[chip + to_add])
        self.femb.write_reg(16, settings.reg16_value[chip + to_add])
        
        #Fine Control Quad Board
        self.femb.write_reg(17, settings.reg17_value[chip + to_add])
        self.femb.write_reg(18, settings.reg18_value[chip + to_add])
        self.femb.write_reg(19, settings.reg19_value[chip + to_add])
        self.femb.write_reg(19, settings.reg19_value[chip + to_add])
        self.femb.write_reg(19, 0x80000000 + settings.reg19_value[chip + to_add])
        """
        self.femb.write_reg( settings.CLKPHASE_reg, 0xFF)
        self.femb.write_reg( settings.CLKPHASE_reg, self.REG_CLKPHASE_data)
        
        time.sleep(0.01)


    def get_data_chipXchnX(self, chip, chn, packets = 1):
        
        if (chn < -1 ) or (chn > settings.chn_num ):
            print ("FEMB CONFIG --> get_data_chipXchnX() -> Error: Channel must be between 0 and 15, or -1 for all channels")
            return
        
        if (chip < 0 ) or (chip > settings.chip_num ):
            print ("FEMB CONFIG --> get_data_chipXchnX() -> Error: Chip must be between 0 and {}".format(self.chip_num))
            return

        k = 0
        for i in range(10):
            
            data = self.femb.get_data_packets(data_type = "int", num = packets, header = False)
            
            try:
                if (k > 0):
                    print ("FEMB CONFIG --> Now doing another test")
                    print (hex(data[0]))
                    print (data[0] == 0xFACE)
                    print (data[0] != 0xFACE)
                if (data[0] != 0xFACE):
                #If FACE isn't the first 2 bytes, turn WIB mode off and then on and try again
                    self.femb.write_reg(8,0) # Turn WIB Mode Off
                    time.sleep(0.01)
                    self.femb.write_reg(8,1) # Turn WIB Mode On
                    time.sleep(0.01)
                    
                # quad board settings:
#                    self.select_chip(chip) #tells fpga which chip information to provide
#                    self.femb.write_reg(3, chip+1)  # CHP_Select <= reg_3p(7-0)
#                                                    # CHN_Select <= reg_3p(15-0)
#                                                    # WIB_Mode <= reg_3p(31)
                # single board settings:
                    self.femb.write_reg(7, chn)      # CHN_select <= reg7_p(7-0)       
                    time.sleep(0.001)

                    if (k > 8):
                        print ("FEMB CONFIG --> Error in get_data_chipXchnX: Packet format error")
                        #print (hex(data[0]))
                        #print (data)
                        return None
                    else:
                        print ("FEMB CONFIG --> Error in get_data_chipXchnX: Packet format error, trying again...")
                        print ("k = {}".format(k))
                        print (data[0:13])
                        print (hex(data[0]))
                        print ("FEMB CONFIG --> Hey: {}".format(data[0] == 0xFACE))
                        k += 1
                else:
                    break
            except IndexError:
                print ("FEMB CONFIG --> Something was wrong with the incoming data")
                print (data)
            
        test_length = len(data)
        
#        if ((test_length % self.BPS) != 0):
#            print ("FEMB CONFIG -> Error in get_data_chipXchnX: Irregular packet size")
#            print (data)
#            return None
        
        full_samples = test_length // self.BPS
        
        chn_data = []
        
        for i in range (full_samples):
            if (chn == 7):
                chn_data.append(data[(self.BPS*i)+1] & 0x0FFF)
            if (chn == 6):
                chn_data.append(((data[(self.BPS*i)+2] & 0x00FF) << 4) + ((data[(self.BPS*i)+1] & 0xF000) >> 12))
            if (chn == 5):
                chn_data.append(((data[(self.BPS*i)+3] & 0x000F) << 8) + ((data[(self.BPS*i)+2] & 0xFF00) >> 8))
            if (chn == 4):
                chn_data.append(((data[(self.BPS*i)+3] & 0xFFF0) >> 4))
            if (chn == 3):
                chn_data.append(data[(self.BPS*i)+4] & 0x0FFF)
            if (chn == 2):
                chn_data.append(((data[(self.BPS*i)+5] & 0x00FF) << 4) + ((data[(self.BPS*i)+4] & 0xF000) >> 12))
            if (chn == 1):
                chn_data.append(((data[(self.BPS*i)+6] & 0x000F) << 8) + ((data[(self.BPS*i)+5] & 0xFF00) >> 8))
            if (chn == 0):
                chn_data.append(((data[(self.BPS*i)+6] & 0xFFF0) >> 4))
            if (chn == 15):
                chn_data.append(data[(self.BPS*i)+7] & 0x0FFF)
            if (chn == 14):
                chn_data.append(((data[(self.BPS*i)+8] & 0x00FF) << 4) + ((data[(self.BPS*i)+7] & 0xF000) >> 12))
            if (chn == 13):
                chn_data.append(((data[(self.BPS*i)+9] & 0x000F) << 8) + ((data[(self.BPS*i)+8] & 0xFF00) >> 8))
            if (chn == 12):
                chn_data.append(((data[(self.BPS*i)+9] & 0xFFF0) >> 4))
            if (chn == 11):
                chn_data.append(data[(self.BPS*i)+10] & 0x0FFF)
            if (chn == 10):
                chn_data.append(((data[(self.BPS*i)+11] & 0x00FF) << 4) + ((data[(self.BPS*i)+10] & 0xF000) >> 12))
            if (chn == 9):
                chn_data.append(((data[(self.BPS*i)+12] & 0x000F) << 8) + ((data[(self.BPS*i)+11] & 0xFF00) >> 8))
            if (chn == 8):
                chn_data.append(((data[(self.BPS*i)+12] & 0xFFF0) >> 4))
            if (chn == -1):
                return (data)
            
        return chn_data
    
    

