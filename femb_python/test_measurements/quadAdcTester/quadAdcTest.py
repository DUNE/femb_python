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

    use_sumatra = True
    test_category = "example"      # pick something
    now = time.time()
    params["session_start_time"] = time.strftime("%Y%m%dT%H%M%S", time.localtime(now))

    #check for executables used in test

    #Explicitly define list of production tests to perform
    tests = []

    #Test 0 - no reconfig long ramp test - configuration happens BEFORE cooldown
    params_test_0 = dict(params)
    params_test_0.update( executable = "quadadc_test_funcgen", argstr="{paramfile}", 
                          datasubdir = "quadAdcTest_noreconfig", outlabel = "quadAdcTest_noreconfig",doReconfig=False)
    tests.append( Test(**params_test_0) )

    #shut down setup before starting normal testing
    #params_test_init_shutdown = dict(params)
    #params_test_init_shutdown.update( executable = "quadadc_prod_shutdownSetup", argstr="{paramfile}", 
    #                      datasubdir = "quadAdcTest_init_shutdown", outlabel = "quadAdcTest_init_shutdown")
    #tests.append( Test(**params_test_init_shutdown) )

    #Take test data using internal vs exteranl ADC clock signals, 1MHz vs 2MHz
    #External + 2MHz

    params_test_funcgen_extclk_2MHz = dict(params)
    params_test_funcgen_extclk_2MHz.update( executable = "quadadc_test_funcgen", argstr="{paramfile}", 
                                            datasubdir = "quadAdcTest_funcgen_extclk_2MHz", outlabel = "quadAdcTest_funcgen_extclk_2MHz",
                                            isExternalClock = True, is1MHzSAMPLERATE=False)
    tests.append( Test(**params_test_funcgen_extclk_2MHz) )

    #Internal + 2MHz
    params_test_funcgen_intclk_2MHz = dict(params)
    params_test_funcgen_intclk_2MHz.update( executable = "quadadc_test_funcgen", argstr="{paramfile}", 
                                            datasubdir = "quadAdcTest_funcgen_intclk_2MHz", outlabel = "quadAdcTest_funcgen_intclk_2MHz",
                                            isExternalClock = False, is1MHzSAMPLERATE=False)
    tests.append( Test(**params_test_funcgen_intclk_2MHz) )

    #External + 1MHz
    params_test_funcgen_extclk_1MHz = dict(params)
    params_test_funcgen_extclk_1MHz.update( executable = "quadadc_test_funcgen", argstr="{paramfile}", 
                                            datasubdir = "quadAdcTest_funcgen_extclk_1MHz", outlabel = "quadAdcTest_funcgen_extclk_1MHz",
                                            isExternalClock = True, is1MHzSAMPLERATE=True)
    tests.append( Test(**params_test_funcgen_extclk_1MHz) )

    #Internal + 1MHz
    params_test_funcgen_intclk_1MHz = dict(params)
    params_test_funcgen_intclk_1MHz.update( executable = "quadadc_test_funcgen", argstr="{paramfile}", 
                                            datasubdir = "quadAdcTest_funcgen_intclk_1MHz", outlabel = "quadAdcTest_funcgen_intclk_1MHz",
                                            isExternalClock = False, is1MHzSAMPLERATE=True)
    tests.append( Test(**params_test_funcgen_intclk_1MHz) )

    #ADC input pin functionality test here
    params_test_funcgen_simple = dict(params)
    params_test_funcgen_simple.update( executable = "quadadc_test_simple", argstr="{paramfile}", 
                                            datasubdir = "quadAdcTest_simple", outlabel = "quadAdcTest_simple",
                                            isExternalClock = False, is1MHzSAMPLERATE=False)
    tests.append( Test(**params_test_funcgen_simple) )

    #final shut down
    #params_test_final_shutdown = dict(params)
    #params_test_final_shutdown.update( executable = "quadadc_prod_shutdownSetup", argstr="{paramfile}", 
    #                      datasubdir = "quadAdcTest_final_shutdown", outlabel = "quadAdcTest_final_shutdown")
    #tests.append( Test(**params_test_final_shutdown) )

    #create summary plots
    params_test_funcgen_summary = dict(params)
    params_test_funcgen_summary.update( executable = "quadadc_test_summary", argstr="{paramfile}", 
                                            datasubdir = "quadAdcTest_summary", outlabel = "quadAdcTest_summary")
    tests.append( Test(**params_test_funcgen_summary) )

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
