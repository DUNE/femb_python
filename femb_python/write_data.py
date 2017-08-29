from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import
from builtins import open
from builtins import int
from builtins import str
from future import standard_library
standard_library.install_aliases()
from builtins import object
import string
from array import array
from femb_python.femb_udp import FEMB_UDP
import uuid
import datetime
import time
import struct
import os

class WRITE_DATA(object):

    def __init__(self, filedir="data"):
        self.femb = FEMB_UDP()
        self.filename = "output_write_data.bin"
        self.numpacketsrecord = 100
        self.run = 0
        self.runtype = 0
        self.runversion = 0
        self.date = int( datetime.datetime.today().strftime('%Y%m%d%H%M%S') )
        self.filedir = filedir

        
    @property
    def data_file_path(self):
        return os.path.join(self.filedir,self.filename)

    def assure_filedir(self):
        #check local directory structure
        if os.path.isdir( str(self.filedir) ) == False:
            print("write_data: Data directory not found, making now.")
            os.makedirs( str(self.filedir) )
        #check if directory actually created
        if os.path.isdir( str(self.filedir) ) == False:
            print("write_data: Error creating data directory, check filesystem.")
            return None
        return 1

    def open_file(self):
        print("write_data: Open file: %s" % self.data_file_path )

        self.assure_filedir()

        self.data_file=open(self.data_file_path,'wb')
        return 1

    def record_data(self,subrun, asic, asicCh):
        subrunVal = int(subrun)
        if subrunVal < 0 :
            return
        asicVal = int(asic)
        if asicVal < 0 :
            return
        asicChVal = int(asicCh)
        if asicChVal < 0 :
            return
        #print("write_data: Record data")
        data = self.femb.get_data_packets(self.numpacketsrecord)
        if data == None :
          print("write_data: Did not get any data, streaming might have failed!!!")
          return
        for packet in data:
            #UDP packet header
            self.data_file.write(struct.pack('!H', 0x0))
            self.data_file.write(struct.pack('!H', 0xDEAD))
            self.data_file.write(struct.pack('!H', 0xBEEF))
            self.data_file.write(struct.pack('!H', 0x0))
            self.data_file.write(struct.pack('!H', 0xBA5E))
            self.data_file.write(struct.pack('!H', subrunVal))
            self.data_file.write(struct.pack('!H', asicVal))
            self.data_file.write(struct.pack('!H', asicChVal))
            #write data
            self.data_file.write(packet)
            
    def close_file(self):
        print("write_data: Close file")
        self.data_file.close()
