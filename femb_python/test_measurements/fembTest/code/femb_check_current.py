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

        print("Checking current for: ",ifemb)

        for j in range(0,4,1):
            self.config.powerOffFemb(j)
                        
        if ("off" in ifemb): #All off
            time.sleep(60)
            curr_measured = self.config.readCurrent()
            self.results_current["none_on"] = curr_measured
            
        elif ("all" not in ifemb): #Single slot on
            self.config.powerOnFemb(ifemb)
            time.sleep(30)
            curr_measured = self.config.readCurrent()
            self.results_current["femb"+str(ifemb)+"on"] = curr_measured
            self.config.powerOffFemb(ifemb)

        #elif len(wibslots)>1: #All on
        else:
            for i in wibslots:
                self.config.powerOnFemb(i)
            time.sleep(30)
            curr_measured = self.config.readCurrent()
            self.results_current["all_on"] = curr_measured
            for j in wibslots:
                self.config.powerOffFemb(j)

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
            i = 0
            for val in resultlist:
                if (i<25):
                    jfemb = int(i/6)
                    val1 = ((val >> 16) & 0xFFFF)
                    val2 = (val & 0xFFFF)

                    if i%6==0:
                        v1 = val1 & 0x3FFF
                        vcc1 = v1*305.18e-6 + 2.5
                        self.fullresults_current[key+"_femb"+str(jfemb)+"_vcc1"] = vcc1
                        v2 = val2 & 0x3FFF
                        temp1 = v2*0.0625
                        self.fullresults_current[key+"_femb"+str(jfemb)+"_temp1"] = temp1
                    else:
                        v1 = val1 & 0x3FFF
                        vi = v1*305.18e-6
                        self.fullresults_current[key+"_femb"+str(jfemb)+"_v"+str(i%6)] = vi
                        v2 = val2 & 0x3FFF
                        ii = v2*19.075e-6/rsense
                        if ii>3.1:
                            ii=0
                        self.fullresults_current[key+"_femb"+str(jfemb)+"_i"+str(i%6)] = ii
                i+=1

    def unpack(self,val,i):
        i -= 1
        rsense = 0.1
        unpacked_results = []
        if (i<25):
            jfemb = int(i/6)
            val1 = ((val >> 16) & 0xFFFF)
            val2 = (val & 0xFFFF)

            if i%6==0:
                v1 = val1 & 0x3FFF
                vcc1 = v1*305.18e-6 + 2.5
                unpacked_results.append(vcc1)
                v2 = val2 & 0x3FFF
                temp1 = v2*0.0625
                unpacked_results.append(temp1)
            else:
                v1 = val1 & 0x3FFF
                vi = v1*305.18e-6
                unpacked_results.append(vi)
                v2 = val2 & 0x3FFF
                ii = v2*19.075e-6/rsense
                if ii>3.1:
                    ii=0
                unpacked_results.append(ii)
        i+=1
        print(i, val, unpacked_results)

        return unpacked_results

                
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
        #currentTest.record_data("off")
        #for ifemb in wibslots:
            #currentTest.record_data(str(ifemb))
        currentTest.record_data("all",wibslots)
        currentTest.do_analysis()
        currentTest.archive_results()

        print( "CURRENT CHECK TEST DONE")        

if __name__ == '__main__':
        main()
