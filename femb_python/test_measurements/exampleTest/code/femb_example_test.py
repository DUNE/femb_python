#!/usr/bin/env python3
import os
import sys
import time
import json

from femb_python.configuration import CONFIG

class EXAMPLE_TEST(object):

    def __init__(self):
        #set status variables
        self.status_check_setup = 0
        self.status_record_data = 0
        self.status_do_analysis = 0
        self.status_archive_results = 0

    def check_setup(self):
        #CHECK STATUS AND INITIALIZATION
        print("CHECK SETUP")
        self.status_check_setup = 0

        #add checks here
        print("CHECK SETUP - Testing something")
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
        print( "EXAMPLE TEST START")
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

        if 'outputlabel' in params:
            outputlabel = params['outputlabel']
        else:
            print( "EXAMPLE TEST - outputlabel not defined, return" )
            return None

        #add additional parameter checks here

        #instantiate the actual test object, pass required parameters to internal variables
        exampleTest = EXAMPLE_TEST()

        #Finally begin testing
        exampleTest.check_setup()
        exampleTest.record_data()
        exampleTest.do_analysis()
        exampleTest.archive_results()

        print( "EXAMPLE TEST DONE")        

if __name__ == '__main__':
        main()
