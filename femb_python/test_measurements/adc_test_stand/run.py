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
import time
import datetime
import glob
from uuid import uuid1 as uuid
import json
import socket
import numpy
import matplotlib.pyplot as plt
import ROOT
from .collect_data import COLLECT_DATA 
from .calibrate_ramp import CALIBRATE_RAMP
from .static_tests import STATIC_TESTS
from .dynamic_tests import DYNAMIC_TESTS
from .baseline_rms import BASELINE_RMS
from .summary_plots import SUMMARY_PLOTS

class ADC_TEST_SUMMARY(object):

    def __init__(self,allStatsRaw,testTime,hostname,board_id):
        self.allStatsRaw = allStatsRaw
        self.testTime = testTime
        self.hostname = hostname
        self.board_id = board_id
        self.allStats = None
        self.staticSummary = None
        self.dynamicSummary = None
        self.inputPinSummary = None
        self.makeSummaries()

    def makeSummaries(self):
        """
        makes keys:
        self.staticSummary[chipSerial][clock][offset][statistic][channel]
        self.dynamicSummary[chipSerial][clock][offset][statistic][amp][freq][channel]
        self.inputPinSummary[chipSerial][clock][offset][statistic][channel]

        from:
        self.allStatsRaw[clock][offset][chipSerial]
        """
        allStatsRaw = self.allStatsRaw
        clocks = sorted(allStatsRaw.keys())
        offsets = []
        chipSerials = []
        for clock in clocks:
            offsets = sorted(allStatsRaw[clock].keys())
            for offset in offsets:
                chipSerials = sorted(allStatsRaw[clock][offset].keys())
                break
            break
        staticSummary = {}
        dynamicSummary = {}
        for chipSerial in chipSerials:
            staticSummary[chipSerial]={}
            dynamicSummary[chipSerial]={}
            for clock in clocks:
                staticSummary[chipSerial][clock]={}
                dynamicSummary[chipSerial][clock]={}
                for offset in offsets:
                    staticSummary[chipSerial][clock][offset] = self.makeStaticSummary(allStatsRaw[clock][offset][chipSerial]["static"])
                    dynamicSummary[chipSerial][clock][offset] = self.makeDynamicSummary(allStatsRaw[clock][offset][chipSerial]["dynamic"])
        self.staticSummary = staticSummary
        self.dynamicSummary = dynamicSummary

        inputPinSummary = {}
        for chipSerial in chipSerials:
            inputPinSummary[chipSerial]={}
            for clock in clocks:
                inputPinSummary[chipSerial][clock]={}
                for offset in offsets:
                    try:
                        inputPinSummary[chipSerial][clock][offset] = self.makeStaticSummary(allStatsRaw[clock][offset][chipSerial]["inputPin"])
                    except KeyError:
                        pass
                if len(inputPinSummary[chipSerial][clock]) == 0:
                    inputPinSummary[chipSerial].pop(clock)
        self.inputPinSummary = inputPinSummary

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
                "serial":serial,"time":self.testTime,
                "hostname":self.hostname,"board_id":self.board_id,
                }
        try:
            result["inputPin"] = self.inputPinSummary[serial]
        except:
            print("get_summary: no inputPin key")
            pass
        return result

    def write_jsons(self,fileprefix):
        for serial in self.staticSummary:
            filename = fileprefix + "_" + str(serial) + ".json"
            data = self.get_summary(serial)
            with open(filename,"w") as f:
                json.dump(data,f)

