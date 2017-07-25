#!/usr/bin/env python3
import os
import sys
import time
import json

from femb_python.configuration import CONFIG
from .doFembTest_simpleMeasurement import FEMB_TEST_SIMPLE

class FEMB_POWER_CYCLE_TEST(object):

    def __init__(self):
        self.config = CONFIG()
        self.ntries = 5
        
    def callit(self,params):

        wibslots = params['wibslots']

        for icycle in range(0,self.ntries):
            for ifemb in wibslots:
                self.config.powerOffFemb(ifemb)
                self.config.powerOnFemb(ifemb)                                
            datadir = params['datadir']
            label = "simpleMeasurement"+str(icycle)
            femb_test = FEMB_TEST_SIMPLE(datadir,label,fembNum)
            femb_test.check_setup()
            femb_test.record_data()
            femb_test.do_analysis()
            femb_test.archive_results()
                

def main():
        '''
        Run the power cycle measurement.
        '''
        print( "POWER CYLCE TEST START")
        for arg in sys.argv :
            print( arg )
        import json
        params = json.loads(open(sys.argv[1]).read())
        
        print( params )

        #check for required parametes
        if 'paramfile' in params:
            paramfile = params['paramfile']
        else:
            print( "FEMB POWER CYCLE TEST - paramfile not defined, return" )
            return None

        #instantiate the actual test object, pass required parameters to internal variables
        powerCycleTest = FEMB_POWER_CYCLE_TEST()

        #Finally begin testing
        powerCycleTest.callit(params)

if __name__ == '__main__':
        main()
