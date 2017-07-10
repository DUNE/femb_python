#!/usr/bin/env python3
'''
This provides a command line interface to the oscillator testing.

It manages a runpolicy object in order to run the osc.  testing script
in a manner consistent with other CE testing stations

It maintains a state over a test sequence.
'''

from femb_python import runpolicy

class Cycle(object):
    def __init__(self, readymsg=None, finishmsg=None, **params):
        self._readymsg = readymsg
        self._finishmsg = finishmsg
        self._params = params;
        pass

    def runparams(self):
        '''
        Return parameters that should be passed to a runner's run.
        ''' 
        return self._params


    def get_yes(self, msg, yes="y"):
        '''
        Loop until we get something from user that starts with a 'y'
        '''
        while True:
            res = input(msg)
            if res.lower().startswith(yes):
                return

    def __call__(self, runner):
        '''
        Perform the cycle.
        '''
        params = runner.resolve(**self._params)

        if self._readymsg:
            self.get_yes(self._readymsg.format(**params))

        runner(**params)

        if self._finishmsg:
            self.get_yes(self._finishmsg.format(**params))
        

class Sequencer(object):
    def __init__(self, cycles, runner):
        self.cycles = cycles
        self.runner = runner              # a runpolicy object

    def run(self):
        for cycle in self.cycles:
            cycle(self.runner)


def main(**params):
    '''
    Main entry to the oscillator test script.
    '''

    use_sumatra = True
    test_category = "osc"                 # pick something

    # for the main test script that gets run in 3 cycles
    main_params = dict(params)
    main_params.update(
        executable = "femb_test_osc",
        argstr = "{datadir} {outlabel} {cycle}",
        datasubdir = "cycle{cycle}",      # use easy to guess sub directory for each cycle
        outlabel = "cycle{cycle}",        # likewise, easy to guess files.
    )                                     # note: cycle is filled in the loop below

    # for the final summary script 
    summary_params = dict(params)
    summary_params.update(
        executable = "femb_test_osc_summary",
        argstr = "{datadir} {outlabel}",
        datasubdir = "summary",
        outlabel = "summary",
    )

    # make one Cycle for each, err, cycle of the main test
    readymsg = "\n\nStartting thermal cycle {cycle}.\nAre the oscillators cold and ready for testing? (y/n):\n"
    finishmsg = "\n\nFinished thermal cycle {cycle}.\nAre the oscillators removed from LN2? (y/n):\n"
    cycles = [Cycle(readymsg, finishmsg, cycle=n, **main_params) for n in range(1,4)]

    # and one for the summary
    cycles.append(Cycle(**summary_params))

    r = runpolicy.make_runner(test_category, use_sumatra,
                                  executable=executable,
                                  argstr=argstr, **params)
    s = Sequencer(cycles, r)
    s.run()
    
    
if '__main__' == __name__:
    main()
    
    
