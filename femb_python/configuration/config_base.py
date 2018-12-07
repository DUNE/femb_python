""" 
Base class for configuration files. These should be considered the 'public'
methods of the config classes, non-configuration code should only use this set
of functions.  
"""

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import
from builtins import int
from builtins import range
from builtins import hex
from builtins import str
from future import standard_library
standard_library.install_aliases()
from builtins import object
from femb_python.generic_femb_udp import FEMB_UDP
from femb_python.test_measurements.quad_FE_Board.detect_peaks import detect_peaks
import time
import matplotlib.pyplot as plt
import numpy as np
import sys
import os

class FEMBConfigError(Exception):
    """Base class exception for femb_python configuration errors"""
    pass

class ConfigADCError(FEMBConfigError):
    """Exception when you can't configure the ADC"""
    pass

class SyncADCError(FEMBConfigError):
    """Exception when you can't sync the ADC"""
    pass

class InitBoardError(FEMBConfigError):
    """Exception when you can't initialize a board"""
    pass

class ReadRegError(FEMBConfigError):
    """Exception when you can't read a register"""
    pass

class FEMB_CONFIG_BASE(object):
    """
    Base class for configuration files. These should be considered the 'public'
    methods of the config classes, non-configuration code should only use this set
    of functions.  
    """

    def __init__(self,exitOnError=True):
        """
        Initialize this class (no board communication here. Should setup self.femb as a femb_udp instance.)
        if exitOnError is false, methods should raise error that subclass FEMBConfigError
        """
        
        self.femb = FEMB_UDP(self.header_size, self.packet_num1, self.packet_num2)
        self.exitOnError=exitOnError
        
        if (self.FEMB == "quadFE"):
            from femb_python.configuration.ASIC_config import FE_CONFIG 
            self.FE_Regs = FE_CONFIG(chip_num = self.NASICS, chn_num = self.NASICCH)
        else:
            print("FEMB_CONFIG_BASE--> No FEMB specified, need to know for FE ASIC SPI!")
        #super(FEMB_CONFIG_BASE, self).__init__()

    def resetBoard(self):
        print ("FEMB_CONFIG_BASE--> Reset FEMB (5 Seconds)")
        self.femb.write_reg ( self.REG_RESET, 1)
        time.sleep(5)
        print ("FEMB_CONFIG_BASE--> Reset FEMB is DONE")

    def initBoard(self, **kwargs):
        """
        Initialize board/asics with default configuration
        """