def runTests(config,adcSerialNumbers,username,board_id,singleConfig=True):
    """
    Runs the ADC tests for all chips on the ADC test board.

    config is the CONFIG object for the test board.
    adcSerialNumbers is a list of a serial numbers for the ADC ASICS
    username is the operator user name string
    board_id is the ID number of the test board
    singleConfig is a boolean. If True only test the ASICS with the external clock
        and no offset current. If False test both clocks and all offset current
        settings.

    returns a list of bools whether an asic passed the tests. The list
        corresponds to the input serial number list.  
    """

    collect_data = COLLECT_DATA(config,100)
    static_tests = STATIC_TESTS(config)
    dynamic_tests = DYNAMIC_TESTS(config)
    baseline_rms = BASELINE_RMS()
    startDateTime = datetime.datetime.now().replace(microsecond=0).isoformat()
    hostname = socket.gethostname() 

    clocks = [0,1] # -1 undefined, 0 external, 1 internal monostable, 2 internal FIFO
    offsets = range(-1,16)
    if singleConfig:
        clocks = [0]
        offsets = [-1]

    allStatsRaw = {}
    for clock in clocks: # -1 undefined, 0 external, 1 internal monostable, 2 internal FIFO
        allStatsRaw[clock] = {}
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
                print("Collecting data for clock: {} offset: {} chip: {} ...".format(clock, offset, iChip))
                sys.stdout.flush()
                chipStats = {}
                fileprefix = "adcTestData_{}_chip{}_adcClock{}_adcOffset{}".format(startDateTime,adcSerialNumbers[iChip],clock,offset)
                collect_data.getData(fileprefix,iChip,adcClock=clock,adcOffset=offset,adcSerial=adcSerialNumbers[iChip])
                print("Processing...")
                static_fns = list(glob.glob(fileprefix+"_functype3_*.root"))
                assert(len(static_fns)==1)
                static_fn = static_fns[0]
                CALIBRATE_RAMP(static_fn).write_calibrate_tree()
                staticStats = static_tests.analyzeLinearity(static_fn,diagnosticPlots=False)
                dynamicStats = dynamic_tests.analyze(fileprefix,diagnosticPlots=False)
                chipStats["static"] = staticStats
                chipStats["dynamic"] = dynamicStats
                configStats[adcSerialNumbers[iChip]] = chipStats
                #with open(fileprefix+"_statsRaw.json","w") as f:
                #    json.dump(chipStats,f)
            allStatsRaw[clock][offset] = configStats
    # check the input pin works
    if True:
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
            fileprefix = "adcTestData_{}_inputPinTest_chip{}_adcClock{}_adcOffset{}".format(startDateTime,adcSerialNumbers[iChip],clock,offset)
            collect_data.dumpWaveformRootFile(iChip,fileprefix,0,0,0,0,100,adcClock=clock,adcOffset=offset,adcSerial=adcSerialNumbers[iChip])
            static_fns = list(glob.glob(fileprefix+"_*.root"))
            assert(len(static_fns)==1)
            static_fn = static_fns[0]
            baselineRmsStats = baseline_rms.analyze(static_fn)
            allStatsRaw[clock][offset][adcSerialNumbers[iChip]]["inputPin"] = baselineRmsStats
            #with open(fileprefix+"_statsRaw.json","w") as f:
            #    json.dump(baselineRmsStats,f)
    with open("adcTestData_{}_statsRaw.json".format(startDateTime),"w") as f:
        json.dump(baselineRmsStats,f)
    print("Summarizing all data...")
    sys.stdout.flush()
    summary = ADC_TEST_SUMMARY(allStatsRaw,startDateTime,hostname,board_id)
    summary.write_jsons("adcTest_{}".format(startDateTime))
    print("Making summary plots...")
    for serial in summary.get_serials():
      SUMMARY_PLOTS(summary.get_summary(serial),"adcTest_{}_{}".format(startDateTime,serial),plotAll=True)
    print("Checking if chips pass..")
    sys.stdout.flush()
    chipsPass = []
    for serial in adcSerialNumbers:
        thisSummary = summary.get_summary(serial)
        thisPass = True
        for clock in thisSummary['static']:
            for offset in thisSummary['static'][clock]:
                for channel in range(len(thisSummary['static'][clock][offset]["DNLmax"])):
                    if thisSummary['static'][clock][offset]["DNLmax400"][channel] > 50.:
                        thisPass = False
                    if thisSummary['static'][clock][offset]["stuckCodeFrac400"][channel] > 0.5:
                        thisPass = False
                        break
                    if thisSummary['static'][clock][offset]["INLabsMax400"][channel] > 50.:
                        thisPass = False
                        break
                    if thisSummary['static'][clock][offset]["minCode"][channel] > 300.:
                        thisPass = False
                        break
                if not thisPass:
                    break
            if not thisPass:
                break
        chipsPass.append(thisPass)
    return chipsPass

def main():
    from ...configuration.argument_parser import ArgumentParser
    from ...configuration import CONFIG
    ROOT.gROOT.SetBatch(True)
    parser = ArgumentParser(description="Runs ADC tests")
    parser.add_argument("-s", "--singleConfig",help="Only run a single configuration (normally runs all clocks and offsets)",action='store_true')
    parser.add_argument("-p", "--profiler",help="Enable python timing profiler and save to given file name",type=str,default=None)
    args = parser.parse_args()
  
    config = CONFIG()
    serialNumbers = list(range(-1,-(config.NASICS+1),-1))
    chipsPass = None
    startTime = datetime.datetime.now()
    if args.profiler:
        import cProfile
        cProfile.runctx('chipsPass = runTests(config,serialNumbers,"Command-line user",None,singleConfig=args.singleConfig)',globals(),locals(),args.profiler)
    else:
        chipsPass = runTests(config,serialNumbers,"Command-line user",None,singleConfig=args.singleConfig)
    runTime = datetime.datetime.now() - startTime
    print("Test took: {:.0f} min {:.1f} s".format(runTime.total_seconds() // 60, runTime.total_seconds() % 60.))
    print("Chips Pass: ",chipsPass)
