#!/usr/bin/env python3
import os
import sys
import time
import json

from femb_python.configuration import CONFIG
from femb_python.femb_udp import FEMB_UDP
from femb_python.test_measurements.wibTestStand.doFembTest_simpleMeasurement import main as simpleMeasurement 

class FEMB_POWER_CYCLE_TEST(object):

    def __init__(self):
        #set status variables
        self.status_check_setup = 0
        self.status_record_data = 0
        self.status_do_analysis = 0
        self.status_archive_results = 0
        self.config = CONFIG()
        self.ntries = 5
        #initialize FEMB UDP object
        self.wibudp = FEMB_UDP()
        self.wibudp.UDP_PORT_WREG = 32000 #WIB PORTS
        self.wibudp.UDP_PORT_RREG = 32001
        self.wibudp.UDP_PORT_RREGRESP = 32002
        
    def check_setup(self,params):
        #CHECK STATUS AND INITIALIZATION
        print("Initialize board")
        #self.config.initBoard()

        self.params = dict(params)

        if False:
            print("CHECK SETUP - Error")       
            return

        #CHECK STATUS SUCCEEDED
        print("CHECK SETUP - STATUS OK" + "\n")
        self.status_check_setup = 1
        
    def record_data(self):

        if self.status_check_setup == 0:
            print("RECORD DATA - Please run check_setup method before trying to take data")
            return
        if self.status_record_data == 1:
            print("RECORD DATA - Data already recorded. ")
            return
        
        for icycle in range(0,self.ntries):
            for ifemb in range(0,4):
                self.config.powerOffFemb(ifemb)
                self.config.powerOnFemb(ifemb)                                

            #pass arguments once that is set up
            #simpleMeasurement(self.params["paramfile"])
            simpleMeasurement()
        self.status_record_data = 1
        

    def do_analysis(self):
        if self.status_record_data == 0:
            print("DO ANALYSIS - Please record data before analysis")
            return
        if self.status_do_analysis == 1:
            print("DO ANALYSIS - Analysis already complete")
            return
        #ANALYSIS SECTION
        print("DO ANALYSIS")

        #ONLINE ANALYSIS GOES HERE

        #ANALYSIS SUCCEEDED
        print("DO ANALYSIS - DONE" + "\n")
        self.status_do_analysis = 1

    def archive_results(self):
        if self.status_do_analysis == 0:
            print("ARCHIVE RESULTS - Please analyze data before archiving results")
            return
        if self.status_archive_results == 1:
            print("ARCHIVE RESULTS -Results already archived")
            return
        #ARCHIVE SECTION
        print("ARCHIVE RESULTS")
        
        #ARCHIVING OF RESULTS GOES HERE

        #ARCHIVING SUCCEEDED
        print("ARCHIVE RESULTS - DONE" + "\n")
        self.status_archive_results = 1

def main():
        '''
        Run an example measurement.
        '''
        print( "POWER CYLCE TEST START")
        for arg in sys.argv :
            print( arg )
        import json
        params = json.loads(open(sys.argv[1]).read())
        
        print( params )

        #check for required parametes
        if 'datadir' in params:
            datadir = params['datadir']
        else:
            print( "EXAMPLE TEST - datadir not defined, return" )
            return None

        if 'outlabel' in params:
            outlabel = params['outlabel']
        else:
            print( "EXAMPLE TEST - outputlabel not defined, return" )
            return None

        #add additional parameter checks here

        #instantiate the actual test object, pass required parameters to internal variables
        powerCycleTest = FEMB_POWER_CYCLE_TEST()

        #Finally begin testing
        powerCycleTest.check_setup(params)
        powerCycleTest.record_data()
        powerCycleTest.do_analysis()
        powerCycleTest.archive_results()

        print( "EXAMPLE TEST DONE")        

if __name__ == '__main__':
        main()
