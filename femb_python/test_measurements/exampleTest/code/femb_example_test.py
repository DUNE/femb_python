#!/usr/bin/env python3
import os
import sys
import time
import json

#from femb_python.configuration import CONFIG #required! commented out for example test

class EXAMPLE_TEST(object):

    def __init__(self, datadir="data"):
        #set status variables
        self.status_check_setup = 0
        self.status_record_data = 0
        self.status_do_analysis = 0
        self.status_archive_results = 0

        #set test specific variables
        self.datadir=datadir    #from object initialization
        self.outlabel="example" #can be modified as object public member before test
        self.outpathlabel = os.path.join(self.datadir, self.outlabel)

        #json output, note module version number defined here
        self.jsondict = {'type':'exampleTest'}
        self.jsondict['version'] = '1.0'
        #NOTE: SHOULD write JSON file at this point to indicate that a production test object was created ie a test was started

        #import femb_config configuration modules from femb_pyton package, environment variable defines the correct configuration
        #self.femb_config = CONFIG() #required! commented out for example test
        #self.write_data = WRITE_DATA(datadir) #helper module for writing testr data to disk, not required

    def check_setup(self):
        #CHECK STATUS AND INITIALIZATION
        print("CHECK SETUP")
        self.status_check_setup = 0

        #make sure output directory exists
        #self.write_data.assure_filedir() #helper module
        if self.datadir == None:
            self.datadir = "data"
        if os.path.isdir( str(self.datadir) ) == False:
            print("exampleTest: Data directory not found, making now.")
            os.makedirs( str(self.datadir) )

        #add checks here, correct configuration module, firmware version, output directory exists etc
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
        #if self.status_do_analysis == 0:
        #    print("ARCHIVE RESULTS - Please analyze data before archiving results")
        #    return
        if self.status_archive_results == 1:
            print("ARCHIVE RESULTS -Results already archived")
            return
        #ARCHIVE SECTION
        print("ARCHIVE RESULTS")
        
        #ARCHIVING OF RESULTS GOES HERE
        self.jsondict['status_check_setup'] = self.status_check_setup
        self.jsondict['status_record_data'] = self.status_record_data
        self.jsondict['status_do_analysis'] = self.status_do_analysis
        self.jsondict['status_archive_results'] = 1

        #dump results into json, NOTE ideally adding to an already existing JSON file
        jsonFile = self.outpathlabel + "-results.json"
        with open( jsonFile , 'w') as outfile:
            json.dump( self.jsondict, outfile, indent=4)

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

        #default parameters, can be updated by JSON input
        datadir = "data"
        outlabel = "example"
       
        #update parameters if a json file is provided
        if len(sys.argv) == 2 :
            params = json.loads(open(sys.argv[1]).read()) #maybe put try except 
            #check for required parameters in json
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

        #add additional parameter checks here are supplied parameters reasonable

        #instantiate the actual test object, pass required parameters to internal variables
        exampleTest = EXAMPLE_TEST(datadir) #datadir passed during object intialization
        exampleTest.outlabel = outlabel     #outlabel to internal variable

        #Finally begin testing
        exampleTest.check_setup()
        exampleTest.record_data()
        exampleTest.do_analysis()
        exampleTest.archive_results()

        print( "EXAMPLE TEST DONE")        

if __name__ == '__main__':
        main()
