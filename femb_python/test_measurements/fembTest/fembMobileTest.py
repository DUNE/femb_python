#!/usr/bin/env python3
'''
This provides a command line interface to WIB + FEMB production tests.

It manages a runpolicy object in order to run the testing script
in a manner consistent with other CE testing stations

It maintains a state over a test sequence.
'''

from femb_python import runpolicy

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

    use_sumatra = False
    test_category = "femb"      # pick something

    #check for any required input paramaters here ie board id etc
    if (not params['operator']):
        print ("Operator data not entered")
        return -99
    if (not params['box_ids']):
        print ("Box ID data not entered")        
        return -99
    if (not params['apa_pos']):
        print ("APA Position data not entered")                
        return -99
   
    #Explicitly define list of production tests to perform
    tests = []

    #Simple Measurement
    params_simple = dict(params)
    params_simple.update( executable="femb_test_simple", argstr="{paramfile}",
                           datasubdir="fembTest_simple",
                           outlabel="fembTest_simple")
    tests.append( Test(**params_simple) )

    
    #ENC Measurements: Loop over gain and shaping times

    params_test = dict(params)

    #Test with external clocks
    params_test.update( executable="femb_test_gainenc", argstr="{paramfile}",
                        datasubdir="fembTest_gainenc_test_g2_s2_intpulse_extclock", 
                        outlabel="fembTest_gainenc_test_g2_s2_intpulse_extclock", 
                        gain=2, shape=2, base=1, useInternalPulser=True, useExtAdcClock=True)
    tests.append ( Test(**params_test) )

    #Current Measurement
    params_test_current = dict(params)
    params_test_current.update( executable="femb_check_current", argstr="{paramfile}",
                                datasubdir="fembTest_check_current_test",
                                outlabel="fembTest_check_current_test")
    tests.append( Test(**params_test_current) )
    

    #Summarize Results
    params_summary = dict(params)
    params_summary.update( executable="femb_mobile_summary", argstr="{paramfile}",
                           datasubdir="fembTest_summary",
                           outlabel="fembTest_summary")
    tests.append( Test(**params_summary) )

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
