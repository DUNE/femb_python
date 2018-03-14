
import os
import sys
from subprocess import Popen, PIPE, STDOUT, TimeoutExpired

def noop(text):
    pass

def execute(cmdstr, outcb=noop, errcb=noop, cwd = ".", env = os.environ, shell=True):
    '''
    Execute the given command string.  Return the exit code.

    The "cwd" sets the working directory in which to execute.

    If "env" is given it is used as an environment dictionary for the
    execution, o.w. os.environ will be used.

    If "out" is a callable taking two arguments which may be None or
    text.  It is called per poll of the running command if any text
    was produced on stdout/stderr.  

    If "shell" is True then the cmdstr is passed to the shell.

    OSError may be raised if cmdstr can not be executed.

    The return code from the command is returned.
    '''

    if not shell and type(cmdstr) == type(""):
        cmdstr = cmdstr.split()

    try:
        proc = Popen(cmdstr, stdout=PIPE, stderr=PIPE,
                         shell=shell, cwd=cwd, env=env,
                         bufsize=1, universal_newlines=True)   # line buffered
    except OSError as err:
        print (err)
        raise

    while True:
        try:
            o,e = proc.communicate(timeout=1)
            outcb(o)
            errcb(e)
        except TimeoutExpired:
            pass

        if proc.returncode is None:
            continue
        break
        
    if proc.returncode == 0: 
        return proc.returncode
    err = 'Command: "%s" failed with code %d in directory %s' % (cmdstr, proc.returncode, cwd)
    print (err)
    raise RuntimeError( err )


