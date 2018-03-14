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
from .calibrate_ramp import CALIBRATE_RAMP
from .static_tests import STATIC_TESTS
from .dynamic_tests import DYNAMIC_TESTS
from .baseline_rms import BASELINE_RMS
from .dc_tests import DC_TESTS
from .test_summary import ADC_TEST_SUMMARY
from .summary_plots import SUMMARY_PLOTS
from ...configuration.config_base import FEMBConfigError

def resetBoardAndProgramFirmware(config,sampleRate):
    programFunc = None
    nTries = 2
    for iPowerCycle in range(2):
        for iTry in range(iPowerCycle*nTries,nTries+iPowerCycle*nTries):
            sys.stdout.flush()
            sys.stderr.flush()
            try:
                if sampleRate == 2000000:
                    if hasattr(config,"FIRMWAREPATH2MHZ"):
                        programFunc = config.programFirmware2Mhz
                    else:
                        print("No 2 MHz firmware path configured, not programming firmware.")
                        return True
                elif sampleRate == 1000000:
                    if not hasattr(config,"FIRMWAREPATH1MHZ"):
                        print("No 1 MHz firmware path configured, skipping.")
                        continue
                    programFunc = config.programFirmware1Mhz
                else:
                    print("Error: Sample rate not 1 MHz or 2 MHz: ",sampleRate)
                    continue
                programFunc()
                config.resetBoard()
                config.initBoard()
                config.syncADC()
            except FEMBConfigError as e:
                sys.stdout.flush()
                sys.stderr.flush()
                sys.stderr.write("Error while reset/init/sync board: Error: {} {}\n".format(type(e),e))
                traceback.print_tb(e.__traceback__)
            except CalledProcessError as e:
                sys.stdout.flush()
                sys.stderr.flush()
                sys.stderr.write("Error while programming firmware: Error: {} {}\n".format(type(e),e))
                traceback.print_tb(e.__traceback__)
            else: # success if no exception :-)
                return True
            sys.stdout.flush()
            sys.stderr.flush()
            print("Reset/init/sync/firmware try {} failed, trying again...".format(iTry))
        print("Reset/init/sync/firmware trying power cycle and {} more tries...".format(nTries))
        config.POWERSUPPLYINTER.off()
        time.sleep(0.5)
        config.POWERSUPPLYINTER.on()
        time.sleep(0.5)
    print("Unable to reset/init/sync/firmware.")
    return False

def configAdcAsic(config,sampleRate,offsetCurrent=None,
                    clockMonostable=None,clockFromFIFO=None,
                    clockExternal=None,testInput=None):
    enableOffsetCurrent = 0
    if offsetCurrent >= 0:
        enableOffsetCurrent = 1
    else:
        offsetCurrent = 0
    nTries = 2
    for iPowerCycle in range(2):
        for iTry in range(iPowerCycle*nTries,nTries+iPowerCycle*nTries):
            sys.stdout.flush()
            sys.stderr.flush()
            try:
                config.configAdcAsic(enableOffsetCurrent=enableOffsetCurrent,offsetCurrent=offsetCurrent,
                            clockMonostable=clockMonostable,clockFromFIFO=clockFromFIFO,
                            clockExternal=clockExternal,testInput=testInput)
            except FEMBConfigError as e:
                sys.stdout.flush()
                sys.stderr.flush()
                sys.stderr.write("Error while configAdcAsic: Error: {} {}\n".format(type(e),e))
                traceback.print_tb(e.__traceback__)
            else: # success if no exception :-)
                return True
            print("configAdcAsic try {} failed, trying again...".format(iTry))
        print("configAdcAsic trying power cycle and {} more tries...".format(nTries))
        config.POWERSUPPLYINTER.off()
        time.sleep(0.5)
        config.POWERSUPPLYINTER.on()
        time.sleep(0.5)
        resetSuccess = resetBoardAndProgramFirmware(config,sampleRate)
        if not resetSuccess:
            return False
    print("Unable to configAdcAsic.")
    return False

def runTests(config,dataDir,adcSerialNumbers,startDateTime,operator,board_id,hostname,quick=False,timestamp=None,sumatradict=None):
    """
    Runs the ADC tests for all chips on the ADC test board.

    config is the CONFIG object for the test board.
    dataDir  is the output directory for data files
    adcSerialNumbers is a list of a serial numbers for the ADC ASICS
    startDateTime string identifying the time the tests are started
    operator is the operator user name string
    board_id is the ID number of the test board
    hostname is the current computer name
    quick is a boolean. If True only test the ASICS with no offset current. If False test 
        all offset current settings settings.
    sumatradict is a dictionary of options that will be written to the summary json

    returns a list of bools whether an asic passed the tests. The list
        corresponds to the input serial number list.  
    """

    collect_data = COLLECT_DATA(config)
    static_tests = STATIC_TESTS(config)
    dynamic_tests = DYNAMIC_TESTS(config)
    baseline_rms = BASELINE_RMS()
    dc_tests = DC_TESTS(config)

    sampleRates = [2000000,1000000]
    clocks = [0,1] # -1 undefined, 0 external, 1 internal monostable, 2 internal FIFO
    offsets = range(-1,16)
    if quick:
        offsets = [-1]

    allStatsRaw = {}
    isError = {}
    for adcSerialNumber in adcSerialNumbers:
        isError[adcSerialNumber] = False
    for sampleRate in sampleRates:
        print("Programming firmware for sample rate: {} ...".format(sampleRate))
        sys.stdout.flush()
        sys.stderr.flush()
        config.SAMPLERATE = float(sampleRate)
        resetAndProgramSuccess = resetBoardAndProgramFirmware(config,sampleRate)
        if not resetAndProgramSuccess:
            continue
        static_tests.samplingFreq = float(sampleRate)
        dynamic_tests.sampleRate = float(sampleRate)
        allStatsRaw[sampleRate] = {}
        for clock in clocks: # -1 undefined, 0 external, 1 internal monostable, 2 internal FIFO
            allStatsRaw[sampleRate][clock] = {}
            clockMonostable=False
            clockFromFIFO=False
            clockExternal=False
            if clock == 0:
                clockExternal=True
            elif clock == 1:
                clockMonostable=True
            else:
                clockFromFIFO=True
            for offset in offsets:
                configStats = {}
                print("Configuring ADC for sample rate: {} clock: {} offset: {} ...".format(sampleRate, clock, offset))
                sys.stdout.flush()
                sys.stderr.flush()
                configSuccess = configAdcAsic(config,sampleRate,
                            offsetCurrent=offset,
                            clockMonostable=clockMonostable,clockFromFIFO=clockFromFIFO,
                            clockExternal=clockExternal,testInput=1)
                if not configSuccess:
                    continue
                longRamp = (clock == 0 and offset == -1)
                feSPI, adcSPI, syncBits = config.getSyncStatus()
                for iChip in range(config.NASICS):
                    if not adcSPI[iChip]:
                        print("SPI readback failed, so skipping sample rate: {} clock: {} offset: {} chip: {} ...".format(sampleRate, clock, offset, iChip))
                        continue
                    print("Collecting data for sample rate: {} clock: {} offset: {} chip: {} ...".format(sampleRate, clock, offset, iChip))
                    sys.stdout.flush()
                    sys.stderr.flush()
                    chipStats = {}
                    fileprefix = "adcTestData_{}_chip{}_adcClock{}_adcOffset{}_sampleRate{}".format(startDateTime,adcSerialNumbers[iChip],clock,offset,sampleRate)
                    fileprefix = os.path.join(dataDir,fileprefix)
                    try:
                        collect_data.getData(fileprefix,iChip,adcClock=clock,adcOffset=offset,adcSerial=adcSerialNumbers[iChip],sampleRate=sampleRate,longRamp=longRamp)
                    except Exception as e:
                        isError[adcSerialNumbers[iChip]] = True
                        print("Error while collecting data, traceback in stderr.")
                        sys.stderr.write("Error collecting data for sample rate: {} clock: {} offset: {} chip: {} Error: {} {}\n".format(sampleRate, clock, offset, iChip,type(e),e))
                        traceback.print_tb(e.__traceback__)
                        continue
                    print("Processing...")
                    static_fns = list(glob.glob(fileprefix+"_functype3_freq734.*.root"))
                    assert(len(static_fns)==1)
                    static_fn = static_fns[0]
                    dc_fns = list(glob.glob(fileprefix+"_functype1_*.root"))
                    try:
                        CALIBRATE_RAMP(static_fn,sampleRate).write_calibrate_tree()
                    except Exception as e:
                        isError[adcSerialNumbers[iChip]] = True
                        print("Error while calibrating ramp, traceback in stderr.")
                        sys.stderr.write("Error calibrating ramp for sample rate: {} clock: {} offset: {} chip: {} Error: {} {}\n".format(sampleRate, clock, offset, iChip,type(e),e))
                        traceback.print_tb(e.__traceback__)
                    try:
                        staticStats = static_tests.analyzeLinearity(static_fn,diagnosticPlots=False)
                        chipStats["static"] = staticStats
                    except Exception as e:
                        isError[adcSerialNumbers[iChip]] = True
                        print("Error while performing static tests, traceback in stderr.")
                        sys.stderr.write("Error in static tests for sample rate: {} clock: {} offset: {} chip: {}  Error: {} {}\n".format(sampleRate, clock, offset, iChip,type(e),e))
                        traceback.print_tb(e.__traceback__)
                    try:
                        dynamicStats = dynamic_tests.analyze(fileprefix,diagnosticPlots=False)
                        chipStats["dynamic"] = dynamicStats
                    except Exception as e:
                        isError[adcSerialNumbers[iChip]] = True
                        print("Error while performing dynamic tests, traceback in stderr.")
                        sys.stderr.write("Error in dynamic tests for sample rate: {} clock: {} offset: {} chip: {}  Error: {} {}\n".format(sampleRate, clock, offset, iChip,type(e),e))
                        traceback.print_tb(e.__traceback__)
                    try:
                        dcStats = dc_tests.analyze(dc_fns,verbose=False)
                        chipStats["dc"] = dcStats
                    except Exception as e:
                        isError[adcSerialNumbers[iChip]] = True
                        print("Error while performing dc tests, traceback in stderr.")
                        sys.stderr.write("Error in dc tests for sample rate: {} clock: {} offset: {} chip: {} Error: {} {}\n".format(sampleRate, clock, offset, iChip,type(e),e))
                        traceback.print_tb(e.__traceback__)
                    configStats[adcSerialNumbers[iChip]] = chipStats
                    #with open(fileprefix+"_statsRaw.json","w") as f:
                    #    json.dump(chipStats,f)
                allStatsRaw[sampleRate][clock][offset] = configStats
    # check the input pin works
    sampleRate = 2000000
    clock=0
    offset = -1
    clockMonostable=False
    clockFromFIFO=False
    clockExternal=True
    configSuccess = configAdcAsic(config,sampleRate,offsetCurrent=offset,
                        clockMonostable=clockMonostable,clockFromFIFO=clockFromFIFO,
                        clockExternal=clockExternal,testInput=0)
    if configSuccess:
        for iChip in range(config.NASICS):
            print("Collecting input pin data for chip: {} ...".format(iChip))
            sys.stdout.flush()
            sys.stderr.flush()
            fileprefix = "adcTestData_{}_inputPinTest_chip{}_adcClock{}_adcOffset{}_sampleRate{}".format(startDateTime,adcSerialNumbers[iChip],clock,offset,sampleRate)
            fileprefix = os.path.join(dataDir,fileprefix)
            try:
                collect_data.dumpWaveformRootFile(iChip,fileprefix,0,0,0,0,100,adcClock=clock,adcOffset=offset,adcSerial=adcSerialNumbers[iChip],sampleRate=sampleRate)
            except Exception as e:
                isError[adcSerialNumbers[iChip]] = True
                print("Error while collecting input pin data, traceback in stderr.")
                sys.stderr.write("Error collecting input pin data for chip: {} Error: {} {}\n".format(iChip,type(e),e))
                traceback.print_tb(e.__traceback__)
            else:
                try:
                    static_fns = list(glob.glob(fileprefix+"_*.root"))
                    assert(len(static_fns)==1)
                    static_fn = static_fns[0]
                    baselineRmsStats = baseline_rms.analyze(static_fn)
                except Exception as e:
                    isError[adcSerialNumbers[iChip]] = True
                    print("Error while performing input pin tests, traceback in stderr.")
                    sys.stderr.write("Error processing input pin data for chip: {} Error: {} {}\n".format(iChip,type(e),e))
                    traceback.print_tb(e.__traceback__)
                else:
                    allStatsRaw[sampleRate][clock][offset][adcSerialNumbers[iChip]]["inputPin"] = baselineRmsStats
                    #with open(fileprefix+"_statsRaw.json","w") as f:
                    #    json.dump(baselineRmsStats,f)
    statsRawJsonFn = "adcTestData_{}_statsRaw.json".format(startDateTime)
    statsRawJsonFn = os.path.join(dataDir,statsRawJsonFn)
    with open(statsRawJsonFn,"w") as f:
        json.dump(allStatsRaw,f)
    print("Summarizing all data...")
    summary = ADC_TEST_SUMMARY(config,allStatsRaw,startDateTime,hostname,board_id,operator,sumatradict=sumatradict,isError=isError)
    summary.write_jsons(os.path.join(dataDir,"adcTest_{}".format(startDateTime)))
    print("Making summary plots...")
    sys.stdout.flush()
    sys.stderr.flush()
    for serial in summary.get_serials():
      SUMMARY_PLOTS(config,summary.get_summary(serial),
                os.path.join(dataDir,"adcTest_{}_{}".format(startDateTime,serial)),
                plotAll=True)

def main():
    from ...configuration.argument_parser import ArgumentParser
    from ...configuration import CONFIG
    import json

    ROOT.gROOT.SetBatch(True)

    timestamp = datetime.datetime.now().replace(microsecond=0).isoformat().replace(":","").replace("-","")

    parser = ArgumentParser(description="Runs ADC tests")
    parser.add_argument("-t", "--timestamp",help="Timestamp string to use for this test",type=str,default=timestamp)
    parser.add_argument("-o", "--operator",help="Test operator name",type=str,default="Command-line Operator")
    parser.add_argument("-s", "--serial",help="Chip serial number, use multiple times for multiple chips, e.g. -s 1 -s 2 -s 3 -s 4",action='append',default=[])
    parser.add_argument("-b", "--board",help="Test board serial number",default=None)
    parser.add_argument("-d", "--datadir",help="Directory for output data files",default="")
    parser.add_argument("-q", "--quick",help="Only run offset current off (normally runs all offsets)",action='store_true')
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
    quick = args.quick

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
                quick = options["quick"]
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
            cProfile.runctx('chipsPass = runTests(config,dataDir,serialNumbers,timestamp,operator,boardid,hostname,quick=quick,sumatradict=options)',globals(),locals(),args.profiler)
        else:
            chipsPass = runTests(config,dataDir,serialNumbers,timestamp,operator,boardid,hostname,quick=quick,sumatradict=options)
    except Exception as e:
        print("Uncaught exception in runTests. Traceback in stderr.")
        sys.stderr.write("Uncaught exception in runTests: Error: {} {}\n".format(type(e),e))
        traceback.print_tb(e.__traceback__)
        config.POWERSUPPLYINTER.off()
        sys.exit(1)
    else:
        config.POWERSUPPLYINTER.off()
        runTime = datetime.datetime.now() - startTime
        print("Test took: {:.0f} min {:.1f} s".format(runTime.total_seconds() // 60, runTime.total_seconds() % 60.))
        print("Chips Pass: ",chipsPass)
