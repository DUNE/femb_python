#!/usr/bin/env python33
import sys
import struct
import socket
import binascii
import time
import pickle
from user_settings import user_editable_settings
settings = user_editable_settings()

class FEMB_UDP:
    
    #Sends a full 32 bit register to either FPGA
    def write_reg(self, reg, data):
        
        regVal = int(reg)
        if (regVal < 0) or (regVal > self.MAX_REG_NUM):
            print ("FEMB_UDP--> Error write_reg: Invalid register number")
            return None
        
        dataVal = int(data)
        if (dataVal < 0) or (dataVal > self.MAX_REG_VAL):
            print ("FEMB_UDP--> Error write_reg: Invalid data value")
            return None
        
        #Splits the register up, since both halves need to go through socket.htons seperately
        dataValMSB = ((dataVal >> 16) & 0xFFFF)
        dataValLSB = dataVal & 0xFFFF
        
        #Organize packets as described in user manual
        WRITE_MESSAGE = struct.pack('HHHHHH',socket.htons( self.KEY1  ), socket.htons( self.KEY2 ),
                                    socket.htons(regVal),socket.htons(dataValMSB),
                                    socket.htons(dataValLSB),socket.htons( self.FOOTER ))
        
        #Set up socket for IPv4 and UDP, attach the correct PC IP
        sock_write = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock_write.bind((settings.PC_IP, 0))
        
        #Send to FPGA at 192.168.121.1, and the correct port for the board we're writing to

        sock_write.sendto(WRITE_MESSAGE,(settings.FPGA_IP, self.PORT_WREG ))
        #print ("Sent FEMB data from")
        #print (sock_write.getsockname())
        sock_write.close()
        #print ("FEMB_UDP--> Write: reg=%x,value=%x"%(reg,data))
        
    #Read a full register from the FEMB FPGA.  Returns the 32 bits in an integer form
    def read_reg(self, reg):
        
        for i in range(10):
            regVal = int(reg)
            if (regVal < 0) or (regVal > self.MAX_REG_NUM):
                    print ("FEMB_UDP--> Error read_reg: Invalid register number")
                    return None
    
            #Set up listening socket before anything else - IPv4, UDP
            sock_readresp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            #Allows us to quickly access the same socket and ignore the usual OS wait time betweeen accesses
            sock_readresp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            #Prepare to listen at configuration socket and for the correct port for the board we're writing to

            sock_readresp.bind((settings.PC_IP, self.PORT_RREGRESP ))
    
            sock_readresp.settimeout(.2)
    
            #First send a request to read out this sepecific register at the read request port for the board
            READ_MESSAGE = struct.pack('HHHHHHHHH',socket.htons(self.KEY1), socket.htons(self.KEY2),socket.htons(regVal),0,0,socket.htons(self.FOOTER),0,0,0)
            sock_read = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock_read.setblocking(0)
            sock_read.bind((settings.PC_IP, 0))
            

            sock_read.sendto(READ_MESSAGE,(settings.FPGA_IP,self.PORT_RREG))
            
            
            #print ("Sent read request from")
            #print (sock_read.getsockname())
            
            sock_read.close()
    
            #try to receive response packet from board, store in hex
            data = []
            try:
                    data = sock_readresp.recv(self.BUFFER_SIZE)
            except socket.timeout:
                if (i > 8):
                    print ("FEMB_UDP--> Error read_reg: No read packet received from board, quitting")
                    print (sock_readresp.getsockname())
                    sock_readresp.close()
                    return None     
                    print ("FEMB_UDP--> Didn't get a readback response, trying again...")
                #else:
                    #print ("FEMB_UDP--> Didn't get a readback response, trying again...")     
                
            #print ("Waited for FEMB response on")
            #print (sock_readresp.getsockname())
            sock_readresp.close()
            
            if (data != []):
                #Goes from binary data to hexidecimal (because we know this is host order bits)
                dataHex = binascii.hexlify(data)
                #If reading, say register 0x290, you may get back
                #0290FFFFCCCC0291FFFFDDDD00000000000000
                #The first 4 bits are the register you requested, the next 8 bits are the value
                #By default, the current firmware also sends back the next register (0291 in this case) also
                #There's an option to continuously read out successive registers, but it would need a larger buffer
                
                #Looks for those first 4 bits to make sure you read the register you're looking for
                if (int(dataHex[0:4],16) == regVal):
                    break
                #else:
                    #print ("FEMB_UDP--> Error read_reg: Invalid response packet")

        
        
            
        #Return the data part of the response in integer form (it's just easier)
        dataHexVal = int(dataHex[4:12],16)
        #print ("FEMB_UDP--> Read: reg=%x,value=%x"%(reg,dataHexVal))
        return dataHexVal

    #Read and return a given amount of unpacked data "packets"
    #If you're going to save it write to disk, request it as "bin"
    #If you're going to use it in Python for something else, request the int or hex
    def get_data_packets(self, data_type, num=1, header = False):
        numVal = int(num)
        if (numVal < 0) or (numVal > self.MAX_NUM_PACKETS):
                print ("FEMB_UDP--> Error: Invalid number of data packets requested")
                return None
            
        if ((data_type != "int") and (data_type != "hex") and (data_type != "bin")):
            print ("FEMB_UDP--> Error: Request packets as data_type = 'int', 'hex', or 'bin'")
            return None

        #set up IPv4, UDP listening socket at requested IP
        sock_data = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock_data.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock_data.bind((settings.PC_IP,self.PORT_HSDATA))
        sock_data.settimeout(10)

        #Read a certain amount of packets
        rawdataPackets = bytearray()
        for packet in range(0,numVal,1):
            data = []
            try:
                    data = sock_data.recv(self.BUFFER_SIZE)
            except socket.timeout:
                    print ("FEMB_UDP--> Error get_data_packets: No data packet received from board, quitting")
                    print ("FEMB_UDP--> Socket was {}".format(sock_data))
                    return []
            except OSError:
                print ("FEMB_UDP--> Error accessing socket: No data packet received from board, quitting")
                print ("FEMB_UDP--> Socket was {}".format(sock_data))
                sock_data.close()
                return []
            if (data != None):
                #If the user wants the header, keep those 16 bits in, or else don't
                if (header != True):
                    rawdataPackets += data[16:]
                else:
                    rawdataPackets += data

        #print (sock_data.getsockname())
        sock_data.close()
        
        #If the user wanted straight up bytes, then return the bytearray
        if (data_type == "bin"):
            return rawdataPackets

        
        buffer = (len(rawdataPackets))/2
        #Unpacking into shorts in increments of 2 bytes
        formatted_data = struct.unpack_from(">%dH"%buffer,rawdataPackets)

        #If the user wants to display the data as a hex
        if (data_type == "hex"):
            hex_tuple = []
            for i in range(len(formatted_data)):
                hex_tuple.append(hex(formatted_data[i]))
            return hex_tuple
            
            
        return formatted_data
        
    def get_data_packets_check(self, folder, num):
        numVal = int(num)
        #set up IPv4, UDP listening socket at requested IP
        sock_data = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock_data.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock_data.bind((settings.PC_IP,self.PORT_HSDATA))
        sock_data.settimeout(10)

        #Read a certain amount of packets
        packet_num = 0
        missing_packets = 0
        rawdataPackets = []
        for packet in range(0,numVal,1):
            data = []
            try:
                    data = sock_data.recv(self.BUFFER_SIZE)
            except socket.timeout:
                    print ("FEMB_UDP--> Error get_data_packets: No data packet received from board, quitting")
                    print ("FEMB_UDP--> Socket was {}".format(sock_data))
                    return []
            except OSError:
                print ("FEMB_UDP--> Error accessing socket: No data packet received from board, quitting")
                print ("FEMB_UDP--> Socket was {}".format(sock_data))
                sock_data.close()
                return []
              
            packet_num_check = struct.unpack_from(">1I",data)[0]
            
            if (packet_num == 0):
                packet_num = packet_num_check
                rawdataPackets.append(data)
            else:
                if(packet_num_check != packet_num + 1):
                    print ("FEMB_UDP--> Missing Packet!  Went from {} to {} on {} try!".format(hex(packet_num), hex(packet_num_check), packet))
                    missing_packets += 1
                    return -1

                rawdataPackets.append(data)
                packet_num = packet_num_check
                
        #print (sock_data.getsockname())
        sock_data.close()
        print ("FEMB_UDP--> {} missing packets".format(missing_packets))
        packet_size = len(data)
        
        try:
            with open(folder + 'configuration.cfg', 'rb') as f:
                config = pickle.load(f)
                config['packet_size'] = packet_size
                
        except IOError:
            config = {'packet_size': packet_size,
                    }
        
        with open(folder + 'configuration.cfg', 'wb') as f:
            pickle.dump(config, f, pickle.HIGHEST_PROTOCOL)
            
        return rawdataPackets
        
    #Send a dummy packet from the PC to an FPGA port in order to initiate an ARP request and map the FPGA port
    def init_ports(self, hostIP = '', destIP = '', dummy_port = 0):
        
        #An incorrect version of the packet is fine, the communication wont go through, it just triggeres ARP
        WRITE_MESSAGE = struct.pack('HHH',socket.htons( self.KEY1  ), socket.htons( self.FOOTER  ), 0x0  )
        
        #Set up the port for IPv4 and UDP
        sock_write = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        sock_write.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        #Send from the appropriate socket to the requested IP (maybe add something to tell you if you did it wrong?)
        sock_write.bind((hostIP,dummy_port))
        sock_write.sendto(WRITE_MESSAGE,(destIP, self.PORT_WREG ))

        sock_write.close()

    #__INIT__#
    def __init__(self):

        #Standard keys to include in data transmission
        self.KEY1 = 0xDEAD
        self.KEY2 = 0xBEEF
        self.FOOTER = 0xFFFF
        
        #The relevant ports for reading and writing to each board
        self.PORT_WREG = 32000
        self.PORT_RREG = 32001
        self.PORT_RREGRESP = 32002
        self.PORT_HSDATA = 32003
        
        #Just some limits to check against
        self.MAX_REG_NUM = 667
        self.MAX_REG_VAL = 0xFFFFFFFF
        self.MAX_NUM_PACKETS = 100000
        self.BUFFER_SIZE = 9014