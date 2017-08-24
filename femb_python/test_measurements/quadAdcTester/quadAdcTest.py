#!/usr/bin/env python3
'''
This code runs production ADC tests with quad-socket test board.

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
    print( "QUAD ADC PRODUCTION TEST - START")

    use_sumatra = False 
    test_category = "example"      # pick something
    now = time.time()
    params["session_start_time"] = time.strftime("%Y%m%dT%H%M%S", time.localtime(now))

    #check for executables used in test

    #Explicitly define list of production tests to perform
    tests = []
    
    #configurations to test: 1+2MHz, internal vs external clocks

    #Test 0 - no reconfig long ramp test - configuration happens BEFORE cooldown

    #Test 1 - function generator test
    params_test_1 = dict(params)
    params_test_1.update( executable = "quadadc_test_simple", argstr="{paramfile}", datasubdir = "quadAdcTest_simple", outlabel = "quadAdcTest_simple",)
    tests.append( Test(**params_test_1) )

    #Test 2 - ADC ASIC input pin test with FE-ASIC

    #actually run tests here
    r = runpolicy.make_runner(test_category, use_sumatra, **params)
    if r == None:
      print("QUAD ADC PRODUCTION TEST - ERROR: runpolicy runner could not be defined, production test not started.")
      return
    s = Sequencer(tests, r)
    s.run()

    print( "QUAD ADC PRODUCTION TEST - DONE")
    
if '__main__' == __name__:
    main()
