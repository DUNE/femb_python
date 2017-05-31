from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import
from builtins import range
from builtins import int
from builtins import str
from builtins import hex
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

class FEMB_TEST_GAIN(object):

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

        #misc variables
        self.fembNum = 0
        self.gain = 0
        self.shape = 0
        self.base = 0

        #json output, note version number defined here
        self.jsonlist = [('type','quadFeAsic_gain')]
        self.jsonlist.append( ('version','1.0') )
        self.jsonlist.append( ('timestamp',str(self.write_data.date)) )

    def reset(self):
        self.status_check_setup = 0
        self.status_record_data = 0
        self.status_do_analysis = 0
        self.status_archive_results = 0

    def check_setup(self):
        #CHECK STATUS AND INITIALIZATION
        print("GAIN MEASUREMENT - CHECKING READOUT STATUS")
        self.status_check_setup = 0

        #check local directory structure, available space
        if os.path.isdir("./data") == False:
            print("Error running doFembTest - data directory not found, making now.")
            os.makedirs("./data")

            #check if directory was created sucessfully
            if os.path.isdir("./data") == False:
                print(" Please check that femb_python package directory structure is intact.")
                return

        #check if register interface is working
        print("Checking register interface")
        regVal = self.write_data.femb.read_reg(5)
        if (regVal == None) or (regVal == -1):
            print("Error running doFembTest - FEMB register interface is not working.")
            print(" Turn on or debug FEMB UDP readout.")       
            return
        print("Read register 5, value = " + str( hex( regVal ) ) )

        #initialize FEMB to known state
        print("Initializing board")
        self.femb_config.initBoard()
        #self.femb_config.initFemb(self.femb_config.fembNum)

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

        print("GAIN MEASUREMENT - READOUT STATUS OK" + "\n")
        self.status_check_setup = 1

    def record_data(self):
        if self.status_check_setup == 0:
            print("Please run check_setup method before trying to take data")
            return
        if self.status_record_data == 1:
            print("Data already recorded. Reset/restat GUI to begin a new measurement")
            return
        #MEASUREMENT SECTION
        print("GAIN MEASUREMENT - RECORDING DATA")

        #initialize FEMB configuration to known state
        print("FE ASIC Settings: Gain " + str(self.gain) + ", Shaping Time " + str(self.shape) + ", Baseline " + str(self.base) )
        self.femb_config.feasicGain = self.gain
        self.femb_config.feasicShape = self.shape
        self.femb_config.feasicBaseline = self.base
        self.femb_config.configFeAsic()

        #wait to make sure HS link is back on
        sleep(0.5)

        #set output file
        #self.write_data.filedir = "data/"
        self.write_data.filedir = "data/gainMeasurement_" + str(self.write_data.date) + "/"
        #self.write_data.filename = "rawdata_gainMeasurement_" + str(self.write_data.date) + ".bin"
        self.write_data.filename = "rawdata_gainMeasurement_" + str(self.write_data.date) + "_femb_" \
                                   + str(self.fembNum) + "_g_" + str(self.gain) + "_s_" + str(self.shape) + "_b_" + str(self.base) + ".bin"

        print("Recording " + self.write_data.filename )
        self.write_data.numpacketsrecord = 50
        self.write_data.run = 0
        self.write_data.runtype = 0
        self.write_data.runversion = 0

        #setup output file and record data
        self.write_data.open_file()
        subrun = 0

        #disable pulser
        self.femb_config.setInternalPulser(0,0x0)

        #take initial noise data run
        for asic in range(0,4,1):
            self.femb_config.turnOnAsic(asic)
            for asicCh in range(0,16,1):
                self.femb_config.selectChannel(asic,asicCh)
                self.write_data.record_data(subrun, asic, asicCh)
            
        #turn ASICs back on, start pulser section
        self.femb_config.turnOnAsics()
        subrun = 1
        #loop over pulser configurations, each configuration is it's own subrun
        #loop over signal sizes
        for p in range(1,64,1):
        #for p in range(0,15,1):
        #for p in [0x0,0x1,0x3,0x7,0xF,0x1F]:
            pVal = int(p)
            #pVal = 1024 + int(p)*256
            #self.femb_config.femb.write_reg_bits( 5, 0,0x3F,pVal) #test pulse amplitude
            self.femb_config.setInternalPulser(1,pVal)
            print("Pulse amplitude " + str(pVal) )

            #loop over channels
            for asic in range(0,4,1):
                for asicCh in range(0,16,1):
                    self.femb_config.selectChannel(asic,asicCh)
                    self.write_data.record_data(subrun, asic, asicCh)

            #increment subrun, important
            subrun = subrun + 1

        #close file
        self.write_data.close_file()

        #turn off pulser
        self.femb_config.setInternalPulser(1,0)

        #turn off ASICs
        self.femb_config.turnOffAsics()

        print("GAIN MEASUREMENT - DONE RECORDING DATA" + "\n")
        self.status_record_data = 1

    def do_analysis(self):
        if self.status_record_data == 0:
            print("Please record data before analysis")
            return
        if self.status_do_analysis == 1:
            print("Analysis already complete")
            return
        #ANALYSIS SECTION
        print("GAIN MEASUREMENT - ANALYZING AND SUMMARIZING DATA")

        #parse binary
        self.cppfr.run("test_measurements/feAsicTest/parseBinaryFile", [str( self.write_data.filedir ) + str( self.write_data.filename ) ])

        #run analysis program
        parsedName = "output_parseBinaryFile_" + self.write_data.filename + ".root"
        call(["mv", "output_parseBinaryFile.root" , str( self.write_data.filedir ) + str(parsedName) ])
        self.cppfr.run("test_measurements/feAsicTest/processNtuple_gainMeasurement",  [str( self.write_data.filedir ) + str(parsedName) ])
        resultName = "output_processNtuple_gainMeasurement_" + self.write_data.filename + ".root"
        call(["mv", "output_processNtuple_gainMeasurement.root" , str( self.write_data.filedir ) + str(resultName) ])
        plotName = "summaryPlot_" + self.write_data.filename + ".png"
        call(["mv", "summaryPlot_gainMeasurement.png" , str( self.write_data.filedir ) + str(plotName) ])
        jsonName = "output_processNtuple_gainMeasurement_" + self.write_data.filename + ".json"
        call(["mv", "output_processNtuple_gainMeasurement.json" , str( self.write_data.filedir ) + str(jsonName) ])

        #summary plot
        print("GAIN MEASUREMENT - DISPLAYING SUMMARY PLOT, CLOSE PLOT TO CONTINUE")
        call(["display",str( self.write_data.filedir ) + str(plotName) ])

        print("GAIN MEASUREMENT - DONE ANALYZING AND SUMMARIZING DATA" + "\n")
        self.status_do_analysis = 1

    def archive_results(self):
        #if self.status_do_analysis == 0:
        #    print("Please analyze data before archiving results")
        #    return
        #if self.status_archive_results == 1:
        #    print("Results already archived")
        #    return
        #ARCHIVE SECTION
        print("GAIN MEASUREMENT - ARCHIVE")

        self.jsonlist.append( ('check_setup',self.status_check_setup) )
        self.jsonlist.append( ('record_data',self.status_record_data) )
        self.jsonlist.append( ('do_analysis',self.status_do_analysis) )
        self.jsonlist.append( ('filedir', str( self.write_data.filedir ) ) )
        self.jsonlist.append( ('config_gain', self.gain ) )
        self.jsonlist.append( ('config_shape', self.shape ) )
        self.jsonlist.append( ('config_base', self.base ) )
       
        #print( self.jsonlist )
        jsonoutput = json.dumps(self.jsonlist, indent=4)
        print( jsonoutput )
 
        #dump results into json
        jsonName = "json_" + str(self.write_data.date) + ".json"
        with open( str(jsonName) , 'w') as outfile:
          json.dump(jsonoutput, outfile)
        call(["mv", str(jsonName) , str( self.write_data.filedir ) + str(jsonName) ])

        #placeholder
        print("GAIN MEASUREMENT - DONE ARCHIVING" + "\n")
        self.status_archive_results = 1

def main():
    for g in range(2,3,1):
      for s in range(1,2,1):
        for b in range(0,1,1):
          femb_test = FEMB_TEST_GAIN()
          femb_test.fembNum = int(0)
          femb_test.gain = int(g)
          femb_test.shape = int(s)
          femb_test.base = int(b)

          femb_test.check_setup()
          femb_test.record_data()
          femb_test.do_analysis()
          femb_test.archive_results()

if __name__ == '__main__':
    main()
