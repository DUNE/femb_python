from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals
from __future__ import absolute_import
from builtins import range
from future import standard_library
standard_library.install_aliases()
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
from ...configuration.config_base import InitBoardError, SyncADCError, ConfigADCError

def setup_board(config,dataDir,adcSerialNumbers,startDateTime,operator,board_id,hostname,timestamp=None,sumatradict=None):
    """
    Sets up the ADC board

    config is the CONFIG object for the test board.
    dataDir  is the output directory for data files
    adcSerialNumbers is a list of a serial numbers for the ADC ASICS
    startDateTime string identifying the time the tests are started
    operator is the operator user name string
    board_id is the ID number of the test board
    hostname is the current computer name
    sumatradict is a dictionary of options that will be written to the summary json

    returns a list of bools whether an asic passed the tests. The list
        corresponds to the input serial number list.  
    """

    outfilename = "adcSetup_{}.json".format(startDateTime)
    outfilename = os.path.join(dataDir,outfilename)
    result = {
                "serials":adcSerialNumbers,
                "timestamp":startDateTime,
                "sumatra":sumatradict,
                "hostname":hostname,"board_id":board_id,
                "operator":operator,
                "sumatra": sumatradict,
             }
    result["pass"] = False;
    result["init"] = None;
    result["configADC"] = None;
    result["sync"] = None;
    with open(outfilename,"w") as outfile:
        config.POWERSUPPLYINTER.on()
        time.sleep(1)
        config.resetBoard(exitOnError=False)
        try:
            config.initBoard(exitOnError=False)
        except InitBoardError:
            print("Board/chip Failure: couldn't initialize board.")
            result["init"] = False;
            json.dump(result,outfile)
            config.POWERSUPPLYINTER.off()
            return
        except ConfigADCError:
            print("Board/chip Failure: couldn't write ADC SPI.")
            result["init"] = False;
            result["configADC"] = False;
            json.dump(result,outfile)
            config.POWERSUPPLYINTER.off()
            return
        else:
            result["init"] = True;
            result["configADC"] = True;
        try:
            config.syncADC(exitOnError=False)
        except SyncADCError:
            print("Board/chip Failure: couldn't sync ADCs.")
            result["sync"] = False;
            json.dump(result,outfile)
            config.POWERSUPPLYINTER.off()
            return
        else:
            result["sync"] = True;
        print("Successfully setup board.")
        result["pass"] = True;
        json.dump(result,outfile)

def main():
    from ...configuration.argument_parser import ArgumentParser
    from ...configuration import CONFIG

    ROOT.gROOT.SetBatch(True)

    timestamp = datetime.datetime.now().replace(microsecond=0).isoformat().replace(":","").replace("-","")

    parser = ArgumentParser(description="Sets up ADC board")
    parser.add_argument("-t", "--timestamp",help="Timestamp string to use for this test",type=str,default=timestamp)
    parser.add_argument("-o", "--operator",help="Test operator name",type=str,default="Command-line Operator")
    parser.add_argument("-s", "--serial",help="Chip serial number, use multiple times for multiple chips, e.g. -s 1 -s 2 -s 3 -s 4",action='append',default=[])
    parser.add_argument("-b", "--board",help="Test board serial number",default=None)
    parser.add_argument("-d", "--datadir",help="Directory for output data files",default="")
    parser.add_argument("-j", "--jsonfile",help="json options file location",default=None)
    args = parser.parse_args()
  
    config = CONFIG()
    chipsPass = None

    hostname = socket.gethostname()
    timestamp = args.timestamp
    operator = args.operator
    boardid = args.board
    serialNumbers = args.serial
    dataDir = args.datadir

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
            except KeyError as e:
                print("Error while parsing json input options: ",e)
                sys.exit(1)

    if len(serialNumbers) == 0:
        serialNumbers = list(range(-1,-(config.NASICS+1),-1))
    elif len(serialNumbers) != config.NASICS:
        print("Error: number of serial numbers ({}) doesn't equal number of ASICs in configuration ({}), exiting.".format(len(serialNumbers),config.NASICS))
        sys.exit(1)
    try:
        serialNumbers = [int(i) for i in serialNumbers]
    except ValueError as e:
        print("Error, serial number must be an int: ",e)
        sys.exit(1)

    try:
        chipsPass = setup_board(config,dataDir,serialNumbers,timestamp,operator,boardid,hostname,sumatradict=options)
    except Exception as e:
        print("Uncaught exception in setup_board. Traceback in stderr.")
        sys.stderr.write("Uncaught exception in setup_board: Error: {} {}\n".format(type(e),e))
        traceback.print_tb(e.__traceback__)
        config.POWERSUPPLYINTER.off()
        sys.exit(1)
