from scripts.sbnd_femb_meas import FEMB_DAQ
import os
import sys
import gc
import struct
#import copy
from datetime import datetime
import pickle
import time
from ctypes import *
from user_settings import user_editable_settings
settings = user_editable_settings()

class main:
    def loop(self):
        print ("Start")
        self.sbnd.femb_config.femb.init_ports(hostIP = settings.PC_IP, destIP = settings.FPGA_IP)
        
#        board_choice = int(input("What version of the board are you using?  (0 is regular, 1 is extended)"))
#        
#        if (board_choice == 0):
#            settings.extended = False
#        else:
#            settings.extended = True
#            
#        if (settings.extended == True):
#            print ("Uses Version 7 of the ADC chips and Extended Quad Board")
#            
#        else:
#            print ("Uses Version 7 of the ADC chips and Regular Quad Board")
            
        self.sbnd.femb_config.resetFEMBBoard()
        self.sbnd.femb_config.initBoard()
            
        time.sleep(1)
        self.sbnd.femb_config.syncADC()
 #       self.FunctionGenerator = self.sbnd.femb_config.initFunctionGenerator()
#            
#        print ("\n\n-----------------------------------------------------------------------------")
#        print ("BNL Quad Chip Tester Data Collection")
#
#        
#        print ("The directory that data is saved to will be")
#        print (settings.path)
#        try: 
#            os.makedirs(settings.path)
#        except OSError:
#            if os.path.exists(settings.path):
#                pass
#            
#        while(1):
#            self.help_info()
#            raw_in = raw_input("Enter your input\n")
#            if (raw_in == "end"):
#                print("Program ending")
#                break
#                
#            elif (raw_in == "test"):
#                print ("Quad Test...")
#                self.quad_test()
#                break
#                
#            elif (raw_in == "c"):
#                print ("Trying DLL...")
#                self.get_packets_from_c()
#                
#            else:
#                print ("That's not a function")
        
    def quad_test(self):

        folder_path = [[],[],[],[]]
        for i in settings.chips_to_use:
            while(1):
                chip_name = raw_input("Enter the identifier for the chip in socket {}\n".format(i))
                folder_path[i] = (settings.path + chip_name + "\\")
                try: 
                    os.makedirs(folder_path[i])
                    break
                except OSError:
                    if os.path.exists(folder_path[i]):
                        if (raw_input("Folder already exists.  Overwrite? (y/n)\n") == "y"):
                            for the_file in os.listdir(folder_path[i]):
                                file_path = os.path.join(folder_path[i], the_file)
                                if os.path.isfile(file_path):
                                    os.unlink(file_path)
                            pass
                            break

        for i in settings.chips_to_use:
            
            print("Test--> Beginning Channel Alive Test...")
            
            self.sbnd.femb_config.adc_reg.set_adc_chip( chip = i, d=0, pcsr=0, pdsr=0, slp=0, tstin=0,
                 clk = 2, frqc = 1, en_gr = 0, f0 = 0, f1 = 0,
                 f2 = 0, f3 = 0, f4 = 0, f5 = 0, slsb = 0)

            self.sbnd.femb_config.configAdcAsic(False)
            
            self.sbnd.femb_config.fe_reg.set_fe_board(sts=0, snc=1, sg=0, st=0, smn=0, sbf=0, 
                       slk = 0, stb = 0, s16=0, slkh=0, sdc=0, sdacsw2=0, sdacsw1=0, sdac=0)

            self.sbnd.femb_config.configFeAsic(False)
            
            self.sbnd.femb_config.select_chip(i)
            
            full_data = self.sbnd.femb_config.femb.get_data_packets(data_type = "int", num=100, header = False)
            
            organize_data = [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]]
            
            for j in range (len(full_data)/13):
                organize_data[7].append((full_data[(self.BPS*j)+1] & 0x0FFF))
                organize_data[6].append((((full_data[(self.BPS*j)+2] & 0x00FF) << 4) + ((full_data[(self.BPS*j)+1] & 0xF000) >> 12)))
                organize_data[5].append((((full_data[(self.BPS*j)+3] & 0x000F) << 8) + ((full_data[(self.BPS*j)+2] & 0xFF00) >> 8)))
                organize_data[4].append((((full_data[(self.BPS*j)+3] & 0xFFF0) >> 4)))
                organize_data[3].append((full_data[(self.BPS*j)+4] & 0x0FFF))
                organize_data[2].append((((full_data[(self.BPS*j)+5] & 0x00FF) << 4) + ((full_data[(self.BPS*j)+4] & 0xF000) >> 12)))
                organize_data[1].append((((full_data[(self.BPS*j)+6] & 0x000F) << 8) + ((full_data[(self.BPS*j)+5] & 0xFF00) >> 8)))
                organize_data[0].append((((full_data[(self.BPS*j)+6] & 0xFFF0) >> 4)))
                organize_data[15].append((full_data[(self.BPS*j)+7] & 0x0FFF))
                organize_data[14].append((((full_data[(self.BPS*j)+8] & 0x00FF) << 4) + ((full_data[(self.BPS*j)+7] & 0xF000) >> 12)))
                organize_data[13].append((((full_data[(self.BPS*j)+9] & 0x000F) << 8) + ((full_data[(self.BPS*j)+8] & 0xFF00) >> 8)))
                organize_data[12].append((((full_data[(self.BPS*j)+9] & 0xFFF0) >> 4)))
                organize_data[11].append((full_data[(self.BPS*j)+10] & 0x0FFF))
                organize_data[10].append((((full_data[(self.BPS*j)+11] & 0x00FF) << 4) + ((full_data[(self.BPS*j)+10] & 0xF000) >> 12)))
                organize_data[9].append((((full_data[(self.BPS*j)+12] & 0x000F) << 8) + ((full_data[(self.BPS*j)+11] & 0xFF00) >> 8)))
                organize_data[8].append((((full_data[(self.BPS*j)+12] & 0xFFF0) >> 4)))
            
            file_rec = folder_path[i] + "\\" + "Channel_Alive_Results.txt"
            screendisplay = sys.stdout
            sys.stdout = open(file_rec, "w")            
            print ("Input to ADC channels was set to 200 mV, as long as the shorting connectors were there")
            for j in range (16):
                listSum = sum(organize_data[j])
                listLength = len(organize_data[j])
                listAverage = listSum/listLength
                if (listAverage > 1000):
                    print ("Channel {} average is {}, looks like a bad channel!".format(j, listAverage))
                else:
                    print ("Channel {} average is {}, looks good!".format(j, listAverage))
                    
            sys.stdout.close()
            sys.stdout = screendisplay
                
            full_data = None
            organize_data = None
            
        del full_data
        del organize_data
        gc.collect()
                
        print("Test--> Beginning Function Generator Test...")
            
        for i in settings.chips_to_use:

            filename = folder_path[i] + "\\" + "Full_Data.dat"
            
            self.sbnd.femb_config.adc_reg.set_adc_chip( chip = i, d=0, pcsr=1, pdsr=0, slp=0, tstin=1,
                 clk = 2, frqc = 1, en_gr = 0, f0 = 0, f1 = 0, 
                 f2 = 0, f3 = 0, f4 = 0, f5 = 0, slsb = 0)

            self.sbnd.femb_config.configAdcAsic(False)
            
            self.sbnd.femb_config.select_chip(i)
            
            self.get_state(folder_path[i])
            
            print("Test--> Collecting Data for Chip {}...".format(folder_path[i]))
            
            for j in range(10):
                self.FunctionGenerator.write("Initiate1")
                rawdata = None
                rawdata = bytearray()
                time.sleep(0.1)
                #rawdata.extend(self.sbnd.femb_config.femb.get_data_packets(data_type = "bin", num = 1, header = True))
                try:
                    rawdata += ''.join(self.sbnd.femb_config.femb.get_data_packets_check(folder = folder_path[i], num = 65000))
                    break
                except TypeError:
                    if (j > 8):
                        sys.exit("Test--> Missed packets {} times in a row, exiting".format(j))
                    else:
                        print("Test--> Packet missed for the {} time, restarting test for chip {}".format(j+1, i))
                        freq = settings.frequency
                        wait = 1/freq
                        print ("Wait for {} seconds".format(wait))
                        time.sleep(wait)
            
            #str1 = ''.join(list1)
                
            with open(filename,"wb") as f:
                f.write(rawdata) 
                f.close()
            rawdata = None
            del rawdata
            print ("Test--> saved")
            if (settings.Quick == False):
                self.sbnd.analyze.UnpackData(data = filename, config_path = folder_path[i], to_plot = True, 
                                             plot_name = folder_path[i] + "\Data_Plot.jpg")
            gc.collect()
            
