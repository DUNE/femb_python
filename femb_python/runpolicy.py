#!/usr/bin/env python3
'''
This module provides the class Runner that can be used to run programs
(ie CE testing module scripts) in a way that enforces certain policy
while delegating some policy to the caller.  See documentation for
Runner for more information.

'''
import os
import json
import subprocess

class Runner(object):
    '''
    A Runner is a parameterized execution of an external program.

    Parameters:
    ===========

    Parameters and parameter resolution govern the detailed policy of
    how the program is run by each call to a Runner instance.

    Parameter resolution
    --------------------

    The canonical parameters, listed below, are subject to parameter
    resolution.  This makes use of `str.format()` using the parameter
    set itself.

    Per-call Parameter override
    ---------------------------

    When an instance of Runner is called an call-specific parameter
    set may be passed.  It will be merged into (a copy of) the
    parameter set passed during construction.

    Canonical parameters
    --------------------

    Some parameters are expected and likely should be given.  If not
    specified then defults will be guessed.  They are all subject to
    parameter resolution as described above.  The user is allowed to
    include additional parameters.  They will be added to the
    `paramfile` but they will not undergo parameter resolution.

        - `rundir` specifies the current working directory to use when
          calling the program.

        - `datadir` specifies where output data files should appear
          and will be registered with Sumatra (if activated).

        - `stdout` specifies the log file to which standard output
          will be directed.

        - `stderr` specifies the log file to which standard error will
          be directed.

        - `paramfile` specifies the file in which the resolved
          parameters will be saved as a JSON text.  This variable must
          be referenced in `argstr` if Sumatra is to discover it.
          Note, Sumatra will actually rename this file before calling
          the program.

        - `executable` specifies the executable program file to run.

        - `argstr` specifies the command line argument string to pass
          to the program on execution.  This variable is resolved
          last.  It should not include the program name.  It should
          include `{paramfile}`.

        - `smtname` specifies the Sumatra project name.  If no name is
          given, the program will not be run under `smt run`.  If
          necessary, the "{rundir}" will be initialized for Sumatra
          (and Git).

        - `smtprime` specifies a file name to use to initialize the
          Git repository, if needed.

        - `smtstore` specifies the file name to use for the Sumatra
          store.

        - `smtlabel` optional label for Sumatra

        - `smtreason` optional Sumatra "reason" for the run.
    '''

    # Canonical parameters, their defaults and resolution order:
    canonical = [
        ('rundir','.'),
        ('datadir','.'),
        ('stdout','{datadir}/output.log'),
        ('stderr','{datadir}/error.log'),
        ('paramfile','{rundir}/params.json'),
        ('executable',None),              # required
        ('argstr',''),
        ('smtname',None),
        ('smtprime','{rundir}/readme-smt.txt'),
        ]


    def __init__(self, **params):
        '''
        Create a runner with for a program in a path.

        :params dictionary: a default set of parameters.  See
            discussion of parameters above.
        '''
        self.default_params = params

        pass

    def __call__(self, **user_params):
        '''
        Execute program with parameters in the run directory.

        The `user_params` dictionary is merged into any defaults given
        to the constructor and then resolved.
        '''
        params = self.resolve(**user_params)
        self.initialize(**params)

        # default, no Sumatra
        cmdline = "{executable} {argstr} > {stdout} 2> {stderr}"

        smtname = params.get('smtname',None)
        if smtname:                                # run under Sumatra
            # warning: race condition. must run 'smt configure' just before
            # 'smt run' as we allow data directory to change.
            cfgcmd = "smt configure -d {datadir}".format(**params)
            self.run(cfgcmd, params['rundir'])
            
            # Embed nominal command line in Sumatra command line.
            cmdline = 'smt run -e "%s"' % cmdline
            if 'smtlabel' in params:
                cmdline += " -l {smtlabel}"
            if 'smtreason' in params:
                cmdline += " -r {smtreason}"

        # prepare param file.
        with open(params['paramfile'], 'w') as fp:
            fp.write(json.dumps(params, indent=4));

        cmdline = cmdline.format(**params)
        self.run(cmdline, params['rundir'])
            
    def assuredir(self, directory):
        os.makedirs(directory, exist_ok=True)

    def run(self, cmdstr, cwd=".", shell=True):
        '''
        Wrap up the low level running of some command
        '''
        print ('Running "%s" in %s' % (cmdstr, cwd))
        sc = subprocess.run(cmdstr, cwd=cwd, shell=shell)
        if sc.stdout:
            print (sc.stdout)
        if sc.stderr:
            print (sc.stderr)
        if sc.returncode != 0:
            raise RuntimeError('Failed to run "%s"' % cmdstr)


    def initialize(self, **params):
        '''
        Initialize rundir, optionally with Sumatra.
        '''
        rundir = params['rundir']
        self.assuredir(rundir)
        datadir = params['datadir']
        self.assuredir(datadir)

        smtname = params.get('smtname',None)
        if not smtname:
            return

        # Initialize git. 

        # Fixme: this probably does not do what the user wants if rundir is a
        # subdir of an existing project.

        dotgit = os.path.join(rundir, '.git')
        if not os.path.exists(dotgit):
            sc = self.run("git init", rundir)

            touch = params.get("smtprime","readme.txt")
            touch_fp = os.path.join(rundir, touch)
            if not os.path.exists(touch_fp):
                with open(touch_fp, "w") as fp:
                    fp.write("Sumatra managed directory.")
            self.run("git add %s"%touch, rundir)
            self.run("git commit -am 'Initialize Sumatra project'", rundir)

        # Initialize Sumatra.

        dotsmt = os.path.join(rundir, '.smt')
        if os.path.exists(dotsmt):
            return
        cmdline = "smt init -s {smtstore} -r . {smtname}".format(**params)
        self.run(cmdline, rundir)
        return
                

    def resolve(self, **user_params):
        params = self.default_params.copy()
        params.update(user_params)

        # "wash" the canonical parameters, applying defaults and resolving.
        for name, default in self.canonical:
            val = params.get(name, default)
            if type(val) == str:
                val = val.format(**params)
            params[name] = val

        return params
