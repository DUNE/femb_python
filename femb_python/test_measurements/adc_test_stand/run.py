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
import time
import datetime
import glob
from uuid import uuid1 as uuid
import json
import numpy
import matplotlib.pyplot as plt
import ROOT
from .collect_data import COLLECT_DATA 
from .static_tests import STATIC_TESTS
from .dynamic_tests import DYNAMIC_TESTS
from .summary_plots import SUMMARY_PLOTS

class ADC_TEST_SUMMARY(object):

    def __init__(self,allStatsRaw,testTime):
        self.allStatsRaw = allStatsRaw
        self.testTime = testTime
        self.allStats = None
        self.makeSummaries()

    def makeSummaries(self):
        """
        makes keys:
        self.staticSummary[chipSerial][clock][offset][statistic][channel]

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
        for chipSerial in chipSerials:
            staticSummary[chipSerial]={}
            for clock in clocks:
                staticSummary[chipSerial][clock]={}
                for offset in offsets:
                    staticSummary[chipSerial][clock][offset] = self.makeStaticSummary(allStatsRaw[clock][offset][chipSerial]["static"])
        self.staticSummary = staticSummary

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

    def get_serials(self):
        return self.staticSummary.keys()

    def get_summary(self,serial):
        return {"static":self.staticSummary[serial],"serial":serial,"time":self.testTime}

    def write_jsons(self,fileprefix):
        for serial in self.staticSummary:
            filename = fileprefix + "_" + str(serial) + ".json"
            data = self.get_summary(serial)
            with open(filename,"w") as f:
                json.dump(data,f)

def runTests(config,adcSerialNumbers,username,singleConfig=True):
    """
    adcCodes is a list of a serial numbers for the ADCs
    username is the operator user name
    """

    collect_data = COLLECT_DATA(config,100)
    static_tests = STATIC_TESTS(config)
    dynamic_tests = DYNAMIC_TESTS(config)
    startDateTime = datetime.datetime.now().replace(microsecond=0).isoformat()

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
                chipStats = {}
                fileprefix = "adcTestData_{}_chip{}_adcClock{}_adcOffset{}".format(startDateTime,adcSerialNumbers[iChip],clock,offset)
                collect_data.getData(fileprefix,iChip,adcClock=clock,adcOffset=offset,adcSerial=adcSerialNumbers[iChip])
                static_fns = list(glob.glob(fileprefix+"_functype3_*.root"))
                assert(len(static_fns)==1)
                static_fn = static_fns[0]
                staticStats = static_tests.analyzeLinearity(static_fn,diagnosticPlots=False)
                dynamicStats = dynamic_tests.analyze(fileprefix,diagnosticPlots=False)
                chipStats["static"] = staticStats
                chipStats["dynamic"] = dynamicStats
                configStats[adcSerialNumbers[iChip]] = chipStats
            allStatsRaw[clock][offset] = configStats
    summary = ADC_TEST_SUMMARY(allStatsRaw,startDateTime)
    summary.write_jsons("adcTest_{}".format(startDateTime))
    for serial in summary.get_serials():
      SUMMARY_PLOTS(summary.get_summary(serial),"adcTest_{}_{}".format(startDateTime,serial),plotAll=True)
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
    args = parser.parse_args()
  
    config = CONFIG()
    serialNumbers = list(range(-1,-(config.NASICS+1),-1))
    chipsPass = runTests(config,serialNumbers,"Command-line user",singleConfig=args.singleConfig)
    print("Chips Pass: ",chipsPass)
