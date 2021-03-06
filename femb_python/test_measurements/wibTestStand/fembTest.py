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

    use_sumatra = True
    test_category = "femb"

    #Explicitly define list of production tests to perform
    tests = []

    #Test 0
    params_test = dict(params)
    params_test.update( executable = "femb_wib_measure_simple", argstr="{paramfile}", datadir = "fembTest_check_setup", outlabel = "fembTest_check_setup",)
    tests.append( Test(**params_test) )

    #actually run tests here
    r = runpolicy.make_runner(test_category, use_sumatra, **params)
    if r == None:
      print("EXAMPLE PRODUCTION TEST - ERROR: runpolicy runner could not be defined, production test not started.")
      return
    s = Sequencer(tests, r)
    s.run()

    print( "EXAMPLE PRODUCTION TEST - DONE")
    
if '__main__' == __name__:
    main()
