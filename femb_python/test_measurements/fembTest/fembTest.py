#!/usr/bin/env python3
'''
This provides a command line interface to WIB + FEMB production tests.

It manages a runpolicy object in order to run the testing script
in a manner consistent with other CE testing stations

It maintains a state over a test sequence.
'''

from femb_python import runpolicy
import time

class Test(object):
    def __init__(self, **params):
        self._params = params;
        pass

    def runparams(self):
        '''
        Return parameters that should be passed to a runner's run.
        ''' 
        return self._params

    def __call__(self, runner):
        '''
        Perform the test.
        '''
        params = runner.resolve(**self._params)
        runner(**params)

class Sequencer(object):
    def __init__(self, tests, runner):
        self.tests = tests      # the tests to perform
        self.runner = runner      # a runpolicy object

    def run(self):
        for test in self.tests:
            test(self.runner)

def main(**params):
    '''
    Main entry to the test script.
    '''
    print( "FEMB PRODUCTION TEST - START")

    use_sumatra = True
    test_category = "femb"      # pick something

    #check for any required input paramaters here ie board id etc
    if (not params['operator']):
        print ("Operator data not entered")
        return -99
    if (not params['box_id']):
        print ("Box ID data not entered")        
        return -99
    if (not params['am_id']):
        print ("Analog MB ID data not entered")                
        return -99
    if (not params['fm_id']):
        print ("FPGA Mezz data not entered")                
        return -99
   
    #Explicitly define list of production tests to perform
    tests = []

    #Test 0
    params_test_0 = dict(params)
    params_test_0.update( executable="femb_power_cycle_test", argstr="{paramfile}", datasubdir="fembTest_powercycle_test", outlabel="fembTest_powercycle_test")
    tests.append( Test(**params_test_0) )

    #ENC Measurements: Loop over gain and shaping times

    testoffset = 0
    params_test = dict(params)
    for s in range(0,4):
        for g in range(2,4):
            params_test.update( executable="femb_test_gainenc", argstr="{paramfile}",
                                datasubdir="fembTest_gainenc_test_g"+str(g)+"_s"+str(s), 
                                outlabel="fembTest_gainenc_test", gain=g, shape=s, base=0)
            tests.append( Test(**params_test) )

    #actually run tests here
    r = runpolicy.make_runner(test_category, use_sumatra, **params)
    if r == None:
      print("FEMB PRODUCTION TEST - ERROR: runpolicy runner could not be defined, production test not started.")
      return
    s = Sequencer(tests, r)
    s.run()

    print( "FEMB PRODUCTION TEST - DONE")
    
if '__main__' == __name__:
    main()