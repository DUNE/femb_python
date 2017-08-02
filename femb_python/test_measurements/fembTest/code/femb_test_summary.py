#!/usr/bin/env python3
import os
import sys
import time
import json
from fpdf import FPDF

from femb_python.configuration import CONFIG

class FEMB_SUMMARY(object):

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

        slotlist = params['wibslots']

        gainlabels = ["4.7", "7.8", "14", "25"]
        shapelabels = ["0.5", "1", "2", "3"]
        pulselabels = ["Internal Pulser", "FPGA Pulser"]
        
        for slot in slotlist:
 
            i = slotlist.index(slot)
            if ("na" in params['box_ids'][i].lower()):
                name = params['am_ids'][i]+"_"+params['fm_ids'][i]
                boxtext = ""
            else:
                name = params['box_ids'][i]
                boxtext = "CE Box "

            text_title = "protoDUNE FEMB QC Summary: "+boxtext+name

            timestamp = "Timestamp: "+params['session_start_time']

            if params['isRoomTemp']:
                temp = "RT"
            else:
                temp = "CT"
            temp = "Temperature: "+temp
            user = "Tested by: "+params['user']

            pdf = FPDF(format='letter')
            pdf.add_page()
            pdf.set_font("Arial", 'B', size=14)

            pdf.cell(200, 10, txt=text_title, ln=1, align='C')

            pdf.set_font("Arial", 'B', size=10)
            pdf.cell(60, 5, txt=timestamp, align='L')
            pdf.cell(60, 5, txt=user, align='L')
            pdf.cell(60, 5, txt=temp, align='L',ln=1)

            amt = "Analog MB ID: "
            fmt = "FPGA Mezz ID: "
            fet = "FE ASICS: "
            adct = "ADC ASICS: "

            t1 = amt+params['am_ids'][i]
            pdf.cell(40, 5, txt=t1, align='L')
            t2 = fmt+params['fm_ids'][i]
            pdf.cell(25, 5, txt=t2, align='L',ln=1)

            pdf.cell(25, 5, txt=fet, align='L')            
            for jfe in params['fe_asics'][i]:
                pdf.cell(10, 5, txt=str(jfe), align='L')            
            pdf.ln(5)

            pdf.cell(25, 5, txt=adct, align='L')            
            for jadc in params['adc_asics'][i]:
                pdf.cell(10, 5, txt=str(jadc), align='L')
            pdf.ln(5)

            printgain = False
            printpc = False
            printcurrent = False
            gainsummary = {}

            for mydir in self.subdirs:
                #Gain summary:
                if ("gainenc" in mydir):
                    gaininfo = []
                    info_file = self.topdir+"/"+mydir+"/params.json"
                    if os.path.isfile(info_file):
                        params_curr = json.loads(open(info_file).read())
                        results_file = params_curr['datadir']+"/gainMeasurement_femb_"+str(slot)+"-results.json"
                        if os.path.isfile(resultsfile):
                            result = json.loads(open(results_file).read())
                            gaininfo.append(gainlabels[int(result['config_gain'])])
                            gaininfo.append(shapelabels[int(result['config_shape'])])
                            if ("intpulse" in mydir):
                                gaininfo.append(pulselabels[0])
                            else:
                                gaininfo.append(pulselabels[1])
                            encsum = 0
                            n = 0
                            for r in result['results']:
                                if ("enc" in r):
                                    encsum+=float(r['enc'])
                                    n+=1
                            encavg = encsum/n
                            gaininfo.append(encavg)
                            gainlabel = gaininfo[0]+"_"+gaininfo[1]+"_"+gaininfo[2]
                            gainsummary[gainlabel] = gaininfo
                    
                    if ("g2_s2_intpulse" in mydir):
                        if os.path.isfile(self.topdir+"/"+mydir+"/gainMeasurement_femb_"+str(slot)+"-summaryPlot.png"):
                            gaintext = "Gain/ENC Measurement: Gain = 14 mV/fC, Shaping Time = 1 us, Internal Pulser"
                            gainimage = self.topdir+"/"+mydir+"/gainMeasurement_femb_"+str(slot)+"-summaryPlot.png"
                            printgain = True
                #Power cycle summary:
                if ("powercycle" in mydir):
                    pc_text = "FEMB power cycled 5 times at beginning of data collection with no failure."
                    printpc = True

                #Current monitor summary:
                if ("current" in mydir):
                    voltage_text = "Voltage (A):"                    
                    current_text = "Current (A):"
                    l1 = "4.2 V"
                    l2 = "3 V"
                    l3 = "2.5 V"
                    l4 = "1.5 V"
                    l5 = "5 V"
                    info_file = self.topdir+"/"+mydir+"/params.json"
                    if os.path.isfile(info_file):
                        params_curr = json.loads(open(info_file).read())
                        results_file = params_curr['datadir']+"/"+params_curr['outlabel']+"-results.json"
                        if (os.path.isfile(results_file):
                            result = json.loads(open(results_file).read())

                            ion = [result["all_on_femb"+str(slot)+"_i1"],
                                   result["all_on_femb"+str(slot)+"_i2"],
                                   result["all_on_femb"+str(slot)+"_i3"],
                                   result["all_on_femb"+str(slot)+"_i4"],
                                   result["all_on_femb"+str(slot)+"_i5"] ]
                            von = [result["all_on_femb"+str(slot)+"_v1"],
                                   result["all_on_femb"+str(slot)+"_v2"],
                                   result["all_on_femb"+str(slot)+"_v3"],
                                   result["all_on_femb"+str(slot)+"_v4"],
                                   result["all_on_femb"+str(slot)+"_v5"] ]

                            #ETW these measurements are not reliable right now - turn off printing
                            printcurrent = False

            if (printgain):

                pdf.ln(7)                
                pdf.cell(200,5,txt="Average ENC measured with internal pulser (electrons))",align='L',ln=1)
                pdf.cell(50,5,txt="",)
                for shape in shapelabels:
                    pdf.cell(25,5,txt=shape+" us",align='L')
                pdf.ln(4)

                pdf.cell(50,5,txt=gainlabels[2]+" mV/fC",align='L')
                for shape in shapelabels:
                    gainlabel = gainlabels[2]+"_"+shape+"_"+pulselabels[0]
                    if (gainlabel in gainsummary.keys()):
                        pdf.cell(25, 5, txt="{:4.0f}".format(gainsummary[gainlabel][3]), align='L')
                    else:
                        pdf.cell(25,5, txt="-", align='L')
                pdf.ln(4)
                
                pdf.cell(50,5,txt=gainlabels[3]+" mV/fC",align='L')                
                for shape in shapelabels:
                    gainlabel = gainlabels[3]+"_"+shape+"_"+pulselabels[0]
                    if (gainlabel in gainsummary.keys()):
                        pdf.cell(25, 5, txt="{:4.0f}".format(gainsummary[gainlabel][3]), align='L')
                    else:
                        pdf.cell(25,5, txt="-", align='L')
                pdf.ln(4)
                
                pdf.ln(7)
                pdf.cell(200,5,txt=gaintext,align='L',ln=1)
                pdf.image(gainimage, w=200)
                pdf.ln(7)

            if (printpc):
                pdf.cell(200,5,txt=pc_text,align='L',ln=1)
                pdf.ln(7)                

            if (printcurrent):
                pdf.cell(50,5,txt="",align='L')
                pdf.cell(15, 5, txt=l1, align='L')
                pdf.cell(15, 5, txt=l2, align='L')
                pdf.cell(15, 5, txt=l3, align='L')
                pdf.cell(15, 5, txt=l4, align='L')
                pdf.cell(15, 5, txt=l5, align='L', ln=1)

                pdf.cell(50,5,txt=voltage_text,align='L')
                pdf.cell(15, 5, txt="{:3.2f}".format(von[0]), align='L')
                pdf.cell(15, 5, txt="{:3.2f}".format(von[1]), align='L')
                pdf.cell(15, 5, txt="{:3.2f}".format(von[2]), align='L')
                pdf.cell(15, 5, txt="{:3.2f}".format(von[3]), align='L')
                pdf.cell(15, 5, txt="{:3.2f}".format(von[4]), align='L', ln=1)

                pdf.cell(50,5,txt=current_text,align='L')
                pdf.cell(15, 5, txt="{:3.2f}".format(ion[0]), align='L')
                pdf.cell(15, 5, txt="{:3.2f}".format(ion[1]), align='L')
                pdf.cell(15, 5, txt="{:3.2f}".format(ion[2]), align='L')
                pdf.cell(15, 5, txt="{:3.2f}".format(ion[3]), align='L')
                pdf.cell(15, 5, txt="{:3.2f}".format(ion[4]), align='L', ln=1)                
                pdf.ln(7)
                

            text = "Data stored on "+params['hostname']+": "
            pdf.cell(200, 5, txt=text, align='L', ln=1)
            text = self.topdir
            pdf.cell(200, 5, txt=text, align='L', ln=1)
            text = "Position on WIB for test: "+str(slot)
            pdf.cell(200, 5, txt=text, align='L', ln=1)
            pdf.output(self.datadir+"/femb"+name+"_summary.pdf",'F')

            print("Summary file created: "+self.datadir+"/femb"+name+"_summary.pdf")

def main():
        '''
        Do a summary of an FEMB test
        '''
        print( "SUMMARY START")
        for arg in sys.argv :
            print( arg )
        import json
        params = json.loads(open(sys.argv[1]).read())
        
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
        summary = FEMB_SUMMARY(datadir,outlabel)

        #Finally begin testing
        summary.check_setup()
        summary.do_analysis(params)

        print( "SUMMARY DONE")        

if __name__ == '__main__':
        main()
