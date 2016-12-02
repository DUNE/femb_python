import sys
import string
from subprocess import call
from time import sleep
import os
import ntpath
import glob
import struct

#specify location of femb_udp package

class FEMB_TEST:

    def __init__(self):

        #import femb_udp modules from femb_udp package
        from femb_python.configuration.femb_config_wib_sbnd import FEMB_CONFIG
        self.femb_config = FEMB_CONFIG()

        #set appropriate packet size for WIB
        self.femb_config.femb.MAX_PACKET_SIZE = 8000
	
        #set status variables
        self.status_check_setup = 0
        self.status_record_data = 0
        self.status_do_analysis = 0
        self.status_archive_results = 0

    def check_setup(self):
        #CHECK STATUS AND INITIALIZATION
        print("SIMPLE MEASUREMENT - CHECKING READOUT STATUS")
        self.status_check_setup = 0
        #check if readout is working
        testData = self.femb_config.femb.get_data_packets(1)
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
        #if os.path.isfile('./processNtuple') == False:    
        #    print('processNtuple not found, run setup.sh')
        #    #sys.exit(0)
        #    return
        #if os.path.isfile('./summaryAnalysis_doFembTest_simpleMeasurement') == False:    
        #    print('summaryAnalysis_doFembTest_simpleMeasurement not found, run setup.sh')
        #    #sys.exit(0)
        #    return
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

        #initialize readout channel range
        self.minchan = 0
        self.maxchan = 127

        #initialize FEMB configuration to known state
        self.femb_config.configFeAsic(0,0,0)
        #wait to make sure HS link is back on
        sleep(0.5)

        #Set ADC test mode
        #self.femb_config.femb.write_reg_bits(3,31,1,0)
        #val = self.femb_config.femb.read_reg(3)
        #print( "Reg 3 " + str(hex(val) ) )

        #config FE ASICs
        filename = "data/output_simpleMeasurement.bin"
        print("Recording " + filename)
        self.filename = filename
        self.numpacketsrecord = 100
        self.run = 0
        self.subrun = 0
        self.runtype = 1
        self.runversion = 0
        self.par1 = 0
        self.par2 = 0
        self.par3 = 0
        self.gain = 0
        self.shape = 0
        self.base = 0

        #setup output file
        FILE = open(str(filename),"wb") 

        #loop over ASICs
        #self.femb_config.selectChannel(0,1)
        for asic in range(0,8,1):
          self.femb_config.selectChannel(asic,0)

          #record the data
          testData = self.femb_config.femb.get_data_packets(100)
          if len(testData) == 0:
            continue
          for packet in testData:
            #write a header
            FILE.write(b'\x00\x00')
            FILE.write(b'\xDE\xAD')
            FILE.write(b'\xBE\xEF')
            FILE.write(b'\x00\x00')
            FILE.write(b'\xBA\x5E')
            FILE.write(struct.pack('!H', int(asic) ))
            FILE.write(packet)
        #Close data file
        FILE.close()

        self.femb_config.configFeAsic(0,0,0)

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
        #self.newlist = "filelist_processData_doFembTest_simpleMeasurement_" + str(self.femb_rootdata.date) + ".txt"
        self.newlist = "filelist_processData_doFembTest_simpleMeasurement_" + ".txt"
        #input_file = open(self.filelist.name, 'r')
        input_file = open("filelist_doFembTest_simpleMeasurement_.txt", 'r')
        output_file = open( self.newlist, "w")
        for line in input_file:
            filename = str(line[:-1])
            #print filename
            #call(["./processNtuple", str(line[:-1]) ])
            call(["./processNtuple_noRootTree", str(line[:-1]) ])
            #rootfiles = glob.glob('output_processNtuple_output_femb_rootdata_doFembTest_' + str(self.femb_rootdata.date) + '*.root')
            rootfiles = glob.glob('output_processNtuple_output_doFembTest' + '*.root')
            if len(rootfiles) == 0:
                print("Processing error detected, needs debugging. Exiting now!")
                sys.exit(0)
                #continue
            newname = max(rootfiles, key=os.path.getctime)
            call(["mv",newname,"data/."])
            newname = "data/" + newname
            output_file.write(newname + "\n")
            print(filename)
            print(newname)
        input_file.close()
        output_file.close()
        #run summary program
        #call(["./summaryAnalysis_doFembTest_simpleMeasurement", self.newlist ])
        #self.status_do_analysis = 1

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
    #femb_test.status_check_setup = 1
    femb_test.record_data()
    #femb_test.status_record_data = 1
    #femb_test.do_analysis()
    #femb_test.archive_results()

if __name__ == '__main__':
    main()
