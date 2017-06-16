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
from .summary_plots import SUMMARY_PLOTS

class ADC_TEST_SUMMARY(object):

    def __init__(self,allStatsRaw,testTime,hostname,board_id,operator,sumatradict=None,isError=None):
        self.allStatsRaw = allStatsRaw
        self.testTime = testTime
        self.hostname = hostname
        self.board_id = board_id
        self.operator = operator
        self.sumatradict = sumatradict
        self.isError = isError
        self.allStats = None
        self.staticSummary = None
        self.dynamicSummary = None
        self.inputPinSummary = None
        self.dcSummary = None
        self.testResults = None
        self.makeSummaries()
        self.checkPass()

    def makeSummaries(self):
        """
        makes keys:
        self.staticSummary[chipSerial][sampleRate][clock][offset][statistic][channel]
        self.dynamicSummary[chipSerial][sampleRate][clock][offset][statistic][amp][freq][channel]
        self.inputPinSummary[chipSerial][sampleRate][clock][offset][statistic][channel]
        self.dcSummary[chipSerial][sampleRate][clock][offset][statistic][channel]

        from:
        self.allStatsRaw[sampleRate][clock][offset][chipSerial]
        """
        print("Summarizing all data...")
        sys.stdout.flush()
        sys.stderr.flush()
        allStatsRaw = self.allStatsRaw
        sampleRates = sorted(allStatsRaw.keys())
        offsets = []
        chipSerials = []
        for sampleRate in sampleRates:
            clocks = sorted(allStatsRaw[sampleRate].keys())
            for clock in clocks:
                offsets = sorted(allStatsRaw[sampleRate][clock].keys())
                for offset in offsets:
                    chipSerials = sorted(allStatsRaw[sampleRate][clock][offset].keys())
                    break
                break
        staticSummary = {}
        dynamicSummary = {}
        for chipSerial in chipSerials:
            staticSummary[chipSerial]={}
            dynamicSummary[chipSerial]={}
            for sampleRate in sampleRates:
                staticSummary[chipSerial][sampleRate]={}
                dynamicSummary[chipSerial][sampleRate]={}
                for clock in clocks:
                    staticSummary[chipSerial][sampleRate][clock]={}
                    dynamicSummary[chipSerial][sampleRate][clock]={}
                    for offset in offsets:
                        staticSummary[chipSerial][sampleRate][clock][offset] = self.makeStaticSummary(allStatsRaw[sampleRate][clock][offset][chipSerial]["static"])
                        dynamicSummary[chipSerial][sampleRate][clock][offset] = self.makeDynamicSummary(allStatsRaw[sampleRate][clock][offset][chipSerial]["dynamic"])
        self.staticSummary = staticSummary
        self.dynamicSummary = dynamicSummary

        inputPinSummary = {}
        for chipSerial in chipSerials:
            inputPinSummary[chipSerial]={}
            for sampleRate in sampleRates:
                inputPinSummary[chipSerial][sampleRate]={}
                for clock in clocks:
                    inputPinSummary[chipSerial][sampleRate][clock]={}
                    for offset in offsets:
                        try:
                            inputPinSummary[chipSerial][sampleRate][clock][offset] = self.makeStaticSummary(allStatsRaw[sampleRate][clock][offset][chipSerial]["inputPin"])
                        except KeyError:
                            pass
                    if len(inputPinSummary[chipSerial][sampleRate][clock]) == 0:
                        inputPinSummary[chipSerial][sampleRate].pop(clock)
                if len(inputPinSummary[chipSerial][sampleRate]) == 0:
                    inputPinSummary[chipSerial].pop(sampleRate)
            if len(inputPinSummary[chipSerial]) == 0:
                inputPinSummary.pop(chipSerial)
        self.inputPinSummary = inputPinSummary

        dcSummary = {}
        for chipSerial in chipSerials:
            dcSummary[chipSerial]={}
            for sampleRate in sampleRates:
                dcSummary[chipSerial][sampleRate]={}
                for clock in clocks:
                    dcSummary[chipSerial][sampleRate][clock]={}
                    for offset in offsets:
                    #    try:
                            dcSummary[chipSerial][sampleRate][clock][offset] = self.makeStaticSummary(allStatsRaw[sampleRate][clock][offset][chipSerial]["dc"])
                    #    except KeyError:
                    #        pass
                    #if len(dcSummary[chipSerial][clock]) == 0:
                    #    dcSummary[chipSerial].pop(clock)
        self.dcSummary = dcSummary

    def makeStaticSummary(self,stats):
        """
        returns:
        result[statistic][channel]

        from:
        stats[channel][statistic]
        """
        statNames = stats[0].keys()
        result = {}
        for statName in statNames:
            result[statName] = []
            for iChan in range(16):
                result[statName].append(stats[iChan][statName])
        return result

    def makeDynamicSummary(self,stats):
        """
        returns:
        result[statistic][amp][freq][channel]

        from:
        stats[channel][amp][freq][statistic]
        """
        amps = stats[0].keys()
        freqs = None
        statNames = None
        for amp in amps:
            freqs = stats[0][amp].keys()
            for freq in freqs:
                statNames = stats[0][amp][freq].keys()
                break
            break
        result = {}
        for statName in statNames:
            result[statName] = {}
            for amp in amps:
                result[statName][amp] = {}
                for freq in freqs:
                    result[statName][amp][freq] = []
                    for iChan in range(16):
                        result[statName][amp][freq].append(stats[iChan][amp][freq][statName])
        return result

    def get_serials(self):
        return self.staticSummary.keys()

    def get_summary(self,serial):
        result =  {"static":self.staticSummary[serial],
                "dynamic":self.dynamicSummary[serial],
                "dc":self.dcSummary[serial],
                "serial":serial,"timestamp":self.testTime,
                "hostname":self.hostname,"board_id":self.board_id,
                "operator":self.operator,
                "sumatra": self.sumatradict,
                }
        if self.isError is None:
            result["error"] = None,
        else:
            result["error"] = self.isError[serial]
        try:
            result["inputPin"] = self.inputPinSummary[serial]
        except:
            print("Error get_summary: no inputPin key")
            pass
        try:
            result["testResults"] = self.testResults[serial]
        except:
            pass
        return result

    def write_jsons(self,fileprefix):
        for serial in self.staticSummary:
            filename = fileprefix + "_" + str(serial) + ".json"
            data = self.get_summary(serial)
            with open(filename,"w") as f:
                json.dump(data,f)

    def checkPass(self):
        print("Checking if chip passes tests...")
        sys.stdout.flush()
        sys.stderr.flush()
        self.testResults = {}
        for serial in self.get_serials():
            thisSummary = self.get_summary(serial)
            thisPass = True
            results = {}
            staticChecks = {
                'DNLmax400': ["lt",28.,{}],
                'DNL75perc400': ["lt",0.48,{}],
                'stuckCodeFrac400': ["lt",0.1,{}],
                'INLabsMax400': ["lt",60.,{"offset":-1}],
                'INLabs75perc400': ["lt",50.,{"offset":-1}],
                'minCode': ["lt",240.,{"offset":-1}],
                'minCodeV': ["lt",0.2,{"offset":-1}],
                'maxCode': ["gt",4090.,{"offset":-1}],
                'maxCodeV': ["gt",1.3,{"offset":-1}],
            }
            dynamicChecks = {
                'sinads': ["gt",25.,{"offset":-1,"clock":0}],
            }
            inputPinChecks = {
                #'mean': ["lt",3000.,{}],
            }
            dcChecks = {
                "meanCodeFor0.2V": ["lt",800,{"offset":-1}],
                "meanCodeFor1.6V": ["gt",3500,{"offset":-1}],
            }
            for stat in staticChecks:
                check = staticChecks[stat]
                statPass = True
                for sampleRate in thisSummary['static']:
                    for clock in thisSummary['static'][sampleRate]:
                        try:
                            if check[2]["clock"] != int(clock):
                                continue
                        except KeyError:
                            pass
                        for offset in thisSummary['static'][sampleRate][clock]:
                            try:
                                if check[2]["offset"] != int(offset):
                                    continue
                            except KeyError:
                                pass
                            for channel in range(16):
                                if check[0] == "lt":
                                    if thisSummary['static'][sampleRate][clock][offset][stat][channel] >= check[1]:
                                        statPass = False
                                        thisPass = False
                                        break
                                if check[0] == "gt":
                                    if thisSummary['static'][sampleRate][clock][offset][stat][channel] <= check[1]:
                                        statPass = False
                                        thisPass = False
                                        break
                            if not statPass:
                                break
                        if not statPass:
                            break
                    if not statPass:
                        break
                results[stat] = statPass
            for stat in dynamicChecks:
                check = dynamicChecks[stat]
                statPass = True
                for sampleRate in thisSummary['dynamic']:
                    for clock in thisSummary['dynamic'][sampleRate]:
                        try:
                            if check[2]["clock"] != int(clock):
                                continue
                        except KeyError:
                            pass
                        for offset in thisSummary['dynamic'][sampleRate][clock]:
                            try:
                                if check[2]["offset"] != int(offset):
                                    continue
                            except KeyError:
                                pass
                            for amp in thisSummary['dynamic'][sampleRate][clock][offset][stat]:
                                for freq in thisSummary['dynamic'][sampleRate][clock][offset][stat][amp]:
                                    for channel in range(16):
                                        if check[0] == "lt":
                                            if thisSummary['dynamic'][sampleRate][clock][offset][stat][amp][freq][channel] >= check[1]:
                                                statPass = False
                                                thisPass = False
                                                break
                                        if check[0] == "gt":
                                            if thisSummary['dynamic'][sampleRate][clock][offset][stat][amp][freq][channel] <= check[1]:
                                                statPass = False
                                                thisPass = False
                                                break
                                    if not statPass:
                                        break
                                if not statPass:
                                    break
                            if not statPass:
                                break
                        if not statPass:
                            break
                    if not statPass:
                        break
                results[stat] = statPass
            for stat in inputPinChecks:
                check = inputPinChecks[stat]
                statPass = True
                for sampleRate in thisSummary['inputPin']:
                    for clock in thisSummary['inputPin'][sampleRate]:
                        try:
                            if check[2]["clock"] != int(clock):
                                continue
                        except KeyError:
                            pass
                        for offset in thisSummary['inputPin'][sampleRate][clock]:
                            try:
                                if check[2]["offset"] != int(offset):
                                    continue
                            except KeyError:
                                pass
                            for channel in range(16):
                                if check[0] == "lt":
                                    if thisSummary['inputPin'][sampleRate][clock][offset][stat][channel] >= check[1]:
                                        statPass = False
                                        thisPass = False
                                        break
                                if check[0] == "gt":
                                    if thisSummary['inputPin'][sampleRate][clock][offset][stat][channel] <= check[1]:
                                        statPass = False
                                        thisPass = False
                                        break
                            if not statPass:
                                break
                        if not statPass:
                            break
                    if not statPass:
                        break
                results["inputPin_"+stat] = statPass
            for stat in dcChecks:
                check = dcChecks[stat]
                statPass = True
                for sampleRate in thisSummary['dc']:
                    for clock in thisSummary['dc'][sampleRate]:
                        try:
                            if check[2]["clock"] != int(clock):
                                continue
                        except KeyError:
                            pass
                        for offset in thisSummary['dc'][sampleRate][clock]:
                            try:
                                if check[2]["offset"] != int(offset):
                                    continue
                            except KeyError:
                                pass
                            for channel in range(16):
                                if check[0] == "lt":
                                    if thisSummary['dc'][sampleRate][clock][offset][stat][channel] >= check[1]:
                                        statPass = False
                                        thisPass = False
                                        break
                                if check[0] == "gt":
                                    if thisSummary['dc'][sampleRate][clock][offset][stat][channel] <= check[1]:
                                        statPass = False
                                        thisPass = False
                                        break
                            if not statPass:
                                break
                        if not statPass:
                            break
                    if not statPass:
                        break
                results[stat] = statPass
            results["noErrors"] = not self.isError[serial]
            thisPass = thisPass and results["noErrors"]
            results["pass"] = thisPass
            self.testResults[serial] = results

