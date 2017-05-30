from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import
from builtins import hex
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

from femb_python.configuration import CONFIG
from femb_python.write_data import WRITE_DATA
from femb_python.configuration.cppfilerunner import CPP_FILE_RUNNER

#specify location of femb_udp package

class FEMB_TEST_SIMPLE(object):

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
            print("Error running doFembTest - data directory not found, making now.")
            os.makedirs("./data")

            #check if directory was created sucessfully
            if os.path.isdir("./data") == False:
                print(" Please check that femb_python package directory structure is intact.")
                return

        #create data-taking directory
        #print("doFembTest - creating data-taking directory : " + str( self.write_data.filedir ) )
        #os.makedirs( str( self.write_data.filedir ) )
        #if os.path.isdir( str( self.write_data.filedir ) ) == False:
        #    print("Error creating data-taking directory.")
        #    return

        #check if register interface is working
        print("Checking register interface")
        regVal = self.femb_config.femb.read_reg(6)
        if (regVal == None) or (regVal == -1):
            print("Error running doFembTest - FEMB register interface is not working.")
            print(" Turn on or debug FEMB UDP readout.")       
            return
        print("Read register 6, value = " + str( hex( regVal ) ) )

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

        print("SIMPLE MEASUREMENT - READOUT STATUS OK" + "\n")
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
        self.femb_config.configFeAsic()
        #self.femb_config.setInternalPulser(1,0x400)
        #self.femb_config.configFeAsic(0,0,0)
        #self.femb_config.setDacPulser(0,0x0000)
        #self.femb_config.setDacPulser(1,0xFF00)
        #self.femb_config.setInternalPulser(0,0x0)
        #self.femb_config.setInternalPulser(1,0x3f)

        #wait to make sure HS link is back on
        #sleep(0.5)

        #set output file
        #self.write_data.filedir = "data/"
        self.write_data.filedir = "data/simpleMeasurement_" + str(self.write_data.date) + "/"
        self.write_data.filename = "rawdata_simpleMeasurement_" + str(self.write_data.date) + ".bin"
        print("Recording " + self.write_data.filename )
        self.write_data.numpacketsrecord = 10
        self.write_data.run = 0
        self.write_data.runtype = 0
        self.write_data.runversion = 0

        #setup output file and record data
        isOpen = self.write_data.open_file()
        if isOpen == 0 :
            print( "Error running doFembTest - Could not open output data file for writing, ending test" )
        subrun = 0

        asicCh = 0
        for asic in range(0,4,1):
          for asicCh in range(0,16,1):
            self.femb_config.selectChannel(asic,asicCh)
            self.write_data.record_data(subrun, asic, asicCh)
        self.write_data.close_file()

        #reset configuration to known state
        #self.femb_config.configFeAsic(0,0,0)

        print("SIMPLE MEASUREMENT - DONE RECORDING DATA" + "\n")
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

        #parse binary
        self.cppfr.run("test_measurements/feAsicTest/parseBinaryFile", [str( self.write_data.filedir ) + str( self.write_data.filename ) ])

        #run analysis program
        newName = "output_parseBinaryFile_" + self.write_data.filename + ".root"
        call(["mv", "output_parseBinaryFile.root" , str( self.write_data.filedir ) + str(newName) ])
        self.cppfr.run("test_measurements/feAsicTest/processNtuple_simpleMeasurement",  [str( self.write_data.filedir ) + str(newName) ])

        #move result to data directory
        newName = "output_processNtuple_simpleMeasurement_" + self.write_data.filename + ".root"
        call(["mv", "output_processNtuple_simpleMeasurement.root" , str( self.write_data.filedir ) + str(newName) ])
        newName = "summaryPlot_" + self.write_data.filename + ".png"
        call(["mv", "summaryPlot_simpleMeasurement.png" , str( self.write_data.filedir ) + str(newName) ])

        #summary plot
        #print("SIMPLE MEASUREMENT - DISPLAYING SUMMARY PLOT, CLOSE PLOT TO CONTINUE")
        #call(["display",str( self.write_data.filedir ) + str(newName) ])

        print("SIMPLE MEASUREMENT - DONE ANALYZING AND SUMMARIZING DATA" + "\n")
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
        #placeholder
        print("SIMPLE MEASUREMENT - DONE STORING RESULTS IN DATABASE" + "\n")
        self.status_archive_results = 1

def main():

    femb_test = FEMB_TEST_SIMPLE()
    femb_test.check_setup()
    femb_test.record_data()
    femb_test.do_analysis()

if __name__ == '__main__':
    main()
