#!/usr/bin/env python3
'''
This provides a command line interface to the flash testing.

It manages a runpolicy object in order to run the osc.  testing script
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
        self.tests = tests
        self.runner = runner              # a runpolicy object

    def run(self):
        for test in self.tests:
            test(self.runner)


def main(**params):
    '''
    Main entry to the flash test script.
    '''
    use_sumatra = True
    test_category = "FlashTesting"                 # pick something

    # for the test
    test_params = dict(params)
    test_params.update(
        executable = "femb_flash_test_main",
        argstr = "{datadir} {outlabel}",
        datasubdir = "QuadEpcsTester",      # use easy to guess sub directory for each cycle
        outlabel = "QuadEpcsTester",                        # likewise, easy to guess files.
    )                                                             # note: cycle is filled in the loop below

    tests = []
    tests.append(Test(**test_params))

    r = runpolicy.make_runner(test_category, use_sumatra, **params)
    if r == None:
        print("ERROR: runpolicy runner could not be defined, production test not started.")
        return
    s = Sequencer(tests, r)
    s.run()
        
if '__main__' == __name__:
    main()
    
    