def runTests(config,dataDir,adcSerialNumbers,startDateTime,operator,board_id,hostname,singleConfig=True,timestamp=None,sumatradict=None):
    """
    Runs the ADC tests for all chips on the ADC test board.

    config is the CONFIG object for the test board.
    dataDir  is the output directory for data files
    adcSerialNumbers is a list of a serial numbers for the ADC ASICS
    startDateTime string identifying the time the tests are started
    operator is the operator user name string
    board_id is the ID number of the test board
    hostname is the current computer name
    singleConfig is a boolean. If True only test the ASICS with the external clock
        and no offset current. If False test both clocks and all offset current
        settings.
    sumatradict is a dictionary of options that will be written to the summary json

    returns a list of bools whether an asic passed the tests. The list
        corresponds to the input serial number list.  
    """

    collect_data = COLLECT_DATA(config,100)
    static_tests = STATIC_TESTS(config)
    dynamic_tests = DYNAMIC_TESTS(config)
    baseline_rms = BASELINE_RMS()
    dc_tests = DC_TESTS(config)

    sampleRates = [2000000,1000000]
    clocks = [0,1] # -1 undefined, 0 external, 1 internal monostable, 2 internal FIFO
    offsets = range(-1,16)
    if singleConfig:
        clocks = [0]
        offsets = [-1]

    allStatsRaw = {}
    isError = {}
    for adcSerialNumber in adcSerialNumbers:
        isError[adcSerialNumber] = False
    for sampleRate in sampleRates:
        if sampleRate == 2000000:
            if hasattr(config,"FIRMWAREPATH2MHZ"):
                try:
                    config.programFirmware2Mhz()
                except CalledProcessError as e:
                    print("Error: firmware programming failed, exiting.")
                    sys.exit(1)
                config.resetBoard()
                config.initBoard()
                config.syncADC()
        elif sampleRate == 1000000:
            if not hasattr(config,"FIRMWAREPATH1MHZ"):
                print("No 1 MHz firmware path configured, skipping.")
                continue
            try:
                config.programFirmware1Mhz()
            except CalledProcessError as e:
                print("Error: firmware programming failed, exiting.")
                sys.exit(1)
            config.resetBoard()
            config.initBoard()
            config.syncADC()
        else:
            print("Error: Sample rate not 1 MHz or 2 MHz, exiting.")
            sys.exit(1)
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
                if offset <=0:
                    config.configAdcAsic(enableOffsetCurrent=0,offsetCurrent=0,
                                        clockMonostable=clockMonostable,clockFromFIFO=clockFromFIFO,
                                        clockExternal=clockExternal)
                else:
                    config.configAdcAsic(enableOffsetCurrent=1,offsetCurrent=offset,
                                        clockMonostable=clockMonostable,clockFromFIFO=clockFromFIFO,
                                        clockExternal=clockExternal)
                for iChip in range(config.NASICS):
                    print("Collecting data for sample rate: {} clock: {} offset: {} chip: {} ...".format(sampleRate, clock, offset, iChip))
                    sys.stdout.flush()
                    sys.stderr.flush()
                    chipStats = {}
                    fileprefix = "adcTestData_{}_chip{}_adcClock{}_adcOffset{}_sampleRate{}".format(startDateTime,adcSerialNumbers[iChip],clock,offset,sampleRate)
                    fileprefix = os.path.join(dataDir,fileprefix)
                    try:
                        collect_data.getData(fileprefix,iChip,adcClock=clock,adcOffset=offset,adcSerial=adcSerialNumbers[iChip],sampleRate=sampleRate)
                    except Exception as e:
                        isError[adcSerialNumbers[iChip]] = True
                        print("Error while collecting data, traceback in stderr.")
                        sys.stderr.write("Error collecting data for sample rate: {} clock: {} offset: {} chip: {} Error: {} {}\n".format(sampleRate, clock, offset, iChip,type(e),e))
                        traceback.print_tb(e.__traceback__)
                        continue
                    print("Processing...")
                    static_fns = list(glob.glob(fileprefix+"_functype3_*.root"))
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
    if True:
        sampleRate = 2000000
        clock=0
        offset = -1
        clockMonostable=False
        clockFromFIFO=False
        clockExternal=True
        config.configAdcAsic(enableOffsetCurrent=0,offsetCurrent=0,
                            clockMonostable=clockMonostable,clockFromFIFO=clockFromFIFO,
                            clockExternal=clockExternal,testInput=0)
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
    summary = ADC_TEST_SUMMARY(allStatsRaw,startDateTime,hostname,board_id,operator,sumatradict=sumatradict,isError=isError)
    summary.write_jsons(os.path.join(dataDir,"adcTest_{}".format(startDateTime)))
    print("Making summary plots...")
    sys.stdout.flush()
    sys.stderr.flush()
    for serial in summary.get_serials():
      SUMMARY_PLOTS(summary.get_summary(serial),
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
    parser.add_argument("-q", "--quick",help="Only run a single configuration (normally runs all clocks and offsets)",action='store_true')
    parser.add_argument("-p", "--profiler",help="Enable python timing profiler and save to given file name",type=str,default=None)
    parser.add_argument("-j", "--jsonfile",help="json options file location",default=None)
    args = parser.parse_args()
  
    config = CONFIG()
    chipsPass = None
    startTime = datetime.datetime.now()

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
        if args.profiler:
            import cProfile
            cProfile.runctx('chipsPass = runTests(config,dataDir,serialNumbers,timestamp,operator,boardid,hostname,singleConfig=args.quick,sumatradict=options)',globals(),locals(),args.profiler)
        else:
            chipsPass = runTests(config,dataDir,serialNumbers,timestamp,operator,boardid,hostname,singleConfig=args.quick,sumatradict=options)
    except Exception as e:
        print("Uncaught exception in runTests. Traceback in stderr.")
        sys.stderr.write("Uncaught exception in runTests: Error: {} {}\n".format(type(e),e))
        traceback.print_tb(e.__traceback__)
        sys.exit(1)
    else:
        runTime = datetime.datetime.now() - startTime
        print("Test took: {:.0f} min {:.1f} s".format(runTime.total_seconds() // 60, runTime.total_seconds() % 60.))
        print("Chips Pass: ",chipsPass)
