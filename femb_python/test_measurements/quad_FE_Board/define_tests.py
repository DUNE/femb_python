# -*- coding: utf-8 -*-
"""
Created on Tue Nov  6 16:55:05 2018

@author: eraguzin
"""

#!/usr/bin/env python3
'''
This provides an example command line interface for production tests.
It manages a runpolicy object in order to run the testing script
in a manner consistent with other CE testing stations
It maintains a state over a test sequence.
'''

from femb_python import runpolicy
import time
import sys

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
            yield

def main(**params):
    '''
    Main entry to the test script.
    '''
    print( "EXAMPLE PRODUCTION TEST - START")
    now = time.time()
    params["session_start_time"] = time.strftime("%Y%m%dT%H%M%S", time.localtime(now))
    
    #HOW TO SUPPLY INPUT PARAMETERS TO TEST MODULE
    #parameters specific for a general test, more are defined by runpolicy runner
    #this example uses replacement fields to make it easier to define each individual test
    #main_params = dict(params)
    #main_params.update(
    #    executable = "femb_example_test",      # the program or script actually running the test
    #    #argstr = "{datadir} {outlabel}",      #command line arguments to exectuable
    #    argstr="{paramfile}",        #provide parameter file as argument
    #    datadir = "exampleTest_test_{test}",      # use easy to guess sub directory for each test, recommend defining it here
    #    outlabel = "exampleTest_test_{test}",       # likewise, easy to guess files, recommend defining it here
    #)                                               # note: "test" is filled in the loop below

    #can define the tests to perform in a loop, updating the params for each test
    #tests = [Test(test=n, **main_params) for n in range(1,4)]

    #Explicitly define list of production tests to perform
    all_tests = []
    tests = params["tests_to_do"]
    for i in tests:
    #Test 1
        params_test = dict(params)
        params_test.update( executable = i[0], argstr="{paramfile}", datasubdir = ".", outlabel = i[1],)
        all_tests.append(Test(**params_test))
    #actually run tests here
    r = runpolicy.make_runner(**params)
    if r == None:
      print("EXAMPLE PRODUCTION TEST - ERROR: runpolicy runner could not be defined, production test not started.")
      return
      
    s = Sequencer(all_tests, r)
    for i in (s.run()):
        yield (s.runner.params)
    
    s.run()
    
if '__main__' == __name__:
    main()