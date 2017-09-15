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

class FEMB_TEST_ADCSCAN(object):

    def __init__(self, datadir="data", outlabel="adcscan",fembNum=0):
        #set internal variables
        self.datadir = datadir
        self.outlabel = outlabel + str("_femb_") + str(fembNum)
        self.outpathlabel = os.path.join(self.datadir, self.outlabel)
        self.fembNum = int(fembNum)

        print( "FEMB # " + str(fembNum) )

        #import femb_udp modules from femb_udp package
        self.femb_config = CONFIG()
        self.write_data = WRITE_DATA(self.datadir)
        #set appropriate packet size
        self.write_data.femb.MAX_PACKET_SIZE = 8000
        self.cppfr = CPP_FILE_RUNNER()
	
        #set status variables
        self.status_check_setup = 0
        self.status_record_data = 0
        self.status_do_analysis = 0
        self.status_archive_results = 0

        #misc variables
        self.gain = 0
        self.shape = 0
        self.base = 0
        self.leakage = 0
        self.leakagex10 = 0
        self.buffer = 0
        self.acdc = 0
        self.useInternalPulser = False
        self.useExtAdcClock = False
        self.isRoomTemp = False
        self.isAPA = False
        self.useDefaultGainFactor = False

        #json output, note module version number defined here
        self.jsondict = {'type':'fembTest_gain'}
        self.jsondict['version'] = '1.0'
        self.jsondict['timestamp']  = str(self.write_data.date)

    def check_setup(self):
        #CHECK STATUS AND INITIALIZATION
        print("MEASUREMENT - CHECKING READOUT STATUS")
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

        #assign FEMB # to test 
        self.femb_config.selectFemb(self.fembNum)

        #initialize FEMB to known state
        print("Initializing board")
        self.femb_config.feasicGain = self.gain
        self.femb_config.feasicShape = self.shape
        self.femb_config.feasicBaseline = self.base
        self.femb_config.feasicLeakageVal = self.leakage
        self.femb_config.feasicLeakagex10Val = self.leakagex10
        self.femb_config.bufVal = self.buffer
        self.femb_config.acdcVal = self.acdc
        self.femb_config.feasicEnableTestInput = 0 #important
        self.femb_config.useExtAdcClock = self.useExtAdcClock
        self.femb_config.isRoomTemp = self.isRoomTemp
        #self.femb_config.printParameters()
        self.femb_config.initFemb()

        #test firmware versions
        if self.femb_config.checkFirmwareVersion() == False:
            print('Error running doFembTest - Invalid firmware and/or register read error')
            return

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

        if not self.cppfr.exists('test_measurements/fembTest/code/processNtuple_adcScan'):    
            print('parseBinaryFile not found, run setup.sh')
            return

        print("MEASUREMENT - READOUT STATUS OK" + "\n")
        self.status_check_setup = 1

    def record_data(self):
        if self.status_check_setup == 0:
            print("Please run check_setup method before trying to take data")
            return
        if self.status_record_data == 1:
            print("Data already recorded. Reset/restat GUI to begin a new measurement")
            return

        #MEASUREMENT SECTION
        print("MEASUREMENT - RECORDING DATA")

        #wait to make sure HS link is back on after check_setup
        sleep(5)

        #setup output file
        self.write_data.filename = self.outlabel+".bin"
        print("Recording " + self.write_data.filename )

        isOpen = self.write_data.open_file()
        if isOpen == 0 :
            print( "Error running doFembTest - Could not open output data file for writing, ending test" )
        subrun = 0

        #config FE ASICs
        print("FE ASIC Settings: Gain " + str(self.gain) + ", Shaping Time " + str(self.shape) + ", Baseline " + str(self.base) )
        print("FE ASIC Settings: Leakage Current " + str(self.leakage) + ", Leakage x10 " + str(self.leakagex10) )
        print("FE ASIC Settings: Output Buffer " + str(self.buffer) + ", AC/DC " + str(self.acdc) )
        self.femb_config.feasicGain = self.gain
        self.femb_config.feasicShape = self.shape
        self.femb_config.feasicBaseline = self.base
        self.femb_config.feasicLeakageVal = self.leakage
        self.femb_config.feasicLeakagex10Val = self.leakagex10
        self.femb_config.bufVal = self.buffer
        self.femb_config.acdcVal = self.acdc
        self.femb_config.feasicEnableTestInput = 1
        self.femb_config.useExtAdcClock = self.useExtAdcClock
        self.femb_config.isRoomTemp = self.isRoomTemp
        self.femb_config.configFeAsic()

        #disable pulsers
        self.femb_config.setInternalPulser(0,0x0)
        self.femb_config.setFpgaPulser(1,9)
        self.femb_config.femb.write_reg_bits( self.femb_config.REG_TP, 16,0xFFFF,0xC8) #test pulse frequency

        #print parameters to terminal
        self.femb_config.printParameters()

        #record data
        self.write_data.numpacketsrecord = 5000
        self.write_data.run = 0
        self.write_data.runtype = 0
        self.write_data.runversion = 0

        #loop over pulser configurations, each configuration is it's own subrun
        subrun = 0
        asicCh = 0
        for shift in range(0,25,1):
            shiftVal = int(shift)
            print("Pulse delay ", shiftVal)
            self.femb_config.femb.write_reg_bits( self.femb_config.REG_TP, 8,0xFF,shift) #test pulse delay
            #loop over channels
            for asic in range(0,8,1):
                self.femb_config.selectChannel(asic,asicCh)
                self.write_data.record_data(subrun, asic, asicCh)

            #increment subrun, important
            subrun = subrun + 1

        #close file
        self.write_data.close_file()

        #turn off FEMB
        self.femb_config.powerOffFemb(self.fembNum)

        print("MEASUREMENT - DONE RECORDING DATA" + "\n")
        self.status_record_data = 1

    def do_analysis(self):
        if self.status_record_data == 0:
            print("Please record data before analysis")
            return
        if self.status_do_analysis == 1:
            print("Analysis already complete")
            return
        #ANALYSIS SECTION
        print("MEASUREMENT - ANALYZING AND SUMMARIZING DATA")

        #parse binary
        self.cppfr.run("test_measurements/fembTest/code/parseBinaryFile", [self.write_data.data_file_path])

        #run analysis program
        parseBinaryFile = self.outpathlabel + "-parseBinaryFile.root"
        call(["mv", "output_parseBinaryFile.root" , parseBinaryFile])
        self.cppfr.run("test_measurements/fembTest/code/processNtuple_adcScan",  [parseBinaryFile])

        processNtupleFile = self.outpathlabel + "-processNtupleFile.root"
        call(["mv", "output_processNtuple_adcScan.root" , processNtupleFile])

        summaryPlot = self.outpathlabel + "-summaryPlot.png"
        call(["mv", "summaryPlot_adcScan.png" , summaryPlot])

        print("MEASUREMENT - DONE ANALYZING AND SUMMARIZING DATA" + "\n")
        self.status_do_analysis = 1

    def archive_results(self):
        #if self.status_check_setup == 0 :
        #     print("Check setup status is 0, not archiving data")
        #     return
        #if self.status_do_analysis == 0:
        #    print("Please analyze data before archiving results")
        #    return
        if self.status_archive_results == 1:
            print("Results already archived")
            return
        #ARCHIVE SECTION
        print("MEASUREMENT - ARCHIVE")

        #add summary variables to output
        self.jsondict['status_check_setup'] = str(self.status_check_setup)
        self.jsondict['status_record_data'] = str(self.status_record_data)
        self.jsondict['status_do_analysis'] = str(self.status_do_analysis)
        self.jsondict['status_archive_results'] = str(1)
        self.jsondict['filedir'] = str(self.write_data.filedir )
        self.jsondict['config_gain'] = str(self.gain)
        self.jsondict['config_shape'] = str(self.shape)
        self.jsondict['config_base'] = str(self.base)
        self.jsondict['useInternalPulser'] = str(self.useInternalPulser)
        self.jsondict['syncStatus'] = str(self.femb_config.syncStatus)

        #dump results into json
        jsonFile = self.outpathlabel + "-results.json"
        with open( jsonFile , 'w') as outfile:
            json.dump( self.jsondict, outfile, indent=4)

        print("MEASUREMENT - DONE STORING RESULTS IN DATABASE" + "\n")
        self.status_archive_results = 1

