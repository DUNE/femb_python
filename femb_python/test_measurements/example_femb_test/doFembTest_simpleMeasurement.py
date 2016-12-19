from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import
from builtins import open
from builtins import range
from builtins import int
from builtins import str
from future import standard_library
standard_library.install_aliases()
from builtins import object
import sys
import string
from subprocess import call
from time import sleep
import os
import ntpath
import glob
import struct

from ...configuration import CONFIG
from ...write_data import WRITE_DATA
from ...configuration.cppfilerunner import CPP_FILE_RUNNER

#specify location of femb_udp package

class FEMB_TEST(object):

    def __init__(self):

        #import femb_udp modules from femb_udp package
        self.femb_config = CONFIG()
        self.write_data = WRITE_DATA()
        #set appropriate packet size
        self.write_data.femb.MAX_PACKET_SIZE = 8000
	
        #set status variables
        self.status_check_setup = 0
        self.status_record_data = 0
        self.status_do_analysis = 0
        self.status_archive_results = 0
        self.cppfr = CPP_FILE_RUNNER()

    def check_setup(self):
        #CHECK STATUS AND INITIALIZATION
        print("SIMPLE MEASUREMENT - CHECKING READOUT STATUS")
        self.status_check_setup = 0

        #check local directory structure, available space
        if os.path.isdir("./data") == False:
            print("Error running doFembTest - data directory not found.")
            print(" Please check that femb_python package directory structure is intact.")
            return

        #check if register interface is working
        print("Checking register interface")
        regVal = self.write_data.femb.read_reg(6)
        if (regVal == None) or (regVal == -1):
            print("Error running doFembTest - FEMB register interface is not working.")
            print(" Turn on or debug FEMB UDP readout.")       
            return

        #initialize FEMB to known state
        print("Initializing board")
        self.femb_config.initBoard()

        #check if data streaming is working
        print("Checking data streaming")
        testData = self.write_data.femb.get_data_packets(1)
        if testData == None:
            print("Error running doFembTest - FEMB is not streaming data.")
            print(" Turn on and initialize FEMB UDP readout.")
            #print(" This script will exit now")
            #sys.exit(0)
            return
        if len(testData) == 0:
            print("Error running doFembTest - FEMB is not streaming data.")
            print(" Turn on and initialize FEMB UDP readout.")
            #print(" This script will exit now")
            #sys.exit(0)
            return

        print("Received data packet " + str(len(testData[0])) + " bytes long")

        #check for analysis executables
        if not self.cppfr.exists('test_measurements/example_femb_test/parseBinaryFile'):    
            print('parseBinaryFile not found, run setup.sh')
            #sys.exit(0)
            return

        print("SIMPLE MEASUREMENT - READOUT STATUS OK")
        self.status_check_setup = 1

    def record_data(self):
        if self.status_check_setup == 0:
            print("Please run check_setup method before trying to take data")
            return
        if self.status_record_data == 1:
            print("Data already recorded. Reset/restat GUI to begin a new measurement")
            return
        #MEASUREMENT SECTION
        print("SIMPLE MEASUREMENT - RECORDING DATA")

        #initialize FEMB configuration to known state
        self.femb_config.configFeAsic(0,0,0)

        #wait to make sure HS link is back on
        sleep(0.5)

        #set output file
        self.write_data.filename = "data/output_simpleMeasurement_" + str(self.write_data.date) + ".bin"
        print("Recording " + self.write_data.filename )
        self.write_data.numpacketsrecord = 100
        self.write_data.run = 0
        self.write_data.runtype = 0
        self.write_data.runversion = 0

        #setup output file and record data
        self.write_data.open_file()
        subrun = 0
        for asic in range(0,8,1):
          for asicCh in range(0,16,1):
            self.femb_config.selectChannel(asic,asicCh)
            self.write_data.record_data(subrun, asic, asicCh)
        self.write_data.close_file()

        #reset configuration to known state
        self.femb_config.configFeAsic(0,0,0)

        print("SIMPLE MEASUREMENT - DONE RECORDING DATA")
        self.status_record_data = 1

    def do_analysis(self):
        if self.status_record_data == 0:
            print("Please record data before analysis")
            return
        if self.status_do_analysis == 1:
            print("Analysis already complete")
            return
        #ANALYSIS SECTION
        print("SIMPLE MEASUREMENT - ANALYZING AND SUMMARIZING DATA")

        #process data
        self.cppfr.call('test_measurements/example_femb_test/parseBinaryFile',[str( self.write_data.filename )])

        #run summary program
        #self.cppfr.call('test_measurements/example_femb_test/summaryAnalysis_doFembTest_simpleMeasurement',self.newlist])

        print("SIMPLE MEASUREMENT - DONE ANALYZING AND SUMMARIZING DATA")
        self.status_do_analysis = 1

    def archive_results(self):
        if self.status_do_analysis == 0:
            print("Please analyze data before archiving results")
            return
        if self.status_archive_results == 1:
            print("Results already archived")
            return
        #ARCHIVE SECTION
        print("SIMPLE MEASUREMENT - STORE RESULTS IN DATABASE")
        constantfiles = glob.glob('output_fembTest_simpleMeasurement_constants_' + '*.txt')
        if len(constantfiles) == 0:
            print("Could not find SIMPLE MEASUREMENT constants")
            #sys.exit(0)
            return
        constantfilename = max(constantfiles, key=os.path.getctime)
        #open constants file
        input_file = open(constantfilename, 'r')

        #open database, insert results
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from setup_database import Base, noise_test, noise_test_ch_result

        engine = create_engine('sqlite:///database_simpleMeasurement.db')
        Base.metadata.bind = engine
        DBSession = sessionmaker(bind=engine)
        session = DBSession()

        #enter noise test
        new_test = noise_test()
        new_test.test_id = int(self.femb_rootdata.date)
        new_test.board_id = 10
        session.add(new_test)
        session.commit()

        #loop through constants file, get channel specific results
        for line in input_file:
            #print( line )
            data = line.split()
            if len(data) != 5:
                continue
            gain = int(data[0])
            shape = int(data[1])
            base = int(data[2])
            ch = int(data[3])
            rms = int(data[4])
            #enter new channel result
            new_ch_result = noise_test_ch_result()
            new_ch_result.test_id = int(self.femb_rootdata.date)
            new_ch_result.fegain = gain
            new_ch_result.feshape = shape
            new_ch_result.baseline = base
            new_ch_result.ch_id = ch
            new_ch_result.ch_rms = rms
            session.add(new_ch_result)
            session.commit()

        input_file.close()
        self.status_archive_results = 1

def main():
    femb_test = FEMB_TEST()
    femb_test.check_setup()
    femb_test.record_data()
    femb_test.do_analysis()
    #femb_test.archive_results()

if __name__ == '__main__':
    main()
