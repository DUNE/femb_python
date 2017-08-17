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
import json

#import femb_python package modules
from femb_python.configuration import CONFIG
from femb_python.write_data import WRITE_DATA
from femb_python.configuration.cppfilerunner import CPP_FILE_RUNNER

class QUADADC_TEST_SIMPLE(object):

    def __init__(self, datadir="data", outlabel="simpleMeasurement",asicnum=0,isRoomTemp=True):
        #set internal variables
        self.datadir = datadir
        self.outlabel = outlabel + str("_asic_") + str(asicnum)
        self.outpathlabel = os.path.join(self.datadir, self.outlabel)
        self.asicnum = int(asicnum)

        print("Test type\t" + str(self.outlabel) )
        print("Data path\t" + str(datadir) )
        print("ASIC socket #\t" + str(self.asicnum) )

        #import femb_udp modules from femb_udp package
        self.femb_config = CONFIG()
        self.write_data = WRITE_DATA(datadir)

        #set appropriate UDP packet size
        self.write_data.femb.MAX_PACKET_SIZE = 8000 #should be larger than largest expected packet size
        self.cppfr = CPP_FILE_RUNNER()
	
        #set test module status variables
        self.status_check_setup = 0
        self.status_record_data = 0
        self.status_do_analysis = 0
        self.status_archive_results = 0
        self.isRoomTemp = isRoomTemp

        #define json output
        self.jsondict = {'type':'quadAdcTest_simple'}
        #self.jsondict['version'] = '1.0'
        self.jsondict['timestamp']  = str(self.write_data.date)
        self.jsondict['asicnum']  = str(self.asicnum)

    def check_setup(self):
        #CHECK STATUS AND INITIALIZATION
        print("SIMPLE MEASUREMENT - CHECKING READOUT STATUS")
        self.status_check_setup = 0

        #make sure output directory exists (should catch permissions issues etc)
        isDir = self.write_data.assure_filedir()
        if isDir == None:
            print("Error running test - Output data directory note created.")
            return

        #check if register interface is working
        print("Checking register interface")
        regVal = self.femb_config.femb.read_reg( self.femb_config.REG_FIRMWARE_VERSION )
        if (regVal == None):
            print("Error running test - register interface is not working.")
            print(" Turn on or debug UDP readout.")       
            return
        if ( regVal < 0 ):
            print("Error running test - register interface is not working.")
            print(" Turn on or debug UDP readout.")       
            return
        print("Read register 6, value = " + str( hex( regVal ) ) )

        #check for any problems in input variables
        #check that input ASIC # is correct
        if self.asicnum > self.femb_config.NASICS :
            print( "Error running test - Invalid ASIC socket # specified, ending test" )
            return

        #initialize readout to known working state
        print("Initializing board")
        self.femb_config.initBoard()

        #test firmware version goes here
        #if self.femb_config.checkFirmwareVersion() == False:
        #    print('Error running doFembTest - Invalid firmware and/or register read error')
        #    return

        #check if data streaming is working, assume it's ON after initialize
        print("Checking data streaming")
        testData = self.write_data.femb.get_data_packets(1)
        if testData == None:
            print("Error running test - board is not streaming data.")
            print(" Turn on and initialize FEMB UDP readout.")
            return
        if len(testData) == 0:
            print("Error running test - board is not streaming data.")
            print(" Turn on and initialize FEMB UDP readout.")
            return

        print("Received data packet " + str(len(testData[0])) + " bytes long")

        #check for analysis executables
        if not self.cppfr.exists('test_measurements/quadAdcTester/code/parseBinaryFile'):    
            print('Error running test - parseBinaryFile executable not found, run setup.sh')
            return
        if not self.cppfr.exists('test_measurements/quadAdcTester/code/processNtuple_simpleMeasurement'):
            print('Error running test - processNtuple_simpleMeasurement executable not found, run setup.sh')
            return

        #Setup is ok
        print("SIMPLE MEASUREMENT - READOUT STATUS OK" + "\n")
        self.status_check_setup = 1

    def record_data(self):
        if self.status_check_setup == 0:
            print("Error running test - Please run check_setup method before trying to take data")
            return
        if self.status_record_data == 1:
            print("Error running test - Data already recorded. Reset/restat GUI to begin a new measurement")
            return

        #MEASUREMENT SECTION
        print("SIMPLE MEASUREMENT - RECORDING DATA")

        #wait to make sure HS link is back on after check_setup function
        sleep(1.)

        #setup output file and record data
        self.write_data.filename = self.outlabel+".bin"
        print("Recording " + self.write_data.filename )

        isOpen = self.write_data.open_file()
        if isOpen == 0 :
            print( "Error running test - Could not open output data file for writing, ending test" )

        #record data
        self.write_data.numpacketsrecord = 1000
        self.write_data.run = 0
        self.write_data.runtype = 0
        self.write_data.runversion = 0

        #loop over each ASIC, record some data
        subrun = 0
        asic = self.asicnum
        asicCh = 0
        self.femb_config.selectChannel(asic,asicCh)
        self.write_data.record_data(subrun, asic, asicCh)
        self.write_data.close_file()

        #Power off ASIC ?
        #self.femb_config.powerOffFemb()

        print("SIMPLE MEASUREMENT - DONE RECORDING DATA" + "\n")
        self.status_record_data = 1

    def do_analysis(self):
        if self.status_record_data == 0:
            print("Error running test - Please record data before analysis")
            return
        if self.status_do_analysis == 1:
            print("Error running test - Analysis already complete")
            return
        #ANALYSIS SECTION

        print("SIMPLE MEASUREMENT - ANALYZING AND SUMMARIZING DATA")

        #parse binary
        self.cppfr.run("test_measurements/quadAdcTester/code/parseBinaryFile", [self.write_data.data_file_path])

        #check for parsed file here
        if os.path.isfile( "output_parseBinaryFile.root" ) == False:
            print("Error running test - parsed data file not found.")
            return

        #run analysis program
        parseBinaryFile = "output_parseBinaryFile.root"
        self.cppfr.run("test_measurements/quadAdcTester/code/processNtuple_simpleMeasurement",  [parseBinaryFile])

        #check for online analysis result files here
        if os.path.isfile( "output_processNtuple_simpleMeasurement.root" ) == False:
            print("Error running test - parsed data file not found.")
            return

        #update output file names
        parseBinaryFile = self.outpathlabel + "-parseBinaryFile.root"
        call(["mv", "output_parseBinaryFile.root" , parseBinaryFile])

        processNtupleFile = self.outpathlabel + "-processNtupleFile.root"
        call(["mv", "output_processNtuple_simpleMeasurement.root" , processNtupleFile])

        summaryPlot = self.outpathlabel + "-summaryPlot.png"
        call(["mv", "summaryPlot_simpleMeasurement.png" , summaryPlot])

        print("SIMPLE MEASUREMENT - DONE ANALYZING AND SUMMARIZING DATA" + "\n")
        self.status_do_analysis = 1

    def archive_results(self):
        #NOTE: GENERALLY ALLOW ARCHIVE PROCESS TO RUN EVEN IF OTHER STEPS FAIL 
        #if self.status_check_setup == 0 :
        #     print("Check setup status is 0, not archiving data")
        #     return
        #if self.status_do_analysis == 0:
        #    print("Please analyze data before archiving results")
        #    return
        if self.status_archive_results == 1:
            print("Error running test - Results already archived")
            return
        #ARCHIVE SECTION
        print("SIMPLE MEASUREMENT - ARCHIVE")

        #add summary variables to output
        self.jsondict['filedir'] = str( self.write_data.filedir )
        self.jsondict['status_check_setup'] = str(self.status_check_setup)
        self.jsondict['status_record_data'] = str(self.status_record_data)
        self.jsondict['status_do_analysis'] = str(self.status_do_analysis)
        self.jsondict['status_archive_results'] = str(1)

        #dump results into json
        jsonFile = self.outpathlabel + "-results.json"
        with open( jsonFile , 'w') as outfile:
            json.dump( self.jsondict, outfile, indent=4)

        print("SIMPLE MEASUREMENT - DONE ARCHIVING" + "\n")
        self.status_archive_results = 1

def main():
    '''
    Run a simple measurement.
    '''
    #default parameters
    datadir = "data"
    asicsockets = [0]
    isRoomTemp = True

    #check for JSON file input
    if len(sys.argv) == 2 :
        params = json.loads(open(sys.argv[1]).read())
        if 'datadir' in params:
            datadir = params['datadir']
        if 'asicsockets' in params:
            asicsockets = params['asicsockets']
        if 'isRoomTemp' in params:
            isRoomTemp = params['isRoomTemp']

    #do some sanity checks on input parameters
    if len(asicsockets) > 4 :
        print("Error running test - Invalid # of ASICs specified")
        return
      
    #actually run the test, one per FEMB slot
    for asicnum in asicsockets:
        quadadc_test = QUADADC_TEST_SIMPLE(datadir,"simpleMeasurement",asicnum,isRoomTemp)
        quadadc_test.check_setup()
        quadadc_test.record_data()
        quadadc_test.do_analysis()
        quadadc_test.archive_results()

if __name__ == '__main__':
    main()