def main():
    #default data taking parameters
    datadir = "data"
    wibslots = [0,1,2,3]
    #wibslots = [1]
    gain = 3
    shape = 3
    base = 0
    useInternalPulser = False
    useExtAdcClock = True
    isRoomTemp = True
    isAPA = False
    useDefaultGainFactor = False

    #get parameters from input JSON file
    if len(sys.argv) == 2 :
        params = json.loads(open(sys.argv[1]).read())
        if 'datadir' in params:
            datadir = params['datadir']
        if 'outlabel' in params:
            outlabel = params['outlabel']
        if 'wibslots' in params:
            wibslots = params['wibslots']
        if 'gain' in params:
            gain = params['gain']
        if 'shape' in params:
            shape = params['shape']
        if 'base' in params:
            base = params['base']
        if 'useInternalPulser' in params:
            useInternalPulser = params['useInternalPulser']
        if 'useExtAdcClock' in params:
            useExtAdcClock = params['useExtAdcClock']
        if 'isRoomTemp' in params:
            isRoomTemp = params['isRoomTemp']
        if 'useDefaultGainFactor' in params:
            useDefaultGainFactor = params['useDefaultGainFactor']
        if 'isAPA' in params:
            isAPA = params['isAPA']

    #do some sanity checks
    if len(wibslots) > 4 :
        print("doFembTest - Invalid # of FEMBs specified")
        return

    #actually run the test, one per FEMB slot
    for femb in wibslots:
        femb_test = FEMB_TEST_ADCSCAN(datadir,"adcscan",femb)
        femb_test.gain = gain
        femb_test.shape = shape
        femb_test.base = base
        femb_test.useInternalPulser = useInternalPulser
        femb_test.useExtAdcClock = useExtAdcClock
        femb_test.isRoomTemp = isRoomTemp
        femb_test.isAPA = isAPA
        femb_test.useDefaultGainFactor = useDefaultGainFactor

        femb_test.check_setup()
        femb_test.record_data()
        femb_test.do_analysis()
        femb_test.archive_results()

if __name__ == '__main__':
    main()
