# -*- coding: utf-8 -*-
"""
Created on Fri Jun  2 11:50:17 2017

@author: vlsilab2
"""

import os
import struct
import matplotlib.pyplot as plt
plt.switch_backend('agg')
import glob
import re
import sys
import pickle
from user_settings import user_editable_settings
settings = user_editable_settings()



class Data_Analysis:
    
    def Seperate_Packets(self, path):
        
        self.screendisplay = sys.stdout
        sys.stdout = open(path + self.debug_file_name, "a+")

        
        search_path = [path + "*Chip0_Packet*.dat", path + "*Chip1_Packet*.dat", 
                       path + "*Chip2_Packet*.dat", path + "*Chip3_Packet*.dat"]


        new_path = path + "\Separated_Packets\\"
        try: 
            os.makedirs(new_path)
        except OSError:
            if os.path.exists(new_path):
                pass
            
        for the_file in os.listdir(new_path):
            file_path = os.path.join(new_path, the_file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(e)
        
        print ("Separating packets in " + path + " for " + str(settings.chip_num) + " chips assuming that there's " +\
               str(settings.packets_per_file) + " packets to a file.  The new separated packets will be in " + new_path)
        
        numbers = re.compile(r'(\d+)')
        def numericalSort(value):
            parts = numbers.split(value)
            parts[1::2] = map(int, parts[1::2])
            return parts
        
        for i in range(settings.chip_num):
            packet_counter = 0
            relevant_files = sorted(glob.glob(search_path[i]), key=numericalSort)
            for infile in relevant_files:
                fileinfo  = os.stat(infile)
                filelength = fileinfo.st_size
                shorts = filelength/2

                each_packet = int(filelength / settings.packets_per_file)

                ideal_packet_indices = []
                for j in range(settings.packets_per_file):
                    ideal_packet_indices.append(each_packet * j)

                with open(infile, 'rb') as f:
                    raw_data = f.read(filelength)

                    f.close()
                    

                    
                full_data = struct.unpack_from(">%dH"%shorts,raw_data)

                if ((len(full_data)%(2*settings.packets_per_file)) != 0):
                    print ("WARNING: " + infile + " doesn't have a properly divisible file length")
                    
                
                real_packet_indices = []
                for m in re.finditer(self.start_of_packet, raw_data):
                    real_packet_indices.append(m.start())
                    
                    
                if (len(real_packet_indices) != settings.packets_per_file):
                    print ("WARNING: Found {} different chips in {} instead of the expected {}.".format(
                            real_packet_indices, infile, settings.packets_per_file))

                error = 0
                for j in range(len(real_packet_indices)):
                    
                    if ((ideal_packet_indices[j]) != (real_packet_indices[j])):
                        print ("WARNING: The beginning of Packet {} in {} is not where it should be!".format(j,infile))
                        
                        print ("It should be at {} but for some reason it's at {}.".format(hex(ideal_packet_indices[j]),
                                                hex(real_packet_indices[j])))
                        
                        data_fraction_test = []
                        
                        for k in range(len(real_packet_indices)):
                            if (k < (len(real_packet_indices) - 1)):
                                data_fraction_test.append(raw_data[real_packet_indices[k]:real_packet_indices[k+1]])
                            else:
                                data_fraction_test.append(raw_data[real_packet_indices[k]:])
                            
                        test_packet_indices = []
                        error = 1

                if (error == 1):
                    for k in range(len(data_fraction_test)):
                        for m in re.finditer(self.start_of_sample, data_fraction_test[k]):
                            test_packet_indices.append(m.start())
                            
                        print ("{} samples found for packet {} in {}".format(len(test_packet_indices), k, infile))
                        test_packet_indices = []
                            
                
                
                for j in range(len(real_packet_indices)):

                    if (j < (len(real_packet_indices) - 1)):
                        data_fraction = raw_data[real_packet_indices[j]:real_packet_indices[j+1]]
                    else:
                        data_fraction = raw_data[real_packet_indices[j]:]

                    
                    packet_number_bytes = data_fraction[8:12]
                    packet_number_int = struct.unpack_from(">1I",packet_number_bytes)

                    
                    filename = new_path + "Chip{}_Packet{}.dat".format(i,packet_number_int[0])
                    with open(filename,"wb") as f:
                        f.write(data_fraction) 
                        f.close()
                        
                packet_counter += 1
                if (packet_counter%self.notice1_every == 0):
                    sys.stdout.close()
                    sys.stdout = self.screendisplay
                    print ("Chip {}: {}/{} packet bundles separated".format(i, packet_counter, len(relevant_files)))
                    self.screendisplay = sys.stdout
                    sys.stdout = open(path + self.debug_file_name, "a+")
            sys.stdout.close()
            sys.stdout = self.screendisplay
            print ("Chip {} packet bundles fully separated".format(i))
            self.screendisplay = sys.stdout
            sys.stdout = open(path + self.debug_file_name, "a+")
        Data_Analysis.Missing_Packet_Check(self, new_path, 1)
        sys.stdout.close()
        sys.stdout = self.screendisplay
    
        return new_path
    
    def Missing_Packet_Check(self, path, packets_per_file):
        
        search_path = [path + "*Chip0_Packet*.dat", path + "*Chip1_Packet*.dat", 
                       path + "*Chip2_Packet*.dat", path + "*Chip3_Packet*.dat"]
        
        chip_specific_files = [[],[],[],[]]
        
        numbers = re.compile(r'(\d+)')
        def numericalSort(value):
            parts = numbers.split(value)
            parts[1::2] = map(int, parts[1::2])
            return parts
        
        for i in range(settings.chip_num):
            for infile in sorted(glob.glob(search_path[i]), key=numericalSort):
                chip_specific_files[i].append(infile)
            packets = (len(chip_specific_files[i]))
            packet_num_array = []
            count = 0
            for j in range(packets):
                filename = chip_specific_files[i][j]
                with open(filename, 'rb') as f:
                    raw_data = f.read(12)
                    f.close()
                packet_num_array.append(struct.unpack_from(">3I",raw_data)[2])
                count += 1
                if (count%self.notice2_every ==0):
                    sys.stdout.close()
                    sys.stdout = self.screendisplay
                    print ("Chip {}: {}/{} packets collected".format(i, count, packets))
                    self.screendisplay = sys.stdout
                    sys.stdout = open(path + self.debug_file_name, "a+")

            skips = 0
            
            sys.stdout.close()
            sys.stdout = self.screendisplay
            print ("Analyzing Chip {}".format(i))
            self.screendisplay = sys.stdout
            sys.stdout = open(path + self.debug_file_name, "a+")
            
            for k in range(len(packet_num_array) - 1):
                first_number = packet_num_array[k]
                second_number = packet_num_array[k+1]
                if (second_number != first_number + packets_per_file):
                    print ("Chip {} skips from packet {} to packet {}, index {} to {}"
                           .format(i, first_number, second_number, k, k+1))
                    skips += 1
            if (skips == 0):
                print ("No packet skips for Chip {}!".format(i))
            else:
                print ("Chip {} had {} packet skips".format(i, skips))
                
            sys.stdout.close()
            sys.stdout = self.screendisplay
            print ("Chip {} analyzed".format(i))
            self.screendisplay = sys.stdout
            sys.stdout = open(path + self.debug_file_name, "a+")

    def UnpackData(self, data, config_path, to_plot, plot_name):
        
        with open(config_path + 'configuration.cfg', 'rb') as f:
                config = pickle.load(f)
            
        packet_size = config['packet_size']


        fileinfo  = os.stat(data)
        filelength = fileinfo.st_size
    

        with open(data, 'rb') as f:
            raw_data = f.read(filelength)
            f.close()
            
        FACE_check = struct.unpack_from(">%dH"%(self.BPS + 8),raw_data)
        
        face_index = -1
        for i in range (self.BPS):
            if (FACE_check[i] == 0xFACE):
                face_index = i
                break
            
        if (face_index == -1):
            print ("UnpackData--> FACE not detected")
            print_tuple = []
            for i in range(len(FACE_check)):
                print_tuple.append(hex(FACE_check[i]))
            
            print (print_tuple)
            return
        
        print ("UnpackData--> FACE detected at {}, Checking for skipped packets (2 min)".format(face_index))
        
        if (filelength % packet_size != 0):
            print ("UnpackData--> Irregular file size {} given packet size {}".format(hex(filelength), (packet_size)))
            sys.exit("Error!")
            
        packets = filelength / packet_size
        
        packet_number_prev = 0
        full_data = []
        
        for i in range(packets):
            single_packet = raw_data[i*packet_size : (i+1) * packet_size]
            packet_number = struct.unpack_from(">1I",single_packet)[0]
            if ((packet_number != (packet_number_prev + 1)) and (packet_number_prev != 0)):
                sys.exit("UnpackData--> Skipped Packet from {} to {}!".format(hex(packet_number_prev), hex(packet_number)))
            else:
                packet_number_prev = packet_number
                unpacked_shorts = list(struct.unpack_from(">%dH"%((packet_size-16)/2),single_packet[16:]))
                for j in range(len(unpacked_shorts)):
                    full_data.append(unpacked_shorts[j])

        del raw_data

        data_length = len(full_data)
        if (data_length % self.BPS != 0):
            sys.exit("UnpackData--> Something's wrong, the pure data list is not a multiple of 13, it's {}".format(data_length))

        full_samples = data_length / self.BPS
        
        print ("UnpackData--> Seperating data into channels (2 min)")
        
        ch0 = []
        ch1 = []
        ch2 = []
        ch3 = []
        ch4 = []
        ch5 = []
        ch6 = []
        ch7 = []
        ch8 = []
        ch9 = []
        ch10 = []
        ch11 = []
        ch12 = []
        ch13 = []
        ch14 = []
        ch15 = []
        for i in range (full_samples):
            ch7.append((full_data[(self.BPS*i)+1] & 0x0FFF) + 0x7000)
            ch6.append((((full_data[(self.BPS*i)+2] & 0x00FF) << 4) + ((full_data[(self.BPS*i)+1] & 0xF000) >> 12)) + 0x6000)
            ch5.append((((full_data[(self.BPS*i)+3] & 0x000F) << 8) + ((full_data[(self.BPS*i)+2] & 0xFF00) >> 8)) + 0x5000)
            ch4.append((((full_data[(self.BPS*i)+3] & 0xFFF0) >> 4)) + 0x4000)
            ch3.append((full_data[(self.BPS*i)+4] & 0x0FFF) + 0x3000)
            ch2.append((((full_data[(self.BPS*i)+5] & 0x00FF) << 4) + ((full_data[(self.BPS*i)+4] & 0xF000) >> 12)) + 0x2000)
            ch1.append((((full_data[(self.BPS*i)+6] & 0x000F) << 8) + ((full_data[(self.BPS*i)+5] & 0xFF00) >> 8)) + 0x1000)
            ch0.append((((full_data[(self.BPS*i)+6] & 0xFFF0) >> 4)))
            ch15.append((full_data[(self.BPS*i)+7] & 0x0FFF) + 0xf000)
            ch14.append((((full_data[(self.BPS*i)+8] & 0x00FF) << 4) + ((full_data[(self.BPS*i)+7] & 0xF000) >> 12)) + 0xe000)
            ch13.append((((full_data[(self.BPS*i)+9] & 0x000F) << 8) + ((full_data[(self.BPS*i)+8] & 0xFF00) >> 8)) + 0xd000)
            ch12.append((((full_data[(self.BPS*i)+9] & 0xFFF0) >> 4)) + 0xc000)
            ch11.append((full_data[(self.BPS*i)+10] & 0x0FFF) + 0xb000)
            ch10.append((((full_data[(self.BPS*i)+11] & 0x00FF) << 4) + ((full_data[(self.BPS*i)+10] & 0xF000) >> 12)) + 0xa000)
            ch9.append((((full_data[(self.BPS*i)+12] & 0x000F) << 8) + ((full_data[(self.BPS*i)+11] & 0xFF00) >> 8)) + 0x9000)
            ch8.append((((full_data[(self.BPS*i)+12] & 0xFFF0) >> 4)) + 0x8000)
            
        chip = [ch0,ch1,ch2,ch3,ch4,ch5,ch6,ch7,ch8,ch9,ch10,ch11,ch12,ch13,ch14,ch15]
        full_data = None
        del full_data
        
        
        print("UnpackData--> Saving as seperate channels (2 min)")
        for i in range (16):
            filename = config_path + "\\" + "LN_2MHz_ch{}.bin".format(hex(i))
            with open(filename,"wb") as f:
                to_write = struct.pack(">{}H".format(len(chip[i])),*chip[i])
                f.write(to_write)
                f.close()

        plt.subplots_adjust(wspace=0, hspace=0, top = 1, bottom = 0.05, right = 0.95, left = 0.05)
        
        if (to_plot == False):
            chip = None
            del chip
            return 0
        
        #print (chip)
        
        if (len(ch7) == len(ch8)):
            length = len(ch7)
        else:
            print ("UnpackData --> Not all channels have equal lengths")

        time_x = []
        
        for i in range(length):
            time_x.append(0.5 * i)
            
        print ("UnpackData--> Plotting Data (4 min)")
            
        fig = plt.figure(figsize=(16, 12), dpi=80)
        overlay_ax = fig.add_subplot(1,1,1)
        overlay_ax.spines['top'].set_color('none')
        overlay_ax.spines['bottom'].set_color('none')
        overlay_ax.spines['left'].set_color('none')
        overlay_ax.spines['right'].set_color('none')
        overlay_ax.tick_params(labelcolor='w', top='off', bottom='off', left='off', right='off')
        overlay_ax.set_xlabel('Time (us)')
        overlay_ax.set_ylabel('ADC Counts')
        overlay_ax.yaxis.set_label_coords(-0.035,0.5)
        
        ax1 = fig.add_subplot(16,1,16)
        plt.plot(time_x, ch0)
        plt.setp(ax1.get_xticklabels(), fontsize=12)
        ax1.set_title("Channel 0")
        ax2 = ax1.twinx()
        ax2.set_ylabel("Channel 0", rotation = 0)
        ax2.spines['top'].set_color('none')
        ax2.spines['bottom'].set_color('none')
        ax2.spines['left'].set_color('none')
        ax2.spines['right'].set_color('none')
        ax2.tick_params(labelcolor='w', top='off', bottom='off', left='off', right='off')
        
        print ("UnpackData--> Ch0 Ready")

        for i in range(15):
        
            ax = fig.add_subplot(16,1,15-i, sharex=ax1)
            plot_data = []
            for j in range (len(chip[i+1])):
                plot_data.append(chip[i+1][j] & 0xFFF)
            plt.plot(time_x, plot_data)
            plt.setp(ax.get_xticklabels(), visible=False)
            ax2 = ax.twinx()
            ax2.set_ylabel("Channel " + str(i+1), rotation = 0)
#            ax2.spines['top'].set_color('none')
#            ax2.spines['bottom'].set_color('none')
#            ax2.spines['left'].set_color('none')
#            ax2.spines['right'].set_color('none')
            ax2.tick_params(labelcolor='w', top='off', bottom='off', left='off', right='off')
            pos1 = ax2.get_position() # get the original position 
            pos2 = [pos1.x0 + 0.025, pos1.y0 + 0.005,  pos1.width , pos1.height ] 
            ax2.set_position(pos2) # set a new position
            print ("UnpackData--> Ch{} Ready".format(i+1))
            
        del chip
        plt.subplots_adjust(wspace=0, hspace=0, top = 1, bottom = 0.05, right = 0.95, left = 0.05)
        
        plt.savefig (plot_name)
        plt.clf()        
        print("UnpackData--> Data Saved as " + plot_name)

        
    def PlotSingles(self, filenames, plot_name):
        
        chip = [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]]
        file_num = len(filenames)
        for i in range(file_num):
            print ("Unpacking Channel {}".format(i))
            fileinfo  = os.stat(filenames[i])
            filelength = fileinfo.st_size
            with open(filenames[i], 'rb') as f:
                raw_data = f.read(filelength)
                f.close()

            temp = (struct.unpack_from(">{}H".format(filelength/2),raw_data))
            for j in range(filelength/2):
                chip[i].append(temp[j] & 0xFFF)
        

        plt.subplots_adjust(wspace=0, hspace=0, top = 1, bottom = 0.05, right = 0.95, left = 0.05)
        
        time_x = []
        
        length = len(chip[0])
        
        for i in range(length):
            time_x.append(0.5 * i)
            
        print ("UnpackData--> Plotting Data (4 min)")
            
        fig = plt.figure(figsize=(16, 12), dpi=80)
        overlay_ax = fig.add_subplot(1,1,1)
        overlay_ax.spines['top'].set_color('none')
        overlay_ax.spines['bottom'].set_color('none')
        overlay_ax.spines['left'].set_color('none')
        overlay_ax.spines['right'].set_color('none')
        overlay_ax.tick_params(labelcolor='w', top='off', bottom='off', left='off', right='off')
        overlay_ax.set_xlabel('Time (us)')
        overlay_ax.set_ylabel('ADC Counts')
        overlay_ax.yaxis.set_label_coords(-0.035,0.5)
        
        ax1 = fig.add_subplot(16,1,16)
        plt.plot(time_x, chip[0])
        plt.setp(ax1.get_xticklabels(), fontsize=12)
        ax1.set_title("Channel 0")
        ax2 = ax1.twinx()
        ax2.set_ylabel("Channel 0", rotation = 0)
        ax2.spines['top'].set_color('none')
        ax2.spines['bottom'].set_color('none')
        ax2.spines['left'].set_color('none')
        ax2.spines['right'].set_color('none')
        ax2.tick_params(labelcolor='w', top='off', bottom='off', left='off', right='off')
        
        print ("UnpackData--> Ch0 Ready")

        for i in range(15):
        
            ax = fig.add_subplot(16,1,15-i, sharex=ax1)
            plot_data = []
            for j in range (len(chip[i+1])):
                plot_data.append(chip[i+1][j] & 0xFFF)
            plt.plot(time_x, plot_data)
            plt.setp(ax.get_xticklabels(), visible=False)
            ax2 = ax.twinx()
            ax2.set_ylabel("Channel " + str(i+1), rotation = 0)