#        self.resetBoard()
#        self.turnOnAsics()
        
        if hasattr(self, 'REG_MUX_MODE'):
            self.femb.write_reg(self.REG_MUX_MODE, self.default_mux)
        if hasattr(self, 'REG_SS'):
            self.femb.write_reg(self.REG_SS, self.default_ss)
        if hasattr(self, 'REG_TIMEOUT'):
            self.femb.write_reg(self.REG_TIMEOUT, self.default_timeout)
        if hasattr(self, 'REG_SAMPLESPEED'):
            self.femb.write_reg(self.REG_SAMPLESPEED, self.default_sample_speed)
        if hasattr(self, 'REG_FRAMESIZE'): 
            if (self.default_frame_size % 16 != 0):
                self.default_frame_size = 16 * (self.default_frame_size//16)
            self.femb.write_reg(self.REG_FRAMESIZE, self.default_frame_size)
        if (self.has_PCB_DAC == True):
            self.set_PCB_DAC(val=self.default_PCB_DAC, period=self.default_PCB_DAC_TP_Period, shift=self.default_PCB_DAC_TP_Shift, enable=False)
                       
        self.configFeAsic(test_cap="on", base="200mV", gain="14mV", shape="2us", monitor_ch=None, buffer="off", 
                       leak = "500pA", monitor_param = None, s16=None, acdc="dc", test_dac="test_off", dac_value=0)
        self.SPI_array = self.writeFE()
        self.additional_init_commands(**kwargs)
        
        print("Inited board")
        return self.SPI_array
    
    #TODO allow turning individual ASICs on and off
    #Note, on the FE quad board, REG_ON_OFF also returns the status of the buttons being pushed, so it won't always return exactly what you wrote, hence doReadback=False
    def turnOffAsics(self):
        print ("FEMB_CONFIG_BASE--> Turning ASICs off (2 seconds)")
        self.femb.write_reg(self.REG_ON_OFF, 0xF, doReadBack=False)
        #pause after turning off ASICs
        time.sleep(2)
        print ("FEMB_CONFIG_BASE--> ASICs off")
        
    def turnOnAsics(self):
        print ("FEMB_CONFIG_BASE--> Turning ASICs on (2 seconds)")
        self.femb.write_reg(self.REG_ON_OFF,0x0, doReadBack=False)
        #pause after turning on ASICSs
        time.sleep(2)
        print ("FEMB_CONFIG_BASE--> ASICs on")

    def writeADC(self,Adcasic_regs):
        """
        Configure ADCs with given list of registers
        """
        pass

    def writeFE(self):
        if (self.FEMB == "quadFE"):
            #Grab ASIC settings from linked class
            Feasic_regs = self.feasic_regs
            #note which sockets fail        
            config_list = [0,0,0,0]
#            print ("FEMB_CONFIG_BASE--> Config FE ASIC SPI")
            
            #Try 10 times (ocassionally it wont work the first time)
            for k in range(10):
                #Puts the settings in FPGA memory
                for i,regNum in enumerate(range(self.REG_FESPI_BASE,self.REG_FESPI_BASE+len(Feasic_regs),1)):
                    self.femb.write_reg( regNum, Feasic_regs[i])
    #                print (hex(Feasic_regs[i]))

#                print ("FEMB_CONFIG--> Program FE ASIC SPI")
                #Reset, then write twice to the ASICs
                self.femb.write_reg ( self.REG_FEASIC_SPI, self.FEASIC_SPI_RESET, doReadBack = False)
                self.femb.write_reg ( self.REG_FEASIC_SPI, self.FEASIC_SPI_STOP, doReadBack = False)
                time.sleep(.2)
                self.femb.write_reg ( self.REG_FEASIC_SPI, self.FEASIC_SPI_START, doReadBack = False)
                self.femb.write_reg ( self.REG_FEASIC_SPI, self.FEASIC_SPI_STOP, doReadBack = False)
                time.sleep(.2)
                self.femb.write_reg ( self.REG_FEASIC_SPI, self.FEASIC_SPI_START, doReadBack = False)
                self.femb.write_reg ( self.REG_FEASIC_SPI, self.FEASIC_SPI_STOP, doReadBack = False)
                time.sleep(.2)
                
#               print ("FEMB_CONFIG--> Check FE ASIC SPI")
    
                #The FPGA automatically compares the readback to check if it matches what was written.  That result is read back
                #A bit that's zero means the corresponding ASIC didn't write properly
                val = self.femb.read_reg(self.REG_FEASIC_SPI) 
                wrong = False
    
                #check to see if everything went well, and return the status of the 4 chips in the array, so the sequence can notify/skip them
                if (((val & 0x10000) >> 16) != 1 and (0 in self.chips_to_use)):
                    print ("FEMB_CONFIG_BASE--> Something went wrong when programming FE 1")
                    config_list[0] = 0
                    wrong = True
                else:
                    config_list[0] = 1
                    
                if (((val & 0x20000) >> 17) != 1 and (1 in self.chips_to_use)):
                    print ("FEMB_CONFIG_BASE--> Something went wrong when programming FE 2")
                    config_list[1] = 0
                    wrong = True
                else:
                    config_list[1] = 1
                    
                if (((val & 0x40000) >> 18) != 1 and (2 in self.chips_to_use)):
                    print ("FEMB_CONFIG_BASE--> Something went wrong when programming FE 3")
                    config_list[2] = 0
                    wrong = True
                else:
                    config_list[2] = 1
                    
                if (((val & 0x80000) >> 19) != 1 and (3 in self.chips_to_use)):
                    print ("FEMB_CONFIG_BASE--> Something went wrong when programming FE 4")
                    config_list[3] = 0
                    wrong = True
                else:
                    config_list[3] = 1
    
                if (wrong == True and k == 9):
                    try:
                        print ("FEMB_CONFIG_BASE--> SPI_Status is {}").format(hex(val))
                    except AttributeError:
                        print ("FEMB_CONFIG_BASE--> SPI_Status is NOT ok for all chips")
    #                sys.exit("FEMB_CONFIG--> femb_config_femb : Wrong readback. FE SPI failed")
                    
                elif (wrong == False):
#                    print ("FEMB_CONFIG_BASE--> FE ASIC SPI is OK")
                    break
                    
            working_chips = []
            for i,j in enumerate(config_list):
                if (j==1):
                    working_chips.append(i)
                    
            return working_chips
                    
        else:
            print("FEMB_CONFIG_BASE--> No FE writing method when the board is {}".format(self.FEMB))

    def configFeAsic(self,gain,shape,base,leak,test_cap,test_dac,dac_value,buffer,monitor_ch=None,acdc="dc",monitor_param=None,s16=None):

        """
        Gain bits      LARASIC7          LARASIC8
        00                4.7               14
        10                7.8               25
        01                14                7.8
        11                25                4.7 
        """
        if (self.FE_ASIC_VER == 7):
            if gain == "4.7mV": sg = 0
            elif gain == "7.8mV": sg = 2
            elif gain == "14mV": sg = 1      
            elif gain == "25mV": sg = 3
            else: 
                print("FEMB_CONFIG_BASE--> {} is an invalid gain setting".format(gain))
                return None
        if (self.FE_ASIC_VER == 8):
            if gain == "4.7mV": sg = 3
            elif gain == "7.8mV": sg = 1
            elif gain == "14mV": sg = 0       
            elif gain == "25mV": sg = 2
            else:
                print("FEMB_CONFIG_BASE--> {} is an invalid gain setting".format(gain))
                return None
                
        if shape == "0.5us": st = 2
        elif shape == "1us": st = 0
        elif shape == "2us": st = 3        
        elif shape == "3us": st = 1
        else:
            print("FEMB_CONFIG_BASE--> {} is an invalid shaping time setting".format(shape))
            return None

        if leak == "100pA": slk,slkh = 0,1
        elif leak == "500pA": slk,slkh = 0,0
        elif leak == "1nA": slk,slkh = 1,1       
        elif leak == "5nA": slk,slkh = 1,0
        else:
            print("FEMB_CONFIG_BASE--> {} is an invalid leakage current setting".format(leak))
            return None
        
        if test_dac == "test_off": sdacsw1,sdacsw2 = 0,0
        elif test_dac == "test_int": sdacsw1,sdacsw2 = 0,1
        elif test_dac == "test_ext": sdacsw1,sdacsw2 = 1,0
        elif test_dac == "test_meas": sdacsw1,sdacsw2 = 1,1
        else:
            print("FEMB_CONFIG_BASE--> {} is an invalid test pulse/DAC setting".format(test_dac))
            return None
        
        if (test_cap == "on"):
            sts = 1
        elif (test_cap == "off"):
            sts = 0
        else:
            print("FEMB_CONFIG_BASE--> {} is an invalid test capacitor setting".format(test_cap))
            return None
            
        if (base == "200mV"):
            snc = 1
        elif (base == "900mV"):
            snc = 0
        else:
            print("FEMB_CONFIG_BASE--> {} is an invalid baseline setting".format(base))
            return None
            
        if (buffer == "on"):
            sbf = 1
        elif (buffer == "off"):
            sbf = 0
        else:
            print("FEMB_CONFIG_BASE--> {} is an invalid buffer setting".format(buffer))
            return None
            
        sdac = int(dac_value)
        if ((sdac < 0) or (sdac > 32)):
            print("FEMB_CONFIG_BASE--> {} is an invalid internal DAC setting".format(sdac))
            return None
          
        #TODO allow writing of individual channels and chips
        if (monitor_ch != None):
            print("FEMB_CONFIG_BASE--> {} is an invalid channel monitor setting".format(monitor_ch))
            return None
            
        if (acdc == "dc"):
            sdc = 0
        elif (acdc == "ac"):
            sdc = 1
        else:
            print("FEMB_CONFIG_BASE--> {} is an invalid ac/dc setting".format(acdc))
            return None
            
        if ((monitor_param == None) or (monitor_param == "None") or (monitor_param == "off")): stb = 0
        elif monitor_param == "temp": stb = 2
        elif monitor_param == "bandgap": stb = 3
        else:
            print("FEMB_CONFIG_BASE--> {} is an invalid parameter monitoring setting".format(monitor_param))
            return None
            
        if ((s16 == None) or (s16 == "None") or (s16 == "off")):
            s16 = 0
        elif (acdc == "on"):
            s16 = 1
        else:
            print("FEMB_CONFIG_BASE--> {} is an invalid Channel 16 filter setting".format(s16))
            return None
            
        self.feasic_regs = self.FE_Regs.set_fe_board(sts=sts, snc=snc, sg=sg, st=st, smn=0, sbf=sbf, 
                       slk = slk, stb = stb, s16=s16, slkh=slkh, sdc=sdc, sdacsw2=sdacsw2, sdacsw1=sdacsw1, sdac=sdac)

    def configAdcAsic(self,enableOffsetCurrent=None,offsetCurrent=None,testInput=None,
                            freqInternal=None,sleep=None,pdsr=None,pcsr=None,
                            clockMonostable=None,clockExternal=None,clockFromFIFO=None,
                            sLSB=None,f0=None,f1=None,f2=None,f3=None,f4=None,f5=None):
        """
        Configure ADCs
          enableOffsetCurrent: 0 disable offset current, 1 enable offset current
          offsetCurrent: 0-15, amount of current to draw from sample and hold
          testInput: 0 digitize normal input, 1 digitize test input
          freqInternal: internal clock frequency: 0 1MHz, 1 2MHz
          sleep: 0 disable sleep mode, 1 enable sleep mode
          pdsr: if pcsr=0: 0 PD is low, 1 PD is high
          pcsr: 0 power down controlled by pdsr, 1 power down controlled externally
          Only one of these can be enabled:
            clockMonostable: True ADC uses monostable clock
            clockExternal: True ADC uses external clock
            clockFromFIFO: True ADC uses digital generator FIFO clock
          sLSB: LSB current steering mode. 0 for full, 1 for partial (ADC7 P1)
          f0, f1, f2, f3, f4, f5: version specific
        """
        if clockMonostable and clockExternal:
            raise Exception("Only clockMonostable, clockExternal, OR, clockFromFIFO can be true, clockMonostable and clockExternal were set true")
        if clockMonostable and clockFromFIFO:
            raise Exception("Only clockMonostable, clockExternal, OR, clockFromFIFO can be true, clockMonostable and clockFromFIFO were set true")
        if clockExternal and clockFromFIFO:
            raise Exception("Only clockMonostable, clockExternal, OR, clockFromFIFO can be true, clockExternal and clockFromFIFO were set true")

    def selectChipChannel(self,chip,chn):
        """
        asic is chip number 0 to 7
        chan is channel within asic from 0 to 15
        hsmode: if 0 then streams all channels of a chip, 
                if 1 only te selected channel
                defaults to 1. Not enabled for all firmware versions
        """
        if (chip < 0 ) or (chip > self.NASICS ):
            print ("FEMB_CONFIG_BASE -> Error in get_data_chipXchnX: Chip must be between 0 and {}".format(self.NASICS))
            return
            
        if (chn < 0 ) or (chn > (self.NASICCH-1)):
            print ("FEMB_CONFIG_BASE -> Error in get_data_chipXchnX: Channel must be between 0 and {}".format(self.NASICCH-1))
            return
          
        #TODO this is only for the specific way the FE quad board works
        chip_int = int(chip + 1)
        chn_int = int(chn)
        self.femb.write_reg(self.REG_CH_SEL, chn_int + (chip_int << 8))
        
    def setInternalPulser(self,pulserEnable,pulseHeight):
        """
        pulserEnable = 0 for disable, 1 for enable
        pulseHeight = 0 to 31
        """
        pass

    #Returns boolean array of the chips that pass.  If a chips is not part of "working chips", its place will be empty in the array
    #chip_id[0] is the index of the chip, where it sits on the board (spot 0, 1, 2, 3 etc...)
    #chip_id[1] is its name (A2567, A2568, etc...)
    def syncADC(self, **kwargs):
        print ("FEMB_CONFIG_BASE--> Start sync ADC")
        outputdir = kwargs["outputdir"]
        #Chips that have failed SPI or have been disabled by the GUI wont be tested
        working_chips = kwargs["working_chips"]
        return_array = []
        for i in range(self.NASICS):
            return_array.append([])
        if ((self.FEMB == "quadFE") and (self.adc == "LTC2314")):
            #Don't ask me why, but you need to set the channel at this point for it to output the right data on the quad board
            self.selectChipChannel(chip = 0, chn = 1)
            for chip in working_chips:
                #"chiplist" is an argument if the function call came from the sumatra runner i.e. the full suite of tests are being run, and there's a timestamp and permanent directory
                #If there's no "chiplist", this has been called by the GUI as a check to get the live trace tester to make sure everything's working.  In that case, output the results to a temporary directory in the test root
                if ("chiplist" in kwargs):
                    chiplist = kwargs["chiplist"]
                    datadir = kwargs["datadir"]
                    chip_id = chiplist[chip]
                    self.savefigpath = os.path.join(datadir,chip_id[1],outputdir,"syncplots")
                else:
                    chip_id = [chip,chip]   
                    self.savefigpath = os.path.join(outputdir,str(chip_id[1]))
                    
                os.makedirs(self.savefigpath)
                self.sync_prep_output()
                print ("FEMB_CONFIG_BASE--> Trying to sync ADC {}({})".format(chip_id[0],chip_id[1]))
                output_result = True
                for chn in range(self.NASICCH):
                    #Tests if it's synchronized, returns True if it is
                    unsync = self.testUnsync(chip = chip_id, chn = chn)
                    if unsync != True:
                        print ("FEMB_CONFIG_BASE--> Chip {}({}), Chn {} not synced, try to fix".format(chip_id[0],chip_id[1], chn))
                        response = self.fixUnsync_outputADC(chip = chip_id, chn = chn)
                        if (response != True):
                            output_result = False
                            print ("FEMB_CONFIG_BASE--> Something is wrong with Chip {}({}), Chn {}".format(chip_id[0],chip_id[1], chn))
                if (output_result == True):
                    print ("FEMB_CONFIG_BASE--> ADC {}({}) synced!".format(chip_id[0],chip_id[1]))

                data = self.get_data_chipX(chip = chip_id[0], packets = 5, tagged = True)
                plot_path = os.path.join(self.savefigpath,"syncplots")
                print("FEMB_CONFIG_BASE--> Printing synchronization plot for Chip {}({})".format(chip_id[0],chip_id[1]))
                self.plot.plot(data = data, plot_name = plot_path, 
                title_name = "Pulses for synchronization: Gain = 14 mv/fC, Peaking Time = 2 us, Buffer off, "
                             "DAC Pulse at {} \nPeaks should be between {} and {}, Baseline should be between "
                             "{} and {}".format(hex(self.sync_peak_height), self.sync_peak_min, 
                               self.sync_peak_max, self.sync_baseline_min, self.sync_baseline_max))
                
                print ("FEMB_CONFIG_BASE--> Trying to sync test ADC {}({})".format(chip_id[0],chip_id[1]))
                
                self.sync_prep_test(chip = chip_id[0])
                test_result = True
                unsync = self.testUnsync(chip = chip_id, chn = chn)
                if unsync != True:
                    print ("FEMB_CONFIG_BASE--> Chip {}({}) (test ADC) not synced, try to fix".format(chip_id[0],chip_id[1]))
                    response = self.fixUnsync_testADC(chip = chip_id)
                    if (response != True):
                        test_result = False
                        print ("FEMB_CONFIG_BASE--> Something is wrong with Chip {}({}) (test ADC)".format(chip_id[0],chip_id[1]))
                if (test_result == True):
                    print ("FEMB_CONFIG_BASE--> Chip {}({}) (test ADC) synced!".format(chip_id[0],chip_id[1]))
                    
                if (output_result and test_result):
                    return_array[chip_id[0]] = True
                else:
                    return_array[chip_id[0]] = False
                
            outputfile = os.path.join(outputdir,"syncresults.txt")
            with open(outputfile, 'w') as f:
                print ("FEMB_CONFIG_BASE--> Final Shift Settings: ")
                f.write("FEMB_CONFIG_BASE--> Final Shift Settings: \n")
                for reg in range(65, 69, 1):
                    value = self.femb.read_reg(reg)
                    f.write("Register {}: {}\n".format(reg, hex(value)))
        
                print ("FEMB_CONFIG_BASE--> Final Phase Settings: ")
                f.write("FEMB_CONFIG_BASE--> Final Phase Settings: \n")
                for reg in range(69, 73, 1):
                    value = self.femb.read_reg(reg)
                    f.write("Register {}: {}\n".format(reg, hex(value)))
                
                for reg in range(73,77,1):
                    value = self.femb.read_reg(reg)
                    f.write("Register {}: {}\n".format(reg, hex(value)))
                
                self.femb.write_reg(17, 0)
                    
                print ("FEMB_CONFIG_BASE--> Sync test done!")
                
            return return_array
                
    def testUnsync(self, chip, chn, index=0):
        #Get some packets of data
        self.selectChipChannel(chip = chip[0], chn = chn)
        data = list(self.get_data_chipXchnX_tagged(chip = chip[0], chn = chn, packets = self.sync_desired_peaks, data_format = "counts"))
#        f.write("Chn{} feed index is {}\n".format(chn,feed_index))
        #Find some peaks
        peaks_index = detect_peaks(x=data, mph=self.sync_peak_min, mpd=100)
#        f.write("Peaks are {}\n".format(peaks_index))
        #Make sure you have more than 0 peaks (so it's not flat) and less than the maximum 
        #(if there's no peak, the baseline will give hundreds of peaks)
        #If it's bad, print it, so we see (must enable inline printing for iPython)
#        figure_data = self.plot.quickPlot(data)
#        ax = figure_data[0]
#        for j in peaks_index:
#            y_value = data[j]
#            ax.scatter(j/2, y_value, marker='x')
#            
#        ax.set_ylabel('mV')
#        ax.set_title("Error")
#        ax.title.set_fontsize(30)
#        for item in ([ax.xaxis.label, ax.yaxis.label] +ax.get_xticklabels() + ax.get_yticklabels()):
#            item.set_fontsize(20)
#        plt.show()
#        plt.close()
        if (len(peaks_index) != self.sync_desired_peaks):
            print ("FEMB_CONFIG_BASE--> Chip {}({}), Channel {} has {} peaks!".format(chip[0],chip[1], chn, len(peaks_index)))
            figure_data = self.plot.quickPlot(data)
            ax = figure_data[0]
            for j in peaks_index:
                y_value = data[j]
                ax.scatter(j/2, y_value, marker='x')
                
            ax.set_ylabel('ADC Counts')
            ax.set_title("FEMB_CONFIG_BASE: Chip {}({}), Chn {} has {} peaks".format(chip[0],chip[1], chn, len(peaks_index)))
            ax.title.set_fontsize(30)
            for item in ([ax.xaxis.label, ax.yaxis.label] +ax.get_xticklabels() + ax.get_yticklabels()):
                item.set_fontsize(20)
            plt.savefig(os.path.join(self.savefigpath,"chip{}chn{}peaks{}_index{}.jpg".format(chip[1],chn,len(peaks_index),index)))
            plt.close()
            
            print("FEMB_CONFIG_BASE--> Chip {}({}), Channel {} has {} peaks!\n".format(chip[0],chip[1], chn, len(peaks_index)))
#            print (peaks_index)
            return False
            
        #So that function before only gives you the X locations of where the peaks are.  Let's get the Y values from that
        peaks_value = []
        for i in peaks_index :
            peaks_value.append(data[i])
#        print("Peak values are {}\n".format(peaks_value))
#        print ("Chip {}({}), Channel {} has peak values {}".format(chip_id[0],chip_id[1], chn, peaks_value))
        #Check if the peak is at the wrong height (happens when it's not synced, the peak will be havled or doubled)
        for peak in peaks_value:
            if ((peak < self.sync_peak_min) or (peak > self.sync_peak_max)):
                print ("FEMB_CONFIG_BASE--> Chip {}({}), Chn {} has a peak that's {}".format(chip[0],chip[1], chn, peak))
                figure_data = self.plot.quickPlot(data)
                ax = figure_data[0]
                for j in peaks_index:
                    y_value = data[j]
                    ax.scatter(j/2, y_value, marker='x')
                    
                ax.set_ylabel('mV')
                ax.set_title("FEMB_CONFIG_BASE: Chip {}({}), Chn {} has a peak that's {}".format(chip[0],chip[1], chn, peak))
                ax.title.set_fontsize(30)
                for item in ([ax.xaxis.label, ax.yaxis.label] +ax.get_xticklabels() + ax.get_yticklabels()):
                    item.set_fontsize(20)
                plt.savefig(os.path.join(self.savefigpath,"chip{}chn{}peak{}.jpg".format(chip,chn,peak)))
                plt.close()
                return False 
        #Check if the baseline is right (this also gets halved and doubled with unsynced ADCs) (avoid the peak to grab a middle section)
        try:
            baseline_area_start = peaks_index[0] + 15
            baseline_area_end = peaks_index[1] - 15
        except IndexError:
            baseline_area_start = 15
            baseline_area_end = 185
        baseline_data = data[baseline_area_start : baseline_area_end]
        baseline = np.mean(baseline_data)
        if (isinstance(baseline, np.float64) != True):
            print("FEMB_CONFIG_BASE--> Baseline is {}".format(type(baseline)))
        if ((baseline < self.sync_baseline_min) or (baseline > self.sync_baseline_max)):
            print ("FEMB_CONFIG_BASE--> Chip {}({}), Chn {} has a baseline that's {}".format(chip[0],chip[1], chn, baseline))
            figure_data = self.plot.quickPlot(data)
            ax = figure_data[0]
            for j in peaks_index:
                y_value = data[j]
                ax.scatter(j/2, y_value, marker='x')
                
            ax.set_ylabel('mV')
            ax.set_title("Chip {}({}), Chn {} has a baseline that's {}".format(chip[0],chip[1], chn, baseline))
            ax.title.set_fontsize(30)
            for item in ([ax.xaxis.label, ax.yaxis.label] +ax.get_xticklabels() + ax.get_yticklabels()):
                item.set_fontsize(20)
            plt.savefig(os.path.join(self.savefigpath,"chip{}chn{}baseline{}.jpg".format(chip,chn,baseline)))
            plt.close()
            return False
                
        #check if the pulse has high frequency noise
        #Giving errors.  There's gotta be a simpler way of checking for high frequency noise, maybe just seeing if there's any sample that are X far away from baseline, or looking at histogram distribution?
#        total_high_freq_noise = 0
#        for peak in peaks_index:
#            dt = 0
#            t_high = 0
#            t_low = 0
#            print("Length of data is {}".format(len(data)))
#            while True:
#                dt = dt + 1
#                #check to see if we have reached the neighborhood of the baseline
#                print("peak is {}".format(peak))
#                print("dt is {}".format(dt))
#                if abs(data[peak+dt] - baseline) < self.sync_baseline_r and not t_high:
#                    t_high = peak+dt
#                if abs(data[peak-dt] - baseline) < self.sync_baseline_r and not t_low:
#                    t_low = peak-dt
#                if t_high and t_low:
#                    break
#                if dt == 100:
#                    if not t_high:
#                        t_high = peak + 100
#                    if not t_low:
#                        t_low = peak - 100
#                    break
#            pulse_data = data[t_low:t_high]
#            pulse_data_fft = np.fft.fft(pulse_data)[:int(len(pulse_data)/2)]
#            total_high_freq_noise = total_high_freq_noise + np.sum(abs(pulse_data_fft[5:].real))
#        avg_high_freq_noise = total_high_freq_noise / len(peaks_index)
#        
#        if avg_high_freq_noise > self.sync_high_freq_noise_max:
#            if saveresults:
#                print("FEMB CONFIG--> Chip {}({}), Chn {} has lots of high frequency noise".format(chip_id[0],chip_id[1], chn))
#                figure_data = self.plot.quickPlot(pulse_data)
#                ax = figure_data[0]
#                    
#                ax.set_ylabel('mV')
#                ax.set_title("Chip {}({}), Chn {} has lots of high frequency noise".format(chip_id[0],chip_id[1], chn))
#                ax.title.set_fontsize(30)
#                for item in ([ax.xaxis.label, ax.yaxis.label] +ax.get_xticklabels() + ax.get_yticklabels()):
#                    item.set_fontsize(20)
#                plt.savefig(os.path.join(savefigpath,"chip{}chn{}high_freq.jpg"))
#                plt.close()
#                return False
#            
        #TODO make the title update with changes
        
        return True
            
    #Shifts through all possible delay and phase options, checking to see if each one fixed the issue

    def fixUnsync_outputADC(self, chip, chn):
        self.selectChipChannel(chip = chip[0], chn = chn)
        
        shift_reg = chip + 65
        phase_reg = chip + 69
#        sample_reg = 75 + (chip//2)
        
        #Get the initial setting you don't disturb the other channels
        init_shift = self.femb.read_reg(shift_reg)
        init_phase = self.femb.read_reg(phase_reg)

        #Because Python can't have a friggin NAND or XOR function that works right at the bitwise level, this is how we get the bitmask
        #This will find the 2 bits in the register that correspond to the channel you want to change.  Say it's channel 2
        #In binary, it makes 0b00000000000000000000000000110000
        #Then inverts it to  0b11111111111111111111111111001111
        #Now you AND that with the initial result to get the initial values WITHOUT the channel you want to change
        #Now you can bitshift your desired setting to that empty space with zeroes, like say you wanted to write a 0b10,
        #It would be 0b100000.  Then add that to whatever the result of the initial values AND mask was.  Boom, you've done it.
        init_mask = (0x3 << (2 * chn))
        neg_mask = 0
        for i in range(32):
            FF_bit = (0xFFFFFFFF >> i) & 0x1
            test_bit = (init_mask >> i) & 0x1
            if (FF_bit != test_bit):
                result_bit = 1
            else:
                result_bit = 0
            neg_mask = neg_mask + (result_bit << i)
        
        #There are 16 possible sync permutations for every ADC
#        for sample_clock in range(2):
#            value = (sample_clock << chn) << (16 * (chip%2))
#            print ("Clock setting for chip {}, channel {} is {}".format(chip, chn, hex(value)))
#            self.femb.write_reg(sample_reg, value)
        for shift in range(4):
            for phase in range(4):
                
                shift_setting = shift << (2 * chn)
                init_shift_with_mask = init_shift & neg_mask
                final_shift = shift_setting + init_shift_with_mask
                
#                print ("Shift is {}".format(shift))
#                print ("phase is {}".format(phase))
#                print ("Negative mask is {}".format(bin(neg_mask)))                
#                print ("Initial reading is {}".format(bin(init_shift)))
#                print ("The new setting is {}".format(bin(shift_setting)))
#                print ("Making space for the new setting is {}".format(bin(init_shift_with_mask)))
#                print ("Adding together is {}".format(bin(final_shift)))
                
                self.femb.write_reg(shift_reg, final_shift)
                
                phase_setting = phase << (2 * chn)
                init_phase_with_mask = init_phase & neg_mask
                final_phase = phase_setting + init_phase_with_mask
                
                self.femb.write_reg(phase_reg, final_phase)
                
                #See if this new setting fixed it
                index = (shift+4) + phase
                print("Trying shift {} phase {} index {}".format(shift,phase,index))
                unsync = self.testUnsync(chip = chip, chn = chn,index = index)
                if unsync == True:
                    #print ("FEMB_CONFIG--> Chip {}, Chn {} fixed!".format(chip, chn))
                    print("FEMB_CONFIG_BASE--> Chip {}, Chn {} fixed!\n".format(chip, chn))
                    return True

        print ("FEMB_CONFIG_BASE--> ADC SYNC process failed for Chip {}, Channel {}".format(chip, chn))
        self.femb.write_reg(shift_reg, init_shift)
        self.femb.write_reg(phase_reg, init_phase)
        return False
    
    def get_fw_version(self):
        if hasattr(self, 'REG_FW_VER'):
            resp = self.femb.read_reg(self.REG_FW_VER)
        else:
            print("FEMB_CONFIG_BASE--> Configuration has no firmware version registers")
            return None
            
        return resp
        
    #Get data in a variety of ways.  You can even pre-convert it to mV!
    def get_data_chipXchnX(self, chip, chn, packets = 1, data_format = "counts"):
        if (chn < 0) or (chn > self.NASICCH):
            print ("FEMB CONFIG -> Error in get_data_chipXchnX: Channel must be between 0 and 15, or -1 for all channels")
            return
        
        if (chip < 0) or (chip > self.NASICS):
            print ("FEMB CONFIG -> Error in get_data_chipXchnX: Chip must be between 0 and {}, but it's {}".format(self.chip_num, chip))
            return

        self.selectChipChannel(chip = chip, chn = chn)
            
        if (data_format == "bin"):
            data = self.femb.get_data_packets(data_type = "bin", num = packets, header = True)

        data = self.femb.get_data_packets(data_type = "int", num = packets, header = False)
        
        if (data_format == "mV"):
            for i in range (len(data)):
                data[i] = data[i] * (0.0018 / 16384)
                
        elif (data_format == "V"):
            for i in range (len(data)):
                data[i] = data[i] * (1.8 / 16384)
                
        return data
        
    def get_data_chipXchnX_tagged(self, chip, chn, packets = 1, data_format = "counts"):
        traces = 0
        loops = 0
        data_to_return = []
        while (traces < packets):
            loops = loops + 1
            data = list(self.get_data_chipXchnX(chip, chn, packets = 5, data_format = "counts"))
            found_trace = False
            for i in range(len(data)):
                #if (data[i] > self.adc_full_scale):
                #Positive pulse
                if (data[i] & (0b10 << 14)):
                    if (len(data[i:]) > self.pulse_spacing):
                        enough_data = True
                    else:
                        enough_data = False
                        break
                    
                    additional_pulse = False
                    for j in range(i+1,i+self.pulse_spacing,1):
                        if (data[j] & (0b10 << 14)):
                            additional_pulse = True
                            break
                        
                    if ((additional_pulse == False) and (enough_data == True)):
                        data[i] = data[i] & self.adc_full_scale
                        data_to_send = []
                        data_to_send.extend(list(data[i:i+self.pulse_spacing]))
                        found_trace = True
                        break
            if (found_trace):
                traces = traces + 1
                data_to_return.extend(list(data_to_send))
            if (loops > (packets*10)):
                print("FEMB_CONFIG_BASE--> Channel {}, Not enough traces found".format(chn))
                break
            
        if (data_format == "mV"):
            for i in range (len(data_to_return)):
                data_to_return[i] = data_to_return[i] * (0.0018 / 16384)
                
        elif (data_format == "V"):
            for i in range (len(data_to_return)):
                data_to_return[i] = data_to_return[i] * (1.8 / 16384)
            
        return data_to_return
        
    #Get a whole chip's worth of data
    def get_data_chipX(self, chip, packets = 1, data_format = "counts", tagged = False):

        #chip_data = [chip, [],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]]
        chip_data = [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]]
        for chn in range(16):
            for i in range(packets):
     #           chip_data[chn + 1].extend(list(self.get_data_chipXchnX(chip, chn, packets = 1, data_format = data_format)))
                if (tagged == False):
                    chip_data[chn].extend(list(self.get_data_chipXchnX(chip, chn, packets = 1, data_format = data_format)))
                else:
                    chip_data[chn].extend(list(self.get_data_chipXchnX_tagged(chip, chn, packets = packets, data_format = data_format)))
        return chip_data
        
    #TODO Allow turning on/off some DACs
    def set_PCB_DAC(self,val=None,period=None,shift=None,enable=None):
        if (val != None):
            int_val = int(val)
            if ((int_val > 0) or (int_val < self.PCB_DAC_VAL_MAX)):
                self.femb.write_reg(self.REG_PCB_DAC_VAL, int_val)
                
                self.femb.write_reg(self.REG_PCB_DAC_SET, self.PCB_DAC_STOP)
                self.femb.write_reg(self.REG_PCB_DAC_SET, self.PCB_DAC_START)
                self.femb.write_reg(self.REG_PCB_DAC_SET, self.PCB_DAC_STOP)
            else:
                print("FEMB_CONFIG_BASE--> PCB_DAC is trying to set a value of {} (max value is {}".format(int_val, self.PCB_DAC_VAL_MAX))
                
        if (enable != None):
            if (enable == True):
                self.femb.write_reg(61, 0x0)
            elif (enable == False):
                self.femb.write_reg(61, 0xF)
                
        if ((period!=None) and (shift!=None)):
            self.femb.write_reg(self.REG_PCB_DAC_TIMING, (shift << 16) + period)