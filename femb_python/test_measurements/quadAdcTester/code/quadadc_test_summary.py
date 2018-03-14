#!/usr/bin/env python3
import os
import sys
import time
import json
from fpdf import FPDF
from subprocess import call

from femb_python.configuration import CONFIG

class TEST_SUMMARY(object):

    def __init__(self, datadir="data", outlabel="summary"):
        #set status variables
        self.status_check_setup = 0
        self.status_do_analysis = 0
        self.status_archive_results = 0
        self.config = CONFIG()
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

        asicsockets = params['asicsockets']
        asic_ids = params['asic_ids']
        dirstocheck = ["quadAdcTest_noreconfig",
                       "quadAdcTest_funcgen_extclk_2MHz",
                       "quadAdcTest_funcgen_extclk_1MHz",
                       "quadAdcTest_funcgen_intclk_2MHz",
                       "quadAdcTest_funcgen_intclk_1MHz"]

        testlabel = ["Short Ramp Measurement - 734Hz 2Vpp Triangle Wave - No Reconfiguration After Cooldown",
                     "Short Ramp Measurement - 734Hz 2Vpp Triangle Wave - External ADC Clocks 2MHz Sampling Rate",
                     "Short Ramp Measurement - 734Hz 2Vpp Triangle Wave - External ADC Clocks 1MHz Sampling Rate",
                     "Short Ramp Measurement - 734Hz 2Vpp Triangle Wave - Internal ADC Clocks 2MHz Sampling Rate",
                     "Short Ramp Measurement - 734Hz 2Vpp Triangle Wave - Internal ADC Clocks 1MHz Sampling Rate"
                    ]
        """
        dirstocheck = ["quadAdcTest_funcgen_extclk_2MHz",
                       "quadAdcTest_funcgen_extclk_1MHz",
                       "quadAdcTest_funcgen_intclk_2MHz",
                       "quadAdcTest_funcgen_intclk_1MHz"]

        testlabel = ["Short Ramp Measurement - 734Hz 2Vpp Triangle Wave - External ADC Clocks 2MHz Sampling Rate",
                     "Short Ramp Measurement - 734Hz 2Vpp Triangle Wave - External ADC Clocks 1MHz Sampling Rate",
                     "Short Ramp Measurement - 734Hz 2Vpp Triangle Wave - Internal ADC Clocks 2MHz Sampling Rate",
                     "Short Ramp Measurement - 734Hz 2Vpp Triangle Wave - Internal ADC Clocks 1MHz Sampling Rate"
                    ]
        """

        pdf = FPDF(format='letter')
        pdf.set_draw_color(0, 80, 180)
        pdf.set_fill_color(230, 230, 0)

        for asic in asicsockets:
          for test in dirstocheck:
            print("ASIC SOCKET ",asic," SUMMARY PLOT")
 
            i = asicsockets.index(asic)
            j = dirstocheck.index(test)
            name = str(asic_ids[i])
            boxtext = "ASIC Socket " + str(i) + ", ASIC ID " + name

            text_title = "protoDUNE QUAD ADC QC Summary: "+boxtext
            timestamp = "Timestamp: "+params['session_start_time']
            temp = "Temperature: CT"
            user = "Tested by: "+params['operator']

            pdf.add_page()
            pdf.set_font("Arial", 'B', size=14)
            pdf.cell(200, 10, txt=text_title, ln=1, align='C')
            pdf.set_font("Arial", 'B', size=10)
            pdf.cell(60, 5, txt=timestamp, align='L')
            pdf.cell(60, 5, txt=user, align='L')
            pdf.cell(60, 5, txt=temp, align='L',ln=1)

            imagetext = testlabel[j]
            imagefile = None
            if os.path.isfile(self.topdir+"/"+dirstocheck[j]+"/funcgenMeasurement_asic_"+str(asic)+"-summaryPlot.png"):
                imagefile = self.topdir+"/"+dirstocheck[j]+"/funcgenMeasurement_asic_"+str(asic)+"-summaryPlot.png"
 
            pdf.ln(7)
            pdf.cell(200,5,txt=imagetext,align='L',ln=1)
            if imagefile != None:
                 pdf.image(imagefile, w=200)
            else:
                 pdf.cell(200,5,txt="TEST SUMMARY PLOT NOT FOUND",align='L',ln=1)
            pdf.ln(7)

        pdf.output(self.datadir+"/quadadc_summary.pdf",'F')
        print("Summary file created: "+self.datadir+"/quadadc_summary.pdf")    

        call(["evince", str(self.datadir)+"/quadadc_summary.pdf" ])

def main():
        '''
        Do a summary of a QUAD ADC test
        '''
        print( "SUMMARY START")
        for arg in sys.argv :
            print( arg )
        
        params = {}

        #require JSON input or additional arguments
        if len(sys.argv) < 2 :
            print("quadadc_test_summary: invalid number of arguments, will not run")
            return None

        #load from input JSON file as part of standard test
        if len(sys.argv) == 2 :
            import json
            params = json.loads(open(sys.argv[1]).read())
        
        #alternatively load from specified location
        if len(sys.argv) == 3 :
            import json
            paramsFile = str(sys.argv[1])
            params = json.loads(open(sys.argv[1]).read())
            newdatadir = str(sys.argv[2])
            params["paramfile"] = paramsFile
            params["datadir"] = newdatadir + "/"
            params["executable"]="quadadc_test_summary"
            params["datasubdir"]="quadadc_summary"
            params["outlabel"]="quadadc_summary"
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

        if 'asicsockets' in params:
            pass
        else:
            print( "SUMMARY - asicsockets not defined, return" )
            return None

        if 'asic_ids' in params:
            pass
        else:
            print( "SUMMARY - asic_ids not defined, return" )
            return None

        #instantiate the actual test object, pass required parameters to internal variables
        summary = TEST_SUMMARY(datadir,outlabel)

        #Finally begin testing
        summary.check_setup()
        summary.do_analysis(params)

        print( "SUMMARY DONE")        

if __name__ == '__main__':
        main()
