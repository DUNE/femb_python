from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals
from __future__ import absolute_import
from builtins import range
from future import standard_library
standard_library.install_aliases()
from ...femb_udp import FEMB_UDP
from ...test_instrument_interface import RigolDG4000
from ...write_root_tree import WRITE_ROOT_TREE
import sys
import os.path
import time
import datetime
import glob
from uuid import uuid1 as uuid
import json
import socket
import traceback
from subprocess import CalledProcessError
import numpy
import matplotlib.pyplot as plt
import ROOT
from .collect_data import COLLECT_DATA 
from ...configuration.config_base import FEMBConfigError

def runTests(config,dataDir,adcSerialNumbers,startDateTime,operator,board_id,hostname,timestamp=None,sumatradict=None,iTry=1):
    """
    Runs the ADC tests for all chips on the ADC test board.

    config is the CONFIG object for the test board.
    dataDir  is the output directory for data files
    adcSerialNumbers is a list of a serial numbers for the ADC ASICS
    startDateTime string identifying the time the tests are started
    operator is the operator user name string
    board_id is the ID number of the test board
    hostname is the current computer name
        all offset current settings settings.
    sumatradict is a dictionary of options that will be written to the summary json

    returns a list of bools whether an asic passed the tests. The list
        corresponds to the input serial number list.  
    """

    collect_data = COLLECT_DATA(config)

    sampleRate = 2000000
    clock = 0 # -1 undefined, 0 external, 1 internal monostable, 2 internal FIFO
    offset = -1

    for iChip in range(config.NASICS):
        print("Collecting David Adams data for sample rate: {} clock: {} offset: {} chip: {} try: {}...".format(sampleRate, clock, offset, iChip,iTry))
        sys.stdout.flush()
        sys.stderr.flush()
        chipStats = {}
        fileprefix = "adcDavidAdamsOnlyData_{}_chip{}_adcClock{}_adcOffset{}_sampleRate{}".format(startDateTime,adcSerialNumbers[iChip],clock,offset,sampleRate)
        fileprefix = os.path.join(dataDir,fileprefix)
        filesuffix = "_try{}".format(iTry)
        try:
            collect_data.getData(fileprefix,iChip,adcClock=clock,adcOffset=offset,adcSerial=adcSerialNumbers[iChip],sampleRate=sampleRate,longRampOnly=True,outSuffix=filesuffix)
        except Exception as e:
            print("Error while collecting David Adams data, traceback in stderr.")
            sys.stderr.write("Error collecting David Adams data for sample rate: {} clock: {} offset: {} chip: {} try: {} Error: {} {}\n".format(sampleRate, clock, offset, iChip, iTry, type(e),e))
            traceback.print_tb(e.__traceback__)
            continue

def main():
    from ...configuration.argument_parser import ArgumentParser
    from ...configuration import CONFIG
    import json

    ROOT.gROOT.SetBatch(True)

    timestamp = datetime.datetime.now().replace(microsecond=0).isoformat().replace(":","").replace("-","")

    parser = ArgumentParser(description="Collects David Adams data. Assumes board is already in a good state 2 MHz no offset, ext clock")
    parser.add_argument("-t", "--timestamp",help="Timestamp string to use for this test",type=str,default=timestamp)
    parser.add_argument("-o", "--operator",help="Test operator name",type=str,default="Command-line Operator")
    parser.add_argument("-s", "--serial",help="Chip serial number, use multiple times for multiple chips, e.g. -s 1 -s 2 -s 3 -s 4",action='append',default=[])
    parser.add_argument("-b", "--board",help="Test board serial number",default=None)
    parser.add_argument("-d", "--datadir",help="Directory for output data files",default="")
    parser.add_argument("-p", "--profiler",help="Enable python timing profiler and save to given file name",type=str,default=None)
    parser.add_argument("-j", "--jsonfile",help="json options file location",default=None)
    args = parser.parse_args()
  
    config = CONFIG(exitOnError=False)
    chipsPass = None
    startTime = datetime.datetime.now()

    hostname = socket.gethostname()
    timestamp = args.timestamp
    operator = args.operator
    boardid = args.board
    serialNumbers = args.serial
    dataDir = args.datadir
    iTry = 1

    options = None

    if args.jsonfile:
        with open(args.jsonfile) as jsonfile:
            options = json.load(jsonfile)
            try:
                hostname = options["hostname"]
                timestamp = options["timestamp"]
                operator = options["operator"]
                boardid = options["board_id"]
                serialNumbers = options["serials"]
                dataDir = options["datadir"]
                iTry = options["iTry"]
            except KeyError as e:
                print("Error while parsing json input options: ",e)
                sys.exit(1)

    if len(serialNumbers) == 0:
        serialNumbers = list(range(-1,-(config.NASICS+1),-1))
    elif len(serialNumbers) != config.NASICS:
        print("Error: number of serial numbers ({}) doesn't equal number of ASICs in configuration ({}), exiting.".format(len(serialNumbers),config.NASICS))
        sys.exit(1)

    try:
        if args.profiler:
            import cProfile
            cProfile.runctx('chipsPass = runTests(config,dataDir,serialNumbers,timestamp,operator,boardid,hostname,sumatradict=options,iTry=iTry)',globals(),locals(),args.profiler)
        else:
            chipsPass = runTests(config,dataDir,serialNumbers,timestamp,operator,boardid,hostname,sumatradict=options,iTry=iTry)
    except Exception as e:
        print("Uncaught exception in runTests. Traceback in stderr.")
        sys.stderr.write("Uncaught exception in runTests: Error: {} {}\n".format(type(e),e))
        traceback.print_tb(e.__traceback__)
        sys.exit(1)
    else:
        runTime = datetime.datetime.now() - startTime
        print("Test took: {:.0f} min {:.1f} s".format(runTime.total_seconds() // 60, runTime.total_seconds() % 60.))
        print("Chips Pass: ",chipsPass)
