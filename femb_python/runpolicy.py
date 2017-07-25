#!/usr/bin/env python3
'''
This module provides the class Runner that can be used to run programs
(ie CE testing module scripts) in a way that enforces certain policy
while delegating some policy to the caller.  See documentation for
Runner for more information.

'''
import os
import sys
import json
import time
#import subprocess
from . import commands
from collections import namedtuple

class Runner(object):
    '''A Runner runs a program as governed by a parameter set.

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
    the corresponding value.  

    When the runner is called, and if the executable returns
    successfully then the resolved parameter set is returned.

    If the executable does not exit successfully then a RuntimeError
    is raised.

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
        '''Execute `cmdline` with parameters in the run directory.

        The `user_params` dictionary is merged into any defaults given
        to the constructor and then resolved.

        If 'paramfile' is a parameter, the parameters will be saved to
        it as JSON.
        '''
        params = self.resolve(**user_params)

        # prepare param file if its wanted.
        paramfile = params.get('paramfile')
        if paramfile:
            print ("Running with parameter file pattern: %s" % paramfile)
            pdir = os.path.dirname(paramfile)
            self.assuredir(pdir)
            with open(paramfile, 'w') as fp:
                fp.write(json.dumps(params, indent=4));

        cmd = self.cmdline(**params)
        self.run(cmd, **params)
        return params;

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

        if cwd == ".":
            print ("which is: %s" % os.path.realpath(cwd))

        stdout = list()
        stderr = list()
        def output(text):
            if not text: return
            stdout.append(text)
            sys.stdout.write("Output: " + text)
            sys.stdout.flush()
        def errput(text):
            if not text: return
            stderr.append(text)
            sys.stderr.write("Error: " + text)

        rc = commands.execute(cmdstr, output, errput,
                                  shell=shell, cwd=cwd)

        stdout = '\n'.join(stdout)
        stderr = '\n'.join(stderr)
        
        self.last_sc = namedtuple("outerr","stdout stderr rc")(stdout, stderr, rc)

    def resolve(self, **user_params):

        params = self.default_params.copy()
        params.update(user_params)

        # make sure canonical reserved params are there
        for name, default in self.canonical:
            val = params.get(name, default)
            params[name] = val

        while True:             # warning: cycles will loop 
            newparams = dict()
            changes = 0
            for var, val in sorted(params.items()):
                if type(val) != str:
                    newparams[var] = val
                    continue
                newval = val.format(**params)
                if val != newval:
                    changes += 1
                newparams[var] = newval
            if not changes:
                return newparams
            params = newparams  # around again

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
        if params.get('stdout'):
            cmd += ' >{stdout}'
        if params.get('stderr'):
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
        ('stdout',None),
        ('stderr',None),
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
        self.exec(cfgcmd, params['rundir'])
            
        self.exec(cmd, params['rundir'])
        # stupid smt run eats return code
        err = self.last_sc.stderr
        if err.startswith("WARNING:root:Returned:"):
            parts = self.last_sc.stderr.split()
            if parts[1] != "0":
                raise RuntimeError('Failed to run "%s"' % cmd)
                
            
    def cmdline(self, **params):
        '''
        Return a command line from the parameters
        '''

        # Embed nominal command line in Sumatra command line.
        cmd = 'smt run '
        if params.get('smtlabel'):
            cmd += " -l {smtlabel}"
        if params.get('smtreason'):
            cmd += " -r {smtreason}"
        if params.get('smttag'): # comma-separated list
            cmd += " -t {smttag}"
        cmd += ' -e {executable} {argstr}'
        if params.get('stdout'):
            cmd+= ' >{stdout}'
        if params.get('stderr'):
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
        smtstore = params['smtstore']
        print ("Initializing Sumatra: %s at %s" % (smtname, smtstore))

        # Initialize git. 

        # Fixme: this probably does not do what the user wants if rundir is a
        # subdir of an existing project.

        dotgit = os.path.join(rundir, '.git')
        if not os.path.exists(dotgit):
            print ("Initializing Git in: %s" % rundir)
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
        print ("Initializing Sumatra in: %s" % rundir)
        cmd = "smt init -s {smtstore} -r . {smtname}".format(**params)
        self.exec(cmd, rundir)
        return
                
import os
import getpass                            # for getuser

def make_runner(test_category, use_sumatra=True, **params):
    '''
    Default parameters for a CE testing.  This enforces some
    parameters to be added through the argument list and divines many
    others from the environment.
    '''

    try:
        params["femb_config"] = os.environ["FEMB_CONFIG"]  # required
    except KeyError:
        print( "ERROR RUNPOLICY - Please set the environment variable FEMB_CONFIG" )
        return None

    # Check out the data disk situation and find the most available disk
    freedisks = list()
    datadisks=["/tmp"]
    hostname = os.uname()[1]
    if hostname.startswith("hoth"):
        datadisks = ["/dsk/1", "/dsk/2"]
    for dd in datadisks:
        stat = os.statvfs(dd)
        MB = stat.f_bavail * stat.f_frsize >> 20
        freedisks.append((MB, dd))
    freedisks.sort()
    params.update(lo_disk = freedisks[0][1], hi_disk = freedisks[-1][1])

    now = time.time()
    params["session_start_time"] = time.strftime("%Y%m%dT%H%M%S", time.localtime(now))
    params["session_start_unix"] = now

    params["user"] = getpass.getuser()
    if params["user"] == "oper":
        params["datadisk"] = "{lo_disk}/data"
    else:
        params["datadisk"] = "{lo_disk}/tmp"

    params.update(test_category = test_category,
                      hostname = hostname,
                      rundir = "/home/{user}/run",
                      datasubdir = ".",   # probably each user should provide this
                      outlabel = "",      # and this
                      datadir = "{datadisk}/{user}/{test_category}/{femb_config}/{session_start_time}/{datasubdir}",
                      paramfile = "{datadir}/params.json",
                      smtname = "{test_category}",
                      smttag = "{hostname},{datadisk}",
                      femb_python_location = os.path.dirname(__file__))
    
    if not use_sumatra:
        return DirectRunner(**params)

    print ("Using Sumatra")
    pghost = os.environ.get("PGHOST")
    if pghost:
        print (" with PostgreSQL database at %s" % pghost)
        params.update(
            smtstore="postgres://{pguser}@{pghost}/{pgdatabase}",
            pguser = os.environ['PGUSER'],
            pghost = os.environ['PGHOST'],
            pgdatabase = os.environ['PGDATABASE'],
        )
    else:
        print (" with Sqlite3 database in rundir")
    return SumatraRunner(**params)
