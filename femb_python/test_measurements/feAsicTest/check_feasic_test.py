#!/usr/bin/env python3
import os
import sys
import time
import json
from fpdf import FPDF

class FEASIC_SUMMARY(object):

    def __init__(self, datadir="data", outlabel="summary"):
        #set status variables
        self.status_check_setup = 0
        self.status_do_analysis = 0
        self.status_archive_results = 0
        self.datadir = datadir
        self.topdir = ""
        self.subdirs = []
        self.outlabel = outlabel
        self.outpathlabel = os.path.join(self.datadir, self.outlabel)

    def check_setup(self):
        #CHECK STATUS AND INITIALIZATION
        print("CHECK SETUP")
        self.status_check_setup = 0

        #Check that data dir exists
        self.topdir = os.path.dirname(self.datadir)
        if not os.path.isdir(self.topdir):
            print("FAIL")
            self.status_check_setup = 0
            return

        self.subdirs = os.listdir(self.topdir)

        if len(self.subdirs) < 1:
            print("No directories for summary - turn on some tests!")
            self.status_check_setup = 0
            return

        #CHECK STATUS SUCCEEDED
        print("CHECK SETUP - STATUS OK" + "\n")
        self.status_check_setup = 1

    def do_analysis(self,params):
        if self.status_check_setup == 0:
            print("DO ANALYSIS - Please record data before analysis")
            return
        if self.status_do_analysis == 1:
            print("DO ANALYSIS - Analysis already complete")
            return
 
        text_title = "protoDUNE FE-ASIC QC Summary"
        timestamp = params['session_start_time']

        for mydir in self.subdirs:
            #print( mydir )
            info_file = self.topdir+"/"+mydir+"/params.json"
            if os.path.isfile(info_file) == False:
                continue

            params_test = json.loads(open(info_file).read())
            #"outlabel": "gain_enc_sequence-g0s3b1-0110-20180110T110004",
            if "outlabel" not in params_test:
                #print("ERROR")
                continue
            testname = params_test["outlabel"]
            #print(testname)

            results_file = self.topdir+"/"+mydir+"/" + testname + "-results.json"
            #print( results_file )
            if os.path.isfile(results_file) == False:
                continue
            result = json.loads(open(results_file).read())
            if 'results' not in result:
                print("ERROR")
                continue
            
            theresults = result["results"]
            asicStatus = ["UNKNOWN","UNKNOWN","UNKNOWN","UNKNOWN"]
            asicGoodVal = [0,0,0,0]
            for element in theresults :
                #print(element)
                if "asic" not in element:
                    continue
                if "fail" not in element:
                    print("ERROR")
                    continue
                asicNum = int(element["asic"])
                if asicNum < 0 or asicNum > 3 :
                    print("ERROR")
                    continue
                failVal = element["fail"]
                if failVal == "0":
                    asicStatus[asicNum] = "GOOD"
                    asicGoodVal[asicNum] = 1
                if failVal == "1":
                    asicStatus[asicNum] = "BAD"
                    asicGoodVal[asicNum] = 0
            
            print(testname,"\t",asicGoodVal[0],"\t",asicGoodVal[1],"\t",asicGoodVal[2],"\t",asicGoodVal[3])
            #print( "TEST: ",testname)
            #print("\tASIC0: ",asicStatus[0],"\tASIC1: ",asicStatus[1],"\tASIC2: ",asicStatus[2],"\tASIC3: ",asicStatus[3]  )

def main():
        '''
        Do a summary of an FEMB test
        '''
        print( "SUMMARY START")
        for arg in sys.argv :
            print( arg )
        
        params = {}

        #load from input JSON file as part of standard test
        if len(sys.argv) == 2 :
            import json
            params = json.loads(open(sys.argv[1]).read())
        
        #load from specified location
        if len(sys.argv) == 3 :
            import json
            paramsFile = str(sys.argv[1])
            params = json.loads(open(sys.argv[1]).read())
            newdatadir = str(sys.argv[2])
            params["paramfile"] = paramsFile
            params["datadir"] = newdatadir + "/"
            params["executable"]="feasic_test_summary"
            params["datasubdir"]="feasic_summary"
            params["outlabel"]="feasic_summary"
        print( params )

        #check for required parameters
        if 'datadir' in params:
            datadir = params['datadir']
        else:
            print( "SUMMARY - datadir not defined, return" )
            return None

        if 'outlabel' in params:
            outlabel = params['outlabel']
        else:
            print( "SUMMARY - outputlabel not defined, return" )
            return None

        #instantiate the actual test object, pass required parameters to internal variables
        summary = FEASIC_SUMMARY(datadir,outlabel)

        #Finally begin testing
        summary.check_setup()
        summary.do_analysis(params)

        print( "SUMMARY DONE")        

if __name__ == '__main__':
        main()
