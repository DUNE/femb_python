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
        from femb_python.write_data import WRITE_DATA
        self.write_data = WRITE_DATA()
        #set appropriate packet size
        self.write_data.femb.MAX_PACKET_SIZE = 8000
	
        #set status variables
        self.status_check_setup = 0
        self.status_record_data = 0
        self.status_do_analysis = 0
        self.status_archive_results = 0

        #misc variables
        self.fembNum = 0
        self.gain = 0
        self.shape = 0
        self.base = 0

    def check_setup(self):
        #CHECK STATUS AND INITIALIZATION
        print("GAIN MEASUREMENT - CHECKING READOUT STATUS")
        self.status_check_setup = 0

        #check local directory structure, available space
        if os.path.isdir("./data") == False:
            print("Error running doFembTest - data directory not found.")
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
        #self.femb_config.initBoard()
        self.femb_config.initFemb(self.femb_config.fembNum)

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
        if os.path.isfile('./parseBinaryFile') == False:    
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
        #self.femb_config.configFeAsic(0,0,0)

        #wait to make sure HS link is back on
        sleep(0.5)

        #initialize pulser
        self.femb_config.femb.write_reg_bits( 16, 0,0x1,1) #test pulse enable
        self.femb_config.femb.write_reg_bits( 16, 8,0x1,1) #test pulse enable
        #self.femb_config.femb.write_reg_bits( 18, 0,0x1,1) #test pulse enable
        self.femb_config.femb.write_reg_bits( 5, 0,0x1F,0x0) #test pulse amplitude
        self.femb_config.femb.write_reg_bits( 5, 16,0xFFFF,0x100) #test pulse frequency
        self.femb_config.femb.write_reg_bits( 5, 8,0xFF,0x00) #test pulse delay

        #set output file
        self.write_data.filedir = "data/"
        #self.write_data.filename = "rawdata_gainMeasurement_" + str(self.write_data.date) + ".bin"
        self.write_data.filename = "rawdata_gainMeasurement_" + str(self.write_data.date) + "_femb_" \
                                   + str(self.fembNum) + "_g_" + str(self.gain) + "_s_" + str(self.shape) + "_b_" + str(self.base) + ".bin"

        print("Recording " + self.write_data.filename )
        self.write_data.numpacketsrecord = 100
        self.write_data.run = 0
        self.write_data.runtype = 0
        self.write_data.runversion = 0

        #setup output file and record data
        self.write_data.open_file()
        subrun = 0
        asicCh = 0

        #config FE ASICs
        print("FE ASIC Settings: Gain " + str(self.gain) + ", Shaping Time " + str(self.shape) + ", Baseline " + str(self.base) )
        #enable test input every channel
        sts = 1 #test input
        snc = self.base #baseline
        sg = self.gain #gain
        st = self.shape #shaping time
        sdc = 0 #coupling
        sdf = 0 #buffer amplifier
        for ch in range(0,128,1):
            pulseCh = int(ch)
            self.femb_config.feasic_ch_list[pulseCh].set_fechn_reg(sts, snc, sg, st, sdc, sdf )
            regNum = self.femb_config.feasic_ch_list[pulseCh].regNum
            regPos = self.femb_config.feasic_ch_list[pulseCh].regPos
            regVal = self.femb_config.feasic_ch_list[pulseCh].regval
            self.femb_config.femb.write_reg_bits( regNum, regPos,0xFF,regVal)
        self.femb_config.doFeAsicConfig()
        sleep(0.5)

        #loop over pulser configurations, each configuration is it's own subrun
        #loop over signal sizes
        #for p in range(0,64,1):
        for p in range(0,10,1):
            pVal = int(p)
            self.femb_config.femb.write_reg_bits( 5, 0,0x3F,pVal) #test pulse amplitude
            print("Pulse amplitude " + str(pVal) )

            #loop over channels
            for asic in range(0,8,1):
                self.femb_config.selectChannel(asic,asicCh)
                self.write_data.record_data(subrun, asic, asicCh)

            #increment subrun, important
            subrun = subrun + 1

        #close file
        self.write_data.close_file()

        #reset configuration to known state
        #self.femb_config.configFeAsic(0,0,0)

        #turn off pulser
        self.femb_config.femb.write_reg_bits( 16, 0,0x1,0) #test pulse enable
        self.femb_config.femb.write_reg_bits( 16, 8,0x1,0) #test pulse enable
        self.femb_config.femb.write_reg_bits( 5, 0,0x1F,0x00) #test pulse amplitude
        self.femb_config.femb.write_reg_bits( 5, 16,0xFFFF,0x100) #test pulse frequency
        self.femb_config.femb.write_reg_bits( 5, 8,0xFF,0x00) #test pulse delay

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
        call(["./parseBinaryFile", str( self.write_data.filedir ) + str( self.write_data.filename ) ])

        #run analysis program
        newName = "output_parseBinaryFile_" + self.write_data.filename + ".root"
        call(["mv", "output_parseBinaryFile.root" , str( self.write_data.filedir ) + str(newName) ])
        call(["./processNtuple_gainMeasurement",  str( self.write_data.filedir ) + str(newName) ])
        newName = "summaryPlot_" + self.write_data.filename + ".root"
        call(["mv", "summaryPlot_gainMeasurement.png" , str( self.write_data.filedir ) + str(newName) ])

        #summary plot
        #print("GAIN MEASUREMENT - DISPLAYING SUMMARY PLOT, CLOSE PLOT TO CONTINUE")
        #call(["display",str( self.write_data.filedir ) + str(newName) ])

        print("GAIN MEASUREMENT - DONE ANALYZING AND SUMMARIZING DATA" + "\n")
        self.status_do_analysis = 1

    def archive_results(self):
        if self.status_do_analysis == 0:
            print("Please analyze data before archiving results")
            return
        if self.status_archive_results == 1:
            print("Results already archived")
            return
        #ARCHIVE SECTION
        print("GAIN MEASUREMENT - STORE RESULTS IN DATABASE")
        #placeholder
        print("GAIN MEASUREMENT - DONE STORING RESULTS IN DATABASE" + "\n")
        self.status_archive_results = 1

def main():
    #loop over all 4 WIB FEMBs
    for femb in range(0,1,1):
      for g in range(0,4,1):
        for s in range(0,4,1):
          for b in range(0,1,1):
            femb_test = FEMB_TEST()
            femb_test.femb_config.selectFemb(femb)
            femb_test.fembNum = int(femb)
            femb_test.gain = int(g)
            femb_test.shape = int(s)
            femb_test.base = int(b)

            femb_test.check_setup()
            femb_test.record_data()
            femb_test.do_analysis()
            #femb_test.archive_results()

if __name__ == '__main__':
    main()
