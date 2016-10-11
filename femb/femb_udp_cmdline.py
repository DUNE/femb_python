import struct
import sys 
import string
import socket
import time
from socket import AF_INET, SOCK_DGRAM
import binascii

class FEMB_UDP:

    def write_reg(self, reg , data ):
        regVal = int(reg)
        if (regVal < 0) or (regVal > self.MAX_REG_NUM):
            #print "FEMB_UDP--> Error write_reg: Invalid register number"
            return None
        dataVal = int(data)
        if (dataVal < 0) or (dataVal > self.MAX_REG_VAL):
            #print "FEMB_UDP--> Error write_reg: Invalid data value"
            return None
        
        #crazy packet structure require for UDP interface
        dataValMSB = ((dataVal >> 16) & 0xFFFF)
        dataValLSB = dataVal & 0xFFFF
        WRITE_MESSAGE = struct.pack('HHHHHHHHH',socket.htons( self.KEY1  ), socket.htons( self.KEY2 ),socket.htons(regVal),socket.htons(dataValMSB),
                socket.htons(dataValLSB),socket.htons( self.FOOTER  ), 0x0, 0x0, 0x0  )
        
        #send packet to board, don't do any checks
        sock_write = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # Internet, UDP
        sock_write.setblocking(0)
        sock_write.sendto(WRITE_MESSAGE,(self.UDP_IP, self.UDP_PORT_WREG ))
        sock_write.close()
        #print "FEMB_UDP--> Write: reg=%x,value=%x"%(reg,data)

    def write_reg_bits(self, reg , pos, mask, data ):
        regVal = int(reg)
        if (regVal < 0) or (regVal > self.MAX_REG_NUM):
                #print "FEMB_UDP--> Error write_reg_bits: Invalid register number"
                return None
        posVal = int(pos)
        if (posVal < 0 ) or (posVal > 31):
                #print "FEMB_UDP--> Error write_reg_bits: Invalid register position"
                return None
        maskVal = int(mask)
        if (maskVal < 0 ) or (maskVal > 31):
                #print "FEMB_UDP--> Error write_reg_bits: Invalid bit mask"
                return None
        dataVal = int(data)
        if (dataVal < 0) or (dataVal > self.MAX_REG_VAL):
                #print "FEMB_UDP--> Error write_reg_bits: Invalid data value"
                return None
        if dataVal > maskVal :
                #print "FEMB_UDP--> Error write_reg_bits: Write value does not fit within mask"
                return None
        if (maskVal << posVal) > self.MAX_REG_VAL:
                #print "FEMB_UDP--> Error write_reg_bits: Write range exceeds register size"
                return None

        #get initial register value
        initReg = self.read_reg( regVal )
        initRegVal = int(initReg)
        if (initRegVal < 0) or (initRegVal > self.MAX_REG_VAL):
                #print "FEMB_UDP--> Error write_reg_bits: Invalid initial register value"
                return None

        shiftVal = (dataVal & maskVal)
        regMask = (maskVal << posVal)
        newRegVal = ( (initRegVal & ~(regMask)) | (shiftVal  << posVal) ) 
        if (newRegVal < 0) or (newRegVal > self.MAX_REG_VAL):
                #print "FEMB_UDP--> Error write_reg_bits: Invalid new register value"
                return None

        #crazy packet structure require for UDP interface
        dataValMSB = ((newRegVal >> 16) & 0xFFFF)
        dataValLSB = newRegVal & 0xFFFF
        WRITE_MESSAGE = struct.pack('HHHHHHHHH',socket.htons( self.KEY1  ), socket.htons( self.KEY2 ),socket.htons(regVal),socket.htons(dataValMSB),
                socket.htons(dataValLSB),socket.htons( self.FOOTER  ), 0x0, 0x0, 0x0  )

        #send packet to board, don't do any checks
        sock_write = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # Internet, UDP
        sock_write.setblocking(0)
        sock_write.sendto(WRITE_MESSAGE,(self.UDP_IP, self.UDP_PORT_WREG ))
        sock_write.close()

    def read_reg(self, reg ):
        regVal = int(reg)
        if (regVal < 0) or (regVal > self.MAX_REG_NUM):
                #print "FEMB_UDP--> Error read_reg: Invalid register number"
                return None

        #set up listening socket, do before sending read request
        sock_readresp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # Internet, UDP
        sock_readresp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock_readresp.bind(('', self.UDP_PORT_RREGRESP ))
        sock_readresp.settimeout(2)

        #crazy packet structure require for UDP interface
        READ_MESSAGE = struct.pack('HHHHHHHHH',socket.htons(self.KEY1), socket.htons(self.KEY2),socket.htons(regVal),0,0,socket.htons(self.FOOTER),0,0,0)
        sock_read = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # Internet, UDP
        sock_read.setblocking(0)
        sock_read.sendto(READ_MESSAGE,(self.UDP_IP,self.UDP_PORT_RREG))
        sock_read.close()

        #try to receive response packet from board, store in hex
        data = []
        try:
                data = sock_readresp.recv(1024)
        except socket.timeout:
                #print "FEMB_UDP--> Error read_reg: No read packet received from board, quitting"
                sock_readresp.close()
                return -1        
        dataHex = binascii.hexlify( data ) 
        sock_readresp.close()

        #extract register value from response
        if int(dataHex[0:4],16) != regVal :
                #print "FEMB_UDP--> Error read_reg: Invalid response packet"
                return None
        dataHexVal = int(dataHex[4:12],16)
        #print "FEMB_UDP--> Write: reg=%x,value=%x"%(reg,dataHexVal)
        return dataHexVal

    def get_data_packets(self, num):
        numVal = int(num)
        if (numVal < 0) or (numVal > self.MAX_NUM_PACKETS):
                #print "FEMB_UDP--> Error record_hs_data: Invalid number of data packets requested"
                return None

        #set up listening socket
        sock_data = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # Internet, UDP
        sock_data.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock_data.bind(('',self.UDP_PORT_HSDATA))
        sock_data.settimeout(2)

        #get N data packets
        rawdataPackets = []
        for packet in range(0,numVal,1):
                data = None
                try:
                        data = sock_data.recv(1024)
                except socket.timeout:
                        #print "FEMB_UDP--> Error get_data_packets: No data packet received from board, quitting"
                        sock_data.close()
                        return None
                if data != None:
                        rawdataPackets.append(data)
        sock_data.close()

        return rawdataPackets

    def get_data_samples(self, rawdataPackets):
        if rawdataPackets == None:
            return None
        if len(rawdataPackets) == 0:
            return None

        dataPackets = []
        for rawdata in rawdataPackets:
            if len(rawdata) < 1024:
                dataPackets = None
                return None
            data = struct.unpack_from(">512H",rawdata)
            #print data[1]
            data = data[8:]
            #dataPackets.append(data)
            dataPackets = dataPackets + list(data)

        return dataPackets

    def get_data(self, num):
      numVal = int(num)
      if (numVal < 0) or (numVal > self.MAX_NUM_PACKETS):
        #print "FEMB_UDP--> Error record_hs_data: Invalid number of data packets requested"
        return None

      rawdata = self.get_data_packets(numVal)
      data = self.get_data_samples(rawdata)
      return data 

    #__INIT__#
    def __init__(self):
        self.UDP_IP = "192.168.121.1"
        self.KEY1 = 0xDEAD
        self.KEY2 = 0xBEEF
        self.FOOTER = 0xFFFF
        self.UDP_PORT_WREG = 32000
        self.UDP_PORT_RREG = 32001
        self.UDP_PORT_RREGRESP = 32002
        self.UDP_PORT_HSDATA = 32003
        self.MAX_REG_NUM = 666
        self.MAX_REG_VAL = 0xFFFFFFFF
        self.MAX_NUM_PACKETS = 1000
