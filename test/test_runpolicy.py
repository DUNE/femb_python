#!/usr/bin/env python3
'''
$ sudo apt-get install python3-dev python3-numpy python3-matplotlib
$ virtualenv -p python3 --system-site-packages venv
$ source venv/bin/activate

$ python setup.py develop

# fixme: this needs to be added to setup.py
$ pip install sumatra gitpython

$ python3 test/test_runpolicy.py 


'''


from femb_python.runpolicy import Runner, DirectRunner, SumatraRunner

import shutil
import json
import time
import os

# for real app, this unique jobid would be generated from user input 
jobid = time.strftime("%Y%m%d-%H%M%S", time.gmtime(time.time()))

basedir = os.path.realpath('./test_runpolicy')
rundir = os.path.join(basedir,"rundir")
datadir = os.path.join(basedir,"datadir-%s"%jobid)
paramfile = os.path.join(datadir,"params.json")

def clear():
    if not os.path.exists(basedir):
        return
    shutil.rmtree(basedir)

def make_runner(klass, **params):
    defaults = dict(
        executable="/bin/cp",
        argstr="{paramfile} {datadir}/{jobid}.dat",
        jobid=jobid,
        paramfile=paramfile,
        rundir=rundir,
        datadir=datadir)
    defaults.update(params)
    r = klass(**defaults)
    return r

def check_dicts(d1, d2):
    for k,v in d1.items():
        if k in d2:
            assert (v == d2[k])

    for k,v in d2.items():
        if k in d1:
            assert (v == d1[k])

def test_basic():
    clear()
    r = Runner(cmdline="/bin/pwd")
    p = r()
    print (p)

def test_direct():
    clear()
    r = DirectRunner(executable="/bin/ls",
                         argstr="-l",
                         rundir=rundir,
                         paramfile="{rundir}/params.json",
                         stdout="{rundir}/output.log",
                         stderr="{rundir}/error.log")
    r()

def test_default_args_only():
    clear()
    r = make_runner(DirectRunner)
    params = r.resolve()
    r()
    params2 = json.load(open(params['paramfile']))
    check_dicts(params, params2)

def test_per_call_args():
    clear()
    r = make_runner(DirectRunner)

    per_call = dict(par1="foo", par2=42, par3=6.9,
                        executable="/bin/ls",
                        argstr="-l {paramfile}")

    p1 = r.resolve(**per_call)
    r(**per_call)
    p2 = json.load(open(p1['paramfile']))
    check_dicts(p1,p2)
    
def test_with_sumatra():
    clear()
    r = make_runner(SumatraRunner, smtname="test_with_sumatra")
    r()

def test_with_sumatra_pgsql():
    clear()
    r = make_runner(SumatraRunner, smtname="test_with_sumatra",
                    smtstore="postgres://cetester_bviren@hothstor2.phy.bnl.gov/cetest_bviren")
    r()

    
def test_fail():
    clear()
    r = make_runner(SumatraRunner, smtname="test_fail", executable="/bin/false")
    try:
        r()
    except RuntimeError:
        print ("Test of /bin/false successfully failed.")
        pass
    else:
        raise RuntimeError("test of /bin/false failed to fail")

if '__main__' == __name__:
    test_basic()
    test_direct()
    test_default_args_only()
    test_per_call_args()
    test_with_sumatra()
    test_fail()
    
