"""
This is the UDB interface to the femb
"""
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import
from builtins import range
from builtins import int
from future import standard_library
standard_library.install_aliases()
from builtins import object
import struct
import sys 
import string
import socket
import time
from socket import AF_INET, SOCK_DGRAM
import binascii
from .helper_scripts.locking import FEMB_LOCK
from femb_python.test_instrument_interface.rigol_dp832 import RigolDP832
from femb_python.test_measurements.OscillatorTesting.code.driverUSBTMC import DriverUSBTMC

class FEMB_UDP(object):
    """
    This is the UDB interface to the femb
    """

    def write_reg(self, reg , data , writeAttempt=0, doReadBack=True):
        try:
            regVal = int(reg)
        except TypeError:
            return None
        if (regVal < 0) or (regVal > int(self.udp["MAX_REG_NUM"], 16)):
            #print "FEMB_UDP--> Error write_reg: Invalid register number"
            return None
        try:
            dataVal = int(data)
        except TypeError:
            return None
        if (dataVal < 0) or (dataVal > int(self.udp["MAX_REG_VAL"], 16)):
            #print "FEMB_UDP--> Error write_reg: Invalid data value"
            return None
        #print("writing register {} data {:#010x}".format(reg,data))
        
        #crazy packet structure require for UDP interface
        dataValMSB = ((dataVal >> 16) & 0xFFFF)
        dataValLSB = dataVal & 0xFFFF
        WRITE_MESSAGE = struct.pack('HHHHHHHHH',socket.htons( int(self.udp["KEY1"], 16)  ), socket.htons( int(self.udp["KEY2"], 16) ),socket.htons(regVal),socket.htons(dataValMSB),
                socket.htons(dataValLSB),socket.htons( int(self.udp["FOOTER"], 16)  ), 0x0, 0x0, 0x0  )
        
        #send packet to board, don't do any checks
        with FEMB_LOCK() as lock:
            sock_write = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # Internet, UDP
            sock_write.setblocking(0)
            sock_write.sendto(WRITE_MESSAGE,(self.udp["UDP_IP"], int(self.udp["UDP_PORT_WREG"]) ))
            sock_write.close()
            #print "FEMB_UDP--> Write: reg=%x,value=%x"%(reg,data)
            time.sleep(float(self.udp["UDP_SLEEP"]))

        if (doReadBack == False) :
            return None
        if (regVal == 0) or (regVal == 1) or (regVal == 2): #don't try to rewrite certain registers
            return None

        #do read back, attempts recursive rewrite if disagreement
        regReadVal = self.read_reg(regVal)
        #print("HERE\t",hex(regReadVal),"\t", hex(dataVal))
        if regReadVal != dataVal :
            print("FEMB_UDP--> Error write_reg: Readback failed.  Writing {} to Register {}, but the readback is {}".format(data, reg, regReadVal))
            if writeAttempt > int(self.udp["MAX_ATTEMPTS"]) :
                print("FEMB_UDP--> Error write_reg: Max number of rewrite attempts, return")
                self.check_power_fault()
                return None
            if writeAttempt > 10 : #harcoded max number of attempts = 10
                print("FEMB_UDP--> Error write_reg: Max number of rewrite attempts, return")
                self.check_power_fault()
                return None
            self.write_reg(regVal,dataVal,writeAttempt + 1)
            

    def write_reg_bits(self, reg , pos, mask, data ):
        try:
            regVal = int(reg)
        except TypeError:
            return None
        if (regVal < 0) or (regVal > int(self.udp["MAX_REG_NUM"], 16)):
            print( "FEMB_UDP--> Error write_reg_bits: Invalid register number")
            return None

        try:
            posVal = int(pos)
        except TypeError:
            return None
        if (posVal < 0 ) or (posVal > 31):
            print( "FEMB_UDP--> Error write_reg_bits: Invalid register position")
            return None

        try:
            maskVal = int(mask)
        except TypeError:
            return None
        if (maskVal < 0 ) or (maskVal > 0xFFFFFFFF):
            print( "FEMB_UDP--> Error write_reg_bits: Invalid bit mask")
            return None

        try:
            dataVal = int(data)
        except TypeError:
            return None
        if (dataVal < 0) or (dataVal > int(self.udp["MAX_REG_VAL"], 16)):
            print( "FEMB_UDP--> Error write_reg_bits: Invalid data value")
            return None
        if dataVal > maskVal :
            print( "FEMB_UDP--> Error write_reg_bits: Write value does not fit within mask")
            return None
        if (maskVal << posVal) > int(self.udp["MAX_REG_VAL"], 16):
            print( "FEMB_UDP--> Error write_reg_bits: Write range exceeds register size")
            return None

        #get initial register value
        initReg = self.read_reg( regVal )
        try:
            initRegVal = int(initReg)
        except TypeError:
            return None
        if (initRegVal < 0) or (initRegVal > int(self.udp["MAX_REG_VAL"], 16)):
            #print "FEMB_UDP--> Error write_reg_bits: Invalid initial register value"
            return None

        shiftVal = (dataVal & maskVal)
        regMask = (maskVal << posVal)
        newRegVal = ( (initRegVal & ~(regMask)) | (shiftVal  << posVal) ) 
        if (newRegVal < 0) or (newRegVal > int(self.udp["MAX_REG_VAL"], 16)):
                #print "FEMB_UDP--> Error write_reg_bits: Invalid new register value"
                return None

        #crazy packet structure require for UDP interface
        dataValMSB = ((newRegVal >> 16) & 0xFFFF)
        dataValLSB = newRegVal & 0xFFFF
        WRITE_MESSAGE = struct.pack('HHHHHHHHH',socket.htons( int(self.udp["KEY1"], 16)  ), socket.htons( int(self.udp["self.KEY2"]) ),socket.htons(regVal),socket.htons(dataValMSB),
                socket.htons(dataValLSB),socket.htons( int(self.udp["FOOTER"], 16)  ), 0x0, 0x0, 0x0  )

        #send packet to board, don't do any checks
        with FEMB_LOCK() as lock:
            sock_write = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # Internet, UDP
            sock_write.setblocking(0)
            sock_write.sendto(WRITE_MESSAGE,(self.udp["UDP_IP"], int(self.udp["UDP_PORT_WREG"]) ))
            sock_write.close()
            time.sleep(float(self.udp["UDP_SLEEP"]))

    def read_reg(self, reg):
        try:
            regVal = int(reg)
        except TypeError:
            return None
        if (regVal < 0) or (regVal > int(self.udp["MAX_REG_NUM"], 16)):
            print ("FEMB_UDP--> Error read_reg: Invalid register number")
            return None

        with FEMB_LOCK() as lock:
            #set up listening socket, do before sending read request
            sock_readresp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # Internet, UDP
            sock_readresp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock_readresp.bind(('', int(self.udp["UDP_PORT_RREGRESP"] )))
            sock_readresp.settimeout(2)

            #crazy packet structure require for UDP interface
            READ_MESSAGE = struct.pack('HHHHHHHHH',socket.htons(int(self.udp["KEY1"], 16)), socket.htons(int(self.udp["KEY2"], 16)),socket.htons(regVal),0,0,socket.htons(int(self.udp["FOOTER"], 16)),0,0,0)
            sock_read = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # Internet, UDP
            sock_read.setblocking(0)
            sock_read.sendto(READ_MESSAGE,(self.udp["UDP_IP"],int(self.udp["UDP_PORT_RREG"])))
            sock_read.close()

            #try to receive response packet from board, store in hex
            data = []
            try:
                data = sock_readresp.recv(int(self.udp["MAX_PACKET_SIZE"]))
            except socket.timeout:
                print("FEMB_UDP--> Error read_reg: No read packet received from board for register {}, quitting".format(reg))
                sock_readresp.close()
                self.check_power_fault()
                return None       
            dataHex = binascii.hexlify( data ) 
            sock_readresp.close()

            #extract register value from response packet
            try:
                packetRegVal = int(dataHex[0:4],16)
            except TypeError:
                return None
            if packetRegVal != regVal :
                print("FEMB_UDP--> Error read_reg: Invalid response packet for register {}".format(reg))
                return None

            try:
                dataHexVal = int(dataHex[4:12],16)
            except TypeError:
                return None
        
            #print "FEMB_UDP--> Write: reg=%x,value=%x"%(reg,dataHexVal)
            time.sleep(float(self.udp["UDP_SLEEP"]))
            return dataHexVal

    #Read and return a given amount of unpacked data "packets"
    #If you're going to save it write to disk, request it as "bin"
    #If you're going to use it in Python for something else, request the "int"
    def get_data_packets(self, data_type = "bin", num=1, header = False):
        try:
            numVal = int(num)
        except TypeError:
            return None
        if (numVal < 0) or (numVal > int(self.udp["MAX_NUM_PACKETS"])):
            print( "FEMB_UDP--> Error get_data_packets: Invalid number of data packets requested" )
            return None

        with FEMB_LOCK() as lock:
            #set up listening socket
            sock_data = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # Internet, UDP
            sock_data.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock_data.bind(('',int(self.udp["UDP_PORT_HSDATA"])))
            sock_data.settimeout(2)

            #get N data packets
            rawdataPackets = bytearray()
            for packet in range(0,numVal,1):
                data = None
                try:
                    data = sock_data.recv(int(self.udp["MAX_PACKET_SIZE"]))
                except socket.timeout:
                    #print("FEMB_UDP--> Error get_data_packets: No data packet received from board, quitting")
                    sock_data.close()
                    self.check_power_fault()
                    return None
                if data != None:
                    if (header != True):
                        rawdataPackets.extend(data[int(self.udp["header_size"]):])
                    else:
                        rawdataPackets.extend(data)

                else:
                    self.check_power_fault()
                        
            sock_data.close()
            
        if (data_type == "bin"):
            return rawdataPackets

        buffer = (len(rawdataPackets))/2
        #Unpacking into shorts in increments of 2 bytes
        formatted_data = struct.unpack_from(">%dH"%buffer,rawdataPackets)
        return formatted_data
        
    #Also gets packets, but checks the packet number field to make sure that you didn't skip a packet.  Some test need that
    def get_data_packets_check(self, data_type = "bin", num=1, header = False):
        try:
            numVal = int(num)
        except TypeError:
            return None
        if (numVal < 0) or (numVal > int(self.udp["MAX_NUM_PACKETS"])):
            print( "FEMB_UDP--> Error get_data_packets: Invalid number of data packets requested" )
            return None

        with FEMB_LOCK() as lock:
            #set up listening socket
            sock_data = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # Internet, UDP
            sock_data.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock_data.bind(('',int(self.udp["UDP_PORT_HSDATA"])))
            sock_data.settimeout(2)

            #get N data packets
            packet_num = 0
            missing_packets = 0
            rawdataPackets = []
            for packet in range(0,numVal,1):
                data = None
                try:
                    data = sock_data.recv(int(self.udp["MAX_PACKET_SIZE"]))
                except socket.timeout:
                    print("FEMB_UDP--> Error get_data_packets: No data packet received from board")
                    sock_data.close()
                    self.check_power_fault()
                    return None
                    
                if data != None:
                    #Config file for specific board will tell it where to look in the header for the "packet number" variable
                    packet_num_check = struct.unpack_from("{}".format(int(self.udp["packet_num1"])),data)[int(self.udp["packet_num2"])]
                
                    if (packet_num == 0):
                        packet_num = packet_num_check
                        
                        if (header != True):
                            rawdataPackets.append(data[int(self.udp["header_size"]):])
                        else:
                            rawdataPackets.append(data)
                    else:
                        if(packet_num_check != packet_num + 1):
                            print ("FEMB_UDP--> Missing Packet!  Went from {} to {} on {} try!".format(hex(packet_num), hex(packet_num_check), packet))
                            missing_packets += 1
                            return -1
    
                        if (header != True):
                            rawdataPackets.append(data[int(self.udp["header_size"]):])
                        else:
                            rawdataPackets.append(data)
                            
                        packet_num = packet_num_check

                else:
                    self.check_power_fault()
                    
            sock_data.close()
            
        if (data_type == "bin"):
            return rawdataPackets

        buffer = (len(rawdataPackets))/2
        #Unpacking into shorts in increments of 2 bytes
        formatted_data = struct.unpack_from(">%dH"%buffer,rawdataPackets)
        return formatted_data

        
    #TODO communicate with the power supply and see if it was tripped
    def check_power_fault(self):
        self.PowerSupply = RigolDP832()
        return
        
    def init_ports(self, hostIP = '', destIP = '', dummy_port = 0):
        #An incorrect version of the packet is fine, the communication wont go through, it just triggeres ARP
        WRITE_MESSAGE = struct.pack('HHH',socket.htons( int(self.udp["KEY1"], 16)  ), socket.htons( int(self.udp["FOOTER"], 16)  ), 0x0  )
        #Set up the port for IPv4 and UDP
        sock_write = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock_write.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        #Send from the appropriate socket to the requested IP (maybe add something to tell you if you did it wrong?)
        sock_write.bind((hostIP,dummy_port))
        sock_write.sendto(WRITE_MESSAGE,(destIP, int(self.udp["PORT_WREG"]) ))
        sock_write.close()

    #__INIT__#
    def __init__(self, config):
        self.udp = config["UDP_SETTINGS"]