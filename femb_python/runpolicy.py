#!/usr/bin/env python3
'''
This module provides the class Runner that can be used to run programs
(ie CE testing module scripts) in a way that enforces certain policy
while delegating some policy to the caller.  See documentation for
Runner for more information.

'''
import os
import json
import time
import subprocess

class Runner(object):
    '''
    A Runner runs a program as governed by a parameter set.

    Parameters:
    ===========

    A runner has canonical, default and per-call parameter sets.

        - canonical parameters and their defaults are hard-coded as a
          class attribute `canonical`.

        - default parameters and their values are passed to the
          constructor and may override canonical parameters on a
          per-instance basis.

        - call parameters and their values are passed to each call of
          the runner instance and may override canonical and default
          parameters for that call.

    Parameter resolution
    --------------------

    On each call, the parameter set is defined as above and then each
    canonical parameter is resolved against all the parameters.  The
    method of resolution is to call the `str.format()` method.  Thus,
    any references to parameters like "{name}" will be replaced with
    the corresponding value.  Canonical parameters are resolved in
    order of their definition in the list held in the class attribute
    `canonical`.

    '''

    canonical = (
        ('cmdline',None),
        )

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
        Execute `cmdline` with parameters in the run directory.

        The `user_params` dictionary is merged into any defaults given
        to the constructor and then resolved.
        '''
        params = self.resolve(**user_params)
        cmd = self.cmdline(**params)
        self.run(cmd, **params)

    def cmdline(self, **params):
        return params['cmdline']

    def run(self, cmd, **params):
        '''
        Simply pass on to exec().

        Subclass may override this to do something more interesting.
        '''
        self.exec(cmd)

    def assuredir(self, directory):
        os.makedirs(directory, exist_ok=True)

    def exec(self, cmdstr, cwd=".", shell=True):
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

class DirectRunner(Runner):
    '''
    A DirectRunner runs a program directly.
    '''
    canonical = (
        # directory from which to run
        ('rundir','.'),
        # if defined, the parameter set will be saved to this path as a JSON file.
        ('paramfile',None),
        # will redirect stdout if defined
        ('stdout',None),
        # will redirect stderr if defined
        ('stderr',None),
        # The executable
        ('executable',None),              # required
        # The rest of the command line argument string
        ('argstr',''),
        )

    def cmdline(self, **params):
        '''
        Build a command line from `executable` and `argstr` and
        redirect output if `stdout` or `stderr` is given.
        '''
        cmd = "{executable} {argstr}"
        if 'stdout' in params:
            cmd += ' >{stdout}'
        if 'stderr' in params:
            cmd += ' 2>{stderr}'
        return cmd.format(**params)

    def run(self, cmd, **params):
        '''
        Run command built from `cmdline()` but first save param set
        file given by `paramfile` so that it is available to the
        command.
        '''
        cmd = self.cmdline(**params)
        if not cmd:
            raise ValueError('No executable')
        params['cmdline'] = cmd

        # prepare param file if its wanted.
        if 'paramfile' in params:
            paramfile = params['paramfile']
            self.assuredir(os.path.dirname(paramfile))
            with open(paramfile, 'w') as fp:
                fp.write(json.dumps(params, indent=4));

        self.exec(cmd)
        

        
class SumatraRunner(Runner):
    '''
    A SumatraRunner runs a program as governed by a parameter set
    under Sumatra.

    The canonical parameters:

        - `rundir` specifies the current working directory to use when
          calling the program.  This is also the Sumatra workdir and
          repository.

        - `datadir` specifies where output data files should appear
          and any found there will be registered with Sumatra.  The
          command must take care to write there either by finding this
          parameter in the paramfile or by including this directory in
          some command line argument(s).

        - `stdout` set an explicit log file for standard output.
          Otherwise, Sumatra will capture.

        - `stderr` set an explicit log file for standard input.
          Otherwise, Sumatra will capture.

        - `paramfile` set the file to store the parameters as JSON
          text.  Beware: Sumatra will actually rename this file before
          calling the program.

        - `executable` specifies the program to execute.

        - `argstr` gives the command line arguments to the executable.
          It should include `{paramfile}` if Sumatra is to discover
          it.  If `argstr` is quoted, Sumatra will not parse it (and
          will not discover the `paramfile`).  This variable is
          resolved last.

        - `smtname` specifies the Sumatra project name.  If necessary,
          it will be used to initialize the "{rundir}" for Sumatra
          (and potentially for Git as well).

        - `smtprime` specifies a file name to use to initialize the
          Git repository, if needed.

        - `smtstore` specifies the database URL (or file name) to use
          for the Sumatra store.

        - `smtlabel` optional label for Sumatra for each run.

        - `smtreason` optional Sumatra "reason" for the run.
    '''

    canonical = (
        ('rundir','.'),
        ('datadir','.'),
        ('stdout','{datadir}/output.log'),
        ('stderr','{datadir}/error.log'),
        ('paramfile','{rundir}/params.json'),
        ('smtname',None),
        ('smtstore',"{rundir}/sumatra.sqlite"),   # replace with PSQL URL
        ('smtprime','{rundir}/readme-smt.txt'),
        ('executable',None),              # required
        ('argstr',''),
        )


    def run(self, cmd, **params):
        '''
        Run for Sumatra, needs potentially to initialize .smt and .git
        directories and call 'smt configure' before finally 'smt run'.
        '''
        self.initialize(**params)

        # warning: race condition. must run 'smt configure' just before
        # 'smt run' as we allow data directory to change between calls.

        cfgcmd = "smt configure -d {datadir}".format(**params)
        self.exec(cfgcmd, params['rundir'])   #fixme: move to run()
            
        self.exec(cmd, params['rundir'])
            
    def cmdline(self, **params):
        '''
        Return a command line from the parameters
        '''
        smtname = params.get('smtname',None)

        # Embed nominal command line in Sumatra command line.
        cmd = 'smt run '
        if 'smtlabel' in params:
            cmd += " -l {smtlabel}"
        if 'smtreason' in params:
            cmd += " -r {smtreason}"
        cmd += ' -e {executable} {argstr}'
        if 'stdout' in params:
            cmd+= ' >{stdout}'
        if 'stderr' in params:
            cmd += ' 2>{stderr}'

        return cmd.format(**params)

    def initialize(self, **params):
        '''
        Initialize rundir.
        '''
        rundir = params['rundir']
        self.assuredir(rundir)
        datadir = params['datadir']
        self.assuredir(datadir)

        smtname = params['smtname']       # required

        # Initialize git. 

        # Fixme: this probably does not do what the user wants if rundir is a
        # subdir of an existing project.

        dotgit = os.path.join(rundir, '.git')
        if not os.path.exists(dotgit):
            sc = self.exec("git init", rundir)

            touch = params.get("smtprime","readme.txt")
            touch_fp = os.path.join(rundir, touch)
            if not os.path.exists(touch_fp):
                with open(touch_fp, "w") as fp:
                    fp.write("Sumatra managed directory.")
            self.exec("git add %s"%touch, rundir)
            self.exec("git commit -am 'Initialize Sumatra project'", rundir)

        # Initialize Sumatra.

        dotsmt = os.path.join(rundir, '.smt')
        if os.path.exists(dotsmt):
            return
        cmd = "smt init -s {smtstore} -r . {smtname}".format(**params)
        self.exec(cmd, rundir)
        return
                