#        print("Quad test complete!")
        print("Single socket test complete!")
        #self.sbnd.femb_config.fe_reg.set_fe_board(sts=1, snc=0, sg=2, st=1, smn=0, sbf=1, 
        #                   slk = 0, stb = 0, s16=0, slkh=0, sdc=0, sdacsw2=1, sdacsw1=0, sdac=15, show=False)

        #for i in range(settings.chip_num):
        #    data = self.sbnd.femb_config.femb.get_data_packets(ip = settings.CHIP_IP[i], 
        #                                                       data_type = "int", num = packets, header = False)
        #    print ("Chip {}".format(i))
        #    self.sbnd.analyze.UnpackData(path = "data", data = data)

    def get_packets_from_c(self):
            
        #Load the DLL and hand itback to the main thread
        mydll = ctypes.cdll.LoadLibrary(settings.DLL_LOCATION)
        
        num_of_packets = 5
        udp_port = 32003
        PC_IP1 = settings.PC_IP
        directory = settings.path

        #Python strings need to be converted first to bytes and then to Ctype strings
        PC_IP1_in = ctypes.create_string_buffer(PC_IP1.encode())
        debug_directory = ctypes.create_string_buffer(directory.encode())
        
        #Name of the main function in the DLL
        testFunction = mydll.socket_read_main
        testFunction.restype = c_char_p
        print("Debug information will print in " + repr(debug_directory.value))
        
        #Calls the DLL and passes all these arguments
        result = testFunction(num_of_packets,
                              udp_port,
                              PC_IP1_in,
                              debug_directory
                              )
        print (result)
        print (type(result))
        print (len(result))
        print (bytes(result))
        
        #The DLL has to be released from memory in a convoluted way becaues it's for 64-bit systems
        libHandle = mydll._handle
        del mydll
        ctypes.windll.kernel32.FreeLibrary.argtypes = [ctypes.wintypes.HMODULE]
        ctypes.windll.kernel32.FreeLibrary(libHandle)
        
    def get_state(self, folder):
        config = {'packet_size': 0}
        
        for i in range(64):
            to_save = dict()
            to_save["reg{}".format(i)] = hex(self.sbnd.femb_config.femb.read_reg(i))
            config.update(to_save)
        
        to_save = dict()
        to_save["temp"] = settings.temp
        to_save["chip_num"] = settings.chip_num
        to_save["PC_IP"] = settings.PC_IP
        to_save["FPGA_IP"] = settings.FPGA_IP
        to_save["FEMB_VER"] = settings.FEMB_VER
        to_save["frequency"] = settings.frequency
        to_save["amplitude"] = settings.amplitude
        to_save["offset"] = settings.offset
        to_save["phase_start"] = settings.phase_start
        to_save["chip_name"] = folder
        config.update(to_save)
        
        with open(folder + 'configuration.cfg', 'wb') as f:
            pickle.dump(config, f, pickle.HIGHEST_PROTOCOL)
            
    def help_info(self):
        print ("Type in the function you want to call.")
        print ("Type 'test' to begin the Quad Board test for {} chips".format(settings.chip_num))
        print ("Type 'end' to exit.")
        
    def __init__(self):
            self.sbnd = FEMB_DAQ()
            self.FunctionGenerator = None
            self.BPS = 13 #Bytes per sample.  The one for "0xFACE" and then 12 bytes for 16 channels at 12 bits each.
            
if __name__ == "__main__":
    main().loop()