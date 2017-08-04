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
from ...configuration.config_base import InitBoardError, SyncADCError, ConfigADCError, ReadRegError

def setup_board(config,outfilename,adcSerialNumbers,startDateTime,operator,board_id,hostname,timestamp=None,power_on=True,power_off=True,sumatradict=None):
    """
    Sets up the ADC board

    config is the CONFIG object for the test board.
    outfilename is the output json filename
    adcSerialNumbers is a list of a serial numbers for the ADC ASICS
    startDateTime string identifying the time the tests are started
    operator is the operator user name string
    board_id is the ID number of the test board
    hostname is the current computer name
    power_cycle is a bool
    sumatradict is a dictionary of options that will be written to the summary json

    returns a list of bools whether an asic passed the tests. The list
        corresponds to the input serial number list.  
    """

    result = {
                "serials":adcSerialNumbers,
                "timestamp":startDateTime,
                "sumatra":sumatradict,
                "hostname":hostname,"board_id":board_id,
                "operator":operator,
                "sumatra": sumatradict,
             }
    result["pass"] = [False]*len(adcSerialNumbers);
    result["readReg"] = None;
    result["init"] = None;
    result["configADC"] = [None]*len(adcSerialNumbers);
    result["configFE"] = [None]*len(adcSerialNumbers);
    result["sync"] = [None]*len(adcSerialNumbers);
    result["havetofindsync"] = [None]*len(adcSerialNumbers);
    with open(outfilename,"w") as outfile:
        if power_on:
            config.POWERSUPPLYINTER.on()
        time.sleep(1)
        config.resetBoard()
        reg2 = config.femb.read_reg(1)
        if reg2 is None:
            print("Board/chip Failure: couldn't read a register.")
            result["readReg"] = False;
            json.dump(result,outfile)
            if power_off:
                config.POWERSUPPLYINTER.off()
            return
        else:
            result["readReg"] = True
        try:
            config.initBoard()
        except ReadRegError:
            print("Board/chip Failure: couldn't read a register so couldn't initialize board.")
            result["init"] = False;
            result["readReg"] = False;
            json.dump(result,outfile)
            if power_off:
                config.POWERSUPPLYINTER.off()
            return
        except InitBoardError:
            print("Board/chip Failure: couldn't initialize board.")
            result["init"] = False;
            json.dump(result,outfile)
            if power_off:
                config.POWERSUPPLYINTER.off()
            return
        except ConfigADCError:
            print("Board/chip Failure: couldn't write ADC SPI.")
            result["init"] = False;
            result["configADC"] = [False]*len(adcSerialNumbers);
            json.dump(result,outfile)
            if power_off:
                config.POWERSUPPLYINTER.off()
            return
        else:
            result["init"] = True;
            result["readReg"] = True;
        # check individual chip config
        feSPIStatus, adcSPIStatus, syncBits = config.getSyncStatus()
        result["configADC"] = adcSPIStatus
        result["configFE"] = feSPIStatus
        for iChip in range(len(adcSerialNumbers)):
            try:
                syncStatus = config.syncADC(iChip)
            except SyncADCError:
                print("Board/chip Failure: couldn't sync ADCs.")
                result["sync"][iChip] = False;
            else:
                result["sync"][iChip] = True;
                hadToSync = syncStatus[0]
                result["havetofindsync"][iChip] = hadToSync
        for iChip in range(len(adcSerialNumbers)):
            if adcSPIStatus[iChip]:
                if feSPIStatus[iChip]:
                    if result["sync"][iChip]:
                        result["pass"][iChip] = True
        print("Successfully setup board.")
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
    parser.add_argument("-f", "--outfilename",help="Output file name",default="adcSetup.json")
    parser.add_argument("-j", "--jsonfile",help="json options file location",default=None)
    args = parser.parse_args()
  
    config = CONFIG(exitOnError=False)
    chipsPass = None

    hostname = socket.gethostname()
    timestamp = args.timestamp
    operator = args.operator
    boardid = args.board
    serialNumbers = args.serial
    outfilename = args.outfilename
    power_on = True
    power_off = True

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
                outfilename = options["outfilename"]
                power_on = options["power_on"]
                power_off = options["power_off"]
            except KeyError as e:
                print("Error while parsing json input options: ",e)
                sys.exit(1)

    if len(serialNumbers) == 0:
        serialNumbers = list(range(-1,-(config.NASICS+1),-1))
    elif len(serialNumbers) != config.NASICS:
        print("Error: number of serial numbers ({}) doesn't equal number of ASICs in configuration ({}), exiting.".format(len(serialNumbers),config.NASICS))
        sys.exit(1)
    try:
        chipsPass = setup_board(config,outfilename,serialNumbers,timestamp,operator,boardid,hostname,power_on=power_on,power_off=power_off,sumatradict=options)
    except Exception as e:
        print("Uncaught exception in setup_board. Traceback in stderr.")
        sys.stderr.write("Uncaught exception in setup_board: Error: {} {}\n".format(type(e),e))
        traceback.print_tb(e.__traceback__)
        if power_off:
            config.POWERSUPPLYINTER.off()
        sys.exit(1)
