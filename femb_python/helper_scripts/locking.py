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
        if os.path.exists(MANUAL_LOCK_PATH):
            userid = os.stat(MANUAL_LOCK_PATH).st_uid
            myuserid = os.getuid()
            if userid != myuserid:
                username = pwd.getpwuid(userid).pw_name
                print("Error: Another user has set the manual lock. User: '{}'. Exiting.".format(username))
                sys.exit(1)
        if not (self.fp is None):
            self.unlock()
        self.fp = open(AUTOMATIC_LOCK_PATH,"w")
        try:
            fcntl.flock(self.fp, fcntl.LOCK_EX|fcntl.LOCK_NB)
            self.fp.write(str(os.getpid()))
            self.fp.flush()
            os.fsync(self.fp.fileno())
        except BlockingIOError as e:
            self.fp.close()
            pid = None
            with open(AUTOMATIC_LOCK_PATH) as pidf:
                pid = str(pidf.read(100))
            userid = os.stat(AUTOMATIC_LOCK_PATH).st_uid
            username = pwd.getpwuid(userid).pw_name
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
    
    try:
        f = open(MANUAL_LOCK_PATH,"x")
    except FileExistsError as e:
        userid = os.stat(MANUAL_LOCK_PATH).st_uid
        myuserid = os.getuid()
        if myuserid != userid:
          username = pwd.getpwuid(userid).pw_name
          print("Error: Another user has set the manual lock. User: '{}'. Exiting.".format(username))
          sys.exit(1)

def unlock():
    """
    Unlock the manual per user lock
    """
    try:
        userid = os.stat(MANUAL_LOCK_PATH).st_uid
        myuserid = os.getuid()
        if myuserid == userid:
            os.remove(MANUAL_LOCK_PATH)
        else:
            username = pwd.getpwuid(userid).pw_name
            print("Error: Another user has set the manual lock. User: '{}'. Exiting.".format(username))
            sys.exit(1)
    except FileNotFoundError as e:
        print("Warning in unlock: lock file doesn't exist")

# Just for testing
if __name__ == "__main__":
    with FEMB_LOCK() as lock:
        time.sleep(20)
    
