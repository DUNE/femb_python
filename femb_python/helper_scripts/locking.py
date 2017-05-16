"""
Locking functionality
"""
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import
import fcntl
import time
import sys
import os
import pwd

MANUAL_LOCK_PATH="/tmp/femb_python_manual_lock"
AUTOMATIC_LOCK_PATH="/tmp/femb_python_auto_lock"
WRAPPER_LOCATION="helper_scripts/lock_wrapper.sh"

class NoLockError(Exception):
    pass

class FEMB_LOCK(object):
    """
    Locking context for FEMB
    Checks both an automaticly locked/unlocked 
    lock and a manual lock
    """
    def __init__(self):
        self.fp = None

    def lock(self):
        """
        Lock the lock file and check the manual lock
        """
        try:
            val = os.environ["FEMB_MANUAL_LOCK_OVERRIDE"] # KeyError if variable not defined
        except KeyError:
            try:
                userid = os.stat(MANUAL_LOCK_PATH).st_uid
                username = pwd.getpwuid(userid).pw_name
                print("Error: The manual lock file exists, {} created by user: '{}'. Exiting.".format(MANUAL_LOCK_PATH,username))
                sys.exit(1)
            except FileNotFoundError:
                pass
        if not (self.fp is None):
            self.unlock()
        # checking pid and username in case somebody else has the lock
        pid = None
        username = None
        try:
            with open(AUTOMATIC_LOCK_PATH) as pidf:
                pid = str(pidf.read(100))
            userid = os.stat(AUTOMATIC_LOCK_PATH).st_uid
            username = pwd.getpwuid(userid).pw_name
        except FileNotFoundError:
            pass
        # now actually locking
        self.fp = open(AUTOMATIC_LOCK_PATH,"a+")
        try:
            fcntl.flock(self.fp, fcntl.LOCK_EX|fcntl.LOCK_NB)
            self.fp.truncate(0) # delete content if somehow already exists
            self.fp.write(str(os.getpid()))
            self.fp.flush()
            os.fsync(self.fp.fileno())
        except BlockingIOError as e:
            print("Error: FEMB automatic lock user: '{}' pid: {}. Exiting.".format(username,pid))
            sys.exit(1)

    def unlock(self):
        """
        Unlock (close) the lock file
        """
        if self.fp is None:
            raise NoLockError("No lock to unlock, try locking first")
        self.fp.close()
        self.fp = None
        try:
            os.remove(AUTOMATIC_LOCK_PATH)
        except:
            pass

    def __enter__(self):
        """
        Does with statement
        """
        return self.lock()

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Handles errors when exiting with statement
        """
        self.unlock()
        if exc_type is None:
            return True
        else:
            return False

def lock():
    """
    Lock the manual per user lock
    """

    import subprocess
    from ..configuration.cppfilerunner import CPP_FILE_RUNNER

    wrapperFileName = CPP_FILE_RUNNER().filename(WRAPPER_LOCATION)
    command = ['flock','--nonblock',MANUAL_LOCK_PATH,'-c','"/bin/bash --rcfile {}"'.format(wrapperFileName)]
    command = " ".join(command)
    #print(WRAPPER_LOCATION,wrapperFileName)
    #print(command)
    try:
        subprocess.check_call(command,shell=True)
        try:
            os.remove(MANUAL_LOCK_PATH)
        except:
            pass
    except subprocess.CalledProcessError as e:
        print("Error getting lock: Somebody else probably has the lock already.\n  Run lslocks and identify the user locking {}".format(MANUAL_LOCK_PATH))
        sys.exit(1)

# Just for testing
if __name__ == "__main__":
    with FEMB_LOCK() as lock:
        time.sleep(20)
    
