#!/usr/bin/env python3
import os
import sys
import time
import json

from femb_python.configuration import CONFIG

class FEMB_CHECK_CURRENT(object):

    def __init__(self, datadir="data", outlabel="check_current"):
        #set status variables
        self.status_check_setup = 0
        self.status_record_data = 0
        self.status_do_analysis = 0
        self.status_archive_results = 0
        self.config = CONFIG()
        self.results_current = {}
        self.fullresults_current = {}
        self.datadir = datadir
        self.outlabel = outlabel
        self.outpathlabel = os.path.join(self.datadir, self.outlabel)

    def check_setup(self):
        #CHECK STATUS AND INITIALIZATION
        print("CHECK SETUP")
        self.status_check_setup = 0

        #check if register interface is working
        print("Checking register interface")
        regVal = self.config.femb.read_reg(6)
        if (regVal == None):
            print("Error running doFembTest - FEMB register interface is not working.")
            print(" Turn on or debug FEMB UDP readout.")       
            return
        if ( regVal < 0 ):
            print("Error running doFembTest - FEMB register interface is not working.")
            print(" Turn on or debug FEMB UDP readout.")       
            return
        print("Read register 6, value = " + str( hex( regVal ) ) )

        #CHECK STATUS SUCCEEDED
        print("CHECK SETUP - STATUS OK" + "\n")
        self.status_check_setup = 1

    def record_data(self,ifemb,wibslots=[]):
        if self.status_check_setup == 0:
            print("RECORD DATA - Please run check_setup method before trying to take data")
            return

        #check that femb number is valid
        if ("all" not in ifemb and "off" not in ifemb):
            if (( int(ifemb) < 0 ) or ( int(ifemb) >= self.config.NFEMBS )):
                print("Error running current check - Invalid FEMB # specified.")
                return    

        for j in range(0,4,1):
            self.config.powerOffFemb(j)

        if ("off" in ifemb):
            results_current = []
            for j in range(0,4,1):
                curr_measured = self.config.readCurrent(j)
                results_current.append(curr_measured)                
            self.results_current["none_on"] = results_current
            
        elif ("all" not in ifemb):
            self.config.selectFemb(ifemb)
            self.config.initFemb()
            time.sleep(5)
            results_current = []            
            for j in range(0,4,1):
                curr_measured = self.config.readCurrent(j)
                results_current.append(curr_measured)
            self.results_current["femb"+str(ifemb)+"on"] = results_current
            self.config.powerOffFemb(ifemb)

        elif len(wibslots)>1:
            results_current = []
            for i in wibslots:
                self.config.selectFemb(i)
                self.config.initFemb()
            time.sleep(5)
            for j in range(0,4,1):
                curr_measured = self.config.readCurrent(j)
                results_current.append(curr_measured)
            self.results_current["all_on"] = results_current
            for i in wibslots:
                self.config.powerOffFemb(i)
        self.status_record_data = 1

    def do_analysis(self):
        if self.status_record_data == 0:
            print("DO ANALYSIS - Please record data before analysis")
            return
        if self.status_do_analysis == 1:
            print("DO ANALYSIS - Analysis already complete")
            return

        print("DO ANALYSIS")
        rsense = 0.1

        for key,resultlist in self.results_current.items():
            print (key, resultlist)
            jfemb = 0
            for result in resultlist:
                i = 0
                for val in result:
                    val1 = ((val >> 16) & 0xFFFF)
                    val2 = (val & 0xFFFF)

                    if i==0:
                        v1 = val1 & 0x3FFF 
                        vcc0 = v1*305.18e-6 + 2.5
                        self.fullresults_current[key+"_femb"+str(jfemb)+"_vcc0"] = vcc0
                        v2 = val2 & 0x3FFF
                        temp0 = v2*0.0625
                        self.fullresults_current[key+"_femb"+str(jfemb)+"_temp0"] = temp0
                    elif i==1:
                        v1 = val1 & 0x3FFF                             
                        vcc1 = v1*305.18e-6 + 2.5
                        self.fullresults_current[key+"_femb"+str(jfemb)+"_vcc1"] = vcc1
                        v2 = val2 & 0x3FFF
                        temp1 = v2*0.0625
                        self.fullresults_current[key+"_femb"+str(jfemb)+"_temp1"] = temp1
                    else:
                        v1 = val1 & 0x3FFF
                        vi = v1*305.18e-6
                        self.fullresults_current[key+"_femb"+str(jfemb)+"_v"+str(i-1)] = vi
                        v2 = val2 & 0x3FFF
                        ii = v2*19.075e-6/rsense
                        if ii>3.1:
                            ii=0
                        self.fullresults_current[key+"_femb"+str(jfemb)+"_i"+str(i-1)] =ii
                    i+=1
                jfemb += 1
        
    def archive_results(self):
        if self.status_record_data == 0:
            print("ARCHIVE RESULTS - Please take data before archiving results")
            return
        if self.status_archive_results == 1:
            print("ARCHIVE RESULTS -Results already archived")
            return

        print("ARCHIVE RESULTS")

        jsonFile = self.outpathlabel + "-results.json"
        with open ( jsonFile, 'w') as outfile:
            json.dump( self.fullresults_current, outfile, indent=4)
                       
        #ARCHIVING SUCCEEDED
        print("ARCHIVE RESULTS - DONE" + "\n")
        self.status_archive_results = 1

def main():
        '''
        Record current draw from each WIB slot
        '''
        print( "CURRENT CHECK START")
        for arg in sys.argv :
            print( arg )
        import json
        params = json.loads(open(sys.argv[1]).read())
        
        print( params )

        #check for required parameters
        if 'datadir' in params:
            datadir = params['datadir']
        else:
            print( "CURRENT CHECK TEST - datadir not defined, return" )
            return None

        if 'outlabel' in params:
            outlabel = params['outlabel']
        else:
            print( "CURRENT CHECK TEST - outputlabel not defined, return" )
            return None

        wibslots = params['wibslots']

        #instantiate the actual test object, pass required parameters to internal variables
        currentTest = FEMB_CHECK_CURRENT(datadir,outlabel)

        #Finally begin testing
        currentTest.check_setup()
        for ifemb in wibslots:
            currentTest.record_data(str(ifemb))
        #currentTest.record_data("all",wibslots)
        currentTest.record_data("off")
        currentTest.do_analysis()
        currentTest.archive_results()

        print( "CURRENT CHECK TEST DONE")        

if __name__ == '__main__':
        main()
