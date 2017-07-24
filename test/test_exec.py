#!/usr/bin/env python3

from femb_python import commands


cmdstr = "echo o1 && echo e1 1>&2 && sleep 1 && echo o2 && echo e2 1>&2 && sleep 1 && echo o3 && echo e3 1>&2"

def test_simple():
    """
    Test simple poll-based execution
    """
    sc = commands.execute(cmdstr)
    assert (sc == 0)

def test_fail():
    """
    Test simple poll-based execution
    """
    try:
        sc = commands.execute(cmdstr + "&& /bin/false")
    except RuntimeError as err:
        print ("Correctly caught error:\n%s" % err)
        print ("^^^ above error caught as expected")
    else:
        raise RuntimeError("Failed to raise runtime error")


if '__main__' == __name__:
    test_simple()
    test_fail()

    