#            ax2.spines['top'].set_color('none')
#            ax2.spines['bottom'].set_color('none')
#            ax2.spines['left'].set_color('none')
#            ax2.spines['right'].set_color('none')
            ax2.tick_params(labelcolor='w', top='off', bottom='off', left='off', right='off')
            pos1 = ax2.get_position() # get the original position 
            pos2 = [pos1.x0 + 0.025, pos1.y0 + 0.005,  pos1.width , pos1.height ] 
            ax2.set_position(pos2) # set a new position
            print ("UnpackData--> Ch{} Ready".format(i+1))
            
        del chip
        plt.subplots_adjust(wspace=0, hspace=0, top = 1, bottom = 0.05, right = 0.95, left = 0.05)
        
        plt.savefig (plot_name)
        plt.clf()        
        print("UnpackData--> Data Saved as " + plot_name)
        
        
#__INIT__#
    def __init__(self):
        self.BPS = 13 #Bytes per sample.  The one for "0xFACE" and then 12 bytes for 16 channels at 12 bits each.
        self.channels = 16
        self.start_of_packet = (b"\xde\xad\xbe\xef")
        self.start_of_sample = (b"\xfa\xce")
        self.debug_file_name = "\Data_Analysis_Debug.txt"
        self.screendisplay = None
        self.notice1_every = 10000
        self.notice2_every = 50000
        
if __name__ == "__main__":
    single_channels = []
    for i in range (16):
        single_channels.append("D:\Eric\Quad_Data_2017_09_26\\axestest\ch{}.dat".format(i))
    
    Data_Analysis().PlotSingles(single_channels)
    #Data_Analysis().UnpackData("D:\\nEXO\\2017_06_19\\" + "ped.dat")
    #Data_Analysis().Missing_Packet_Check("D:\\Eric\\Packets\\")
    #Data_Analysis().Seperate_Packets("D:\\Eric\\Packets\\", 4, 4)