#!/usr/bin/env python3

import os
from subprocess import Popen, PIPE, STDOUT

def dump(oline, eline):
    if oline:
        print ("Output: %s" % oline)
    if eline:
        print ("Output: %s" % eline)


def execute(cmdstr, cwd = ".", env = os.environ, out = dump, shell=True):
    '''
    Execute the given command string.  Return the exit code.

    The "cwd" sets the working directory in which to execute.

    If "env" is given it is used as an environment dictionary for the
    execution, o.w. os.environ will be used.

    If "out" is given it will be called once with either a line of
    output or a line of error or both.  It may be called multiple
    times as the process runs.  Any trailing newline on a line is
    stripped.

    If "shell" is True then the cmdstr is passed to the shell.

    OSError may be raised if cmdstr can not be executed.

    The return code from the command is returned.
    '''

    if not shell and type(cmdstr) == type(""):
        cmdstr = cmdstr.split()

    def slurp(oline, eline):                   # send line to all outs
        if oline and oline[-1] == '\n':
            oline = oline[:-1]
        if eline and eline[-1] == '\n':
            eline = eline[:-1]
        out(oline, eline)
        return

    print('Executing: %s' % cmdstr)
    try:
        proc = Popen(cmdstr, stdout=PIPE, stderr=PIPE, shell=shell, cwd=cwd,
                     universal_newlines=True, env=env)
    except OSError as err:
        print (err)
        raise

    
    # While command is polled as running, slurp its output and marshal
    # it to out() until command finishes
    res = None
    while True:
        oline = proc.stdout.readline()
        eline = proc.stderr.readline()
        res = proc.poll()

        if oline or eline:
            slurp(oline, eline)

        if res is None:         # still running
            continue

        for line in proc.stdout.readlines():
            slurp(line,None)                     # drain any remaining
        for line in proc.stderr.readlines():
            slurp(None,line)                     # drain any remaining

        break

    if res == 0: 
        print('Command: "%s" succeeded' % cmdstr)
        return proc.returncode
    err = 'Command: "%s" failed with code %d in directory %s' % (cmdstr, res, cwd)
    print (err)
    raise RuntimeError( err )


