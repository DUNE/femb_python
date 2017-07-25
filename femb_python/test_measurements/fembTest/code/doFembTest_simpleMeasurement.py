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

from femb_python.configuration import CONFIG
from femb_python.write_data import WRITE_DATA
from femb_python.configuration.cppfilerunner import CPP_FILE_RUNNER

#specify location of femb_udp package

class FEMB_TEST_SIMPLE(object):

    def __init__(self, datadir="data", outlabel="simpleMeasurement",fembNum=0):
        #set internal variables
        self.outlabel = outlabel
        self.outpathlabel = os.path.join(datadir, outlabel)
        self.fembNum = int(fembNum)

        print("Test type\t" + str(self.outlabel) )
        print("Data path\t" + str(datadir) )
        print("FEMB #\t" + str(self.fembNum) )

        #import femb_udp modules from femb_udp package
        self.femb_config = CONFIG()
        self.write_data = WRITE_DATA(datadir)
        #set appropriate packet size
        self.write_data.femb.MAX_PACKET_SIZE = 8000
	
        #set status variables
        self.status_check_setup = 0
        self.status_record_data = 0
        self.status_do_analysis = 0
        self.status_archive_results = 0
        self.cppfr = CPP_FILE_RUNNER()

        #json output, note module version number defined here
        self.jsondict = {'type':'fembTest_simple'}
        self.jsondict['version'] = '1.0'
        self.jsondict['timestamp']  = str(self.write_data.date)

    def check_setup(self):
        #CHECK STATUS AND INITIALIZATION
        print("SIMPLE MEASUREMENT - CHECKING READOUT STATUS")
        self.status_check_setup = 0

        #make sure output directory exists
        self.write_data.assure_filedir()

        #check if register interface is working
        print("Checking register interface")
        regVal = self.femb_config.femb.read_reg(6)
        if (regVal == None):
            print("Error running doFembTest - FEMB register interface is not working.")
            print(" Turn on or debug FEMB UDP readout.")       
            return
        if ( regVal < 0 ):
            print("Error running doFembTest - FEMB register interface is not working.")
            print(" Turn on or debug FEMB UDP readout.")       
            return
        print("Read register 6, value = " + str( hex( regVal ) ) )

        #check that femb number is valid
        if ( int(self.fembNum) < 0 ) or ( int( self.fembNum) >= self.femb_config.NFEMBS ):
            print("Error running doFembTest - Invalid FEMB # specified.")
            return    

        #do firmware version check HERE
        self.femb_config.selectFemb(self.fembNum)
        #regVal = self.femb_config.femb.read_reg(257)

        #initialize FEMB to known state
        print("Initializing board")
        self.femb_config.initFemb( self.fembNum )

        #check if data streaming is working
        print("Checking data streaming")
        testData = self.write_data.femb.get_data_packets(1)
        if testData == None:
            print("Error running doFembTest - FEMB is not streaming data.")
            print(" Turn on and initialize FEMB UDP readout.")
            return
        if len(testData) == 0:
            print("Error running doFembTest - FEMB is not streaming data.")
            print(" Turn on and initialize FEMB UDP readout.")
            return

        print("Received data packet " + str(len(testData[0])) + " bytes long")

        #check for analysis executables
        if not self.cppfr.exists('test_measurements/fembTest/code/parseBinaryFile'):    
            print('parseBinaryFile not found, run setup.sh')
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

        self.femb_config.setInternalPulser(1,0x3F)

        #wait to make sure HS link is back on after check_setup
        sleep(0.5)

        #setup output file and record data
        self.write_data.filename = self.outlabel+".bin"
        print("Recording " + self.write_data.filename )

        isOpen = self.write_data.open_file()
        if isOpen == 0 :
            print( "Error running doFembTest - Could not open output data file for writing, ending test" )
        subrun = 0

        #record data
        self.write_data.numpacketsrecord = 100
        self.write_data.run = 0
        self.write_data.runtype = 0
        self.write_data.runversion = 0

        asicCh = 0
        for asic in range(0,8,1):
          self.femb_config.selectChannel(asic,asicCh)
          self.write_data.record_data(subrun, asic, asicCh)
        self.write_data.close_file()

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
        self.cppfr.run("test_measurements/fembTest/code/parseBinaryFile", [self.write_data.data_file_path])

        #run analysis program
        parseBinaryFile = self.outpathlabel + "-parseBinaryFile.root"
        call(["mv", "output_parseBinaryFile.root" , parseBinaryFile])
        self.cppfr.run("test_measurements/fembTest/code/processNtuple_simpleMeasurement",  [parseBinaryFile])

        processNtupleFile = self.outpathlabel + "-processNtupleFile.root"
        call(["mv", "output_processNtuple_simpleMeasurement.root" , processNtupleFile])

        summaryPlot = self.outpathlabel + "-summaryPlot.png"
        call(["mv", "summaryPlot_simpleMeasurement.png" , summaryPlot])

        print("SIMPLE MEASUREMENT - DONE ANALYZING AND SUMMARIZING DATA" + "\n")
        self.status_do_analysis = 1

    def archive_results(self):
        #if self.status_do_analysis == 0:
        #    print("Please analyze data before archiving results")
        #    return
        #if self.status_archive_results == 1:
        #    print("Results already archived")
        #    return
        #ARCHIVE SECTION
        print("SIMPLE MEASUREMENT - ARCHIVE")

        #add summary variables to output
        self.jsondict['femb']  = self.fembNum
        self.jsondict['filedir'] = str( self.write_data.filedir )
        self.jsondict['status_check_setup'] = self.status_check_setup
        self.jsondict['status_record_data'] = self.status_record_data
        self.jsondict['status_do_analysis'] = self.status_do_analysis
        self.jsondict['status_archive_results'] = 1

        #dump results into json
        jsonFile = self.outpathlabel + "-results.json"
        with open( jsonFile , 'w') as outfile:
            json.dump( self.jsondict, outfile, indent=4)

        print("SIMPLE MEASUREMENT - DONE ARCHIVING" + "\n")
        self.status_archive_results = 1

def main():
    '''
    Run a simple FEMB measurement.
    '''

    datadir = "data"
    fembNum = 1
    if len(sys.argv) == 2 :
      params = json.loads(open(sys.argv[1]).read())
      datadir = params['datadir']
      fembNum = params['fembNum']
      
    femb_test = FEMB_TEST_SIMPLE(datadir,"simpleMeasurement",fembNum)
    femb_test.check_setup()
    femb_test.record_data()
    femb_test.do_analysis()
    femb_test.archive_results()

if __name__ == '__main__':
    main()
