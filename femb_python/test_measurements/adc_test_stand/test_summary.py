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
from types import MappingProxyType
import numpy
import matplotlib.pyplot as plt
import ROOT

class ADC_TEST_SUMMARY(object):

    # Don't use _checks!!! Use checks
    _checks = {}
    _checks["warm"] = {
        'static' : {
            'DNLmax400': ["lt",28.,{}],
            'DNL75perc400': ["lt",0.48,{}],
            'stuckCodeFrac400': ["lt",0.1,{}],
            'INLabsMax400': ["lt",60.,{"offset":-1}],
            'INLabs75perc400': ["lt",50.,{"offset":-1}],
            'minCode': ["lt",240.,{"offset":-1}],
            'minCodeV': ["lt",0.2,{"offset":-1}],
            'maxCode': ["gt",4090.,{"offset":-1}],
            'maxCodeV': ["gt",1.3,{"offset":-1}],
        },
        'dynamic' : {
            'sinads': ["gt",25.,{"offset":-1,"clock":0}],
        },
        'inputPin' : {
            #'mean': ["lt",3000.,{}],
        },
        'dc' : {
            "meanCodeFor0.2V": ["lt",800,{"offset":-1}],
            "meanCodeFor1.6V": ["gt",3500,{"offset":-1}],
        },
    }
    _checks["cold"] = {
        'static' : {
            'DNLmax400': ["lt",28.,{}],
            'DNL75perc400': ["lt",0.48,{}],
            'stuckCodeFrac400': ["lt",0.1,{}],
            'INLabsMax400': ["lt",60.,{"offset":-1}],
            'INLabs75perc400': ["lt",50.,{"offset":-1}],
            'minCode': ["lt",240.,{"offset":-1}],
            'minCodeV': ["lt",0.2,{"offset":-1}],
            'maxCode': ["gt",4090.,{"offset":-1}],
            'maxCodeV': ["gt",1.3,{"offset":-1}],
        },
        'dynamic' : {
            'sinads': ["gt",25.,{"offset":-1,"clock":0}],
        },
        'inputPin' : {
            #'mean': ["lt",3000.,{}],
        },
        'dc' : {
            "meanCodeFor0.2V": ["lt",800,{"offset":-1}],
            "meanCodeFor1.6V": ["gt",3500,{"offset":-1}],
        },
    }

    # checks is read-only, which is how we want something
    # shared by all instances of the class to be
    checks = MappingProxyType(_checks)

    def __init__(self,config,allStatsRaw,testTime,hostname,board_id,operator,sumatradict=None,isError=None):
        self.config = config
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
                        try:
                            staticSummary[chipSerial][sampleRate][clock][offset] = self.makeStaticSummary(allStatsRaw[sampleRate][clock][offset][chipSerial]["static"])
                        except KeyError:
                            pass
                        try:
                            dynamicSummary[chipSerial][sampleRate][clock][offset] = self.makeDynamicSummary(allStatsRaw[sampleRate][clock][offset][chipSerial]["dynamic"])
                        except KeyError:
                            pass
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
        statNames = None
        chfunc = int
        try:
            statNames = stats[chfunc(0)].keys()
        except KeyError:
            chfunc = str
            statNames = stats[chfunc(0)].keys()
        result = {}
        for statName in statNames:
            result[statName] = []
            for iChan in range(16):
                result[statName].append(stats[chfunc(iChan)][statName])
        return result

    def makeDynamicSummary(self,stats):
        """
        returns:
        result[statistic][amp][freq][channel]

        from:
        stats[channel][amp][freq][statistic]
        """
        amps = None
        chfunc = int
        try:
            amps = stats[chfunc(0)].keys()
        except KeyError:
            chfunc = str
            amps = stats[chfunc(0)].keys()
        freqs = None
        statNames = None
        for amp in amps:
            freqs = stats[chfunc(0)][amp].keys()
            for freq in freqs:
                statNames = stats[chfunc(0)][amp][freq].keys()
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
                        result[statName][amp][freq].append(stats[chfunc(iChan)][amp][freq][statName])
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

    def checkPass(self,verbose=False):
        sys.stdout.flush()
        sys.stderr.flush()
        self.testResults = {}
        checks = self.checks["warm"]
        if self.config.COLD:
            checks = self.checks["cold"]
        for serial in self.get_serials():
            thisSummary = self.get_summary(serial)
            thisPass = True
            results = {}
            for stat in checks['static']:
                check = checks['static'][stat]
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
            for stat in checks['dynamic']:
                check = checks['dynamic'][stat]
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
            for stat in checks['inputPin']:
                check = checks['inputPin'][stat]
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
            for stat in checks['dc']:
                check = checks['dc'][stat]
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
            if not (self.isError is None):
                results["noErrors"] = not self.isError[serial]
                thisPass = thisPass and results["noErrors"]
            if verbose:
                allStats = sorted(list(results.keys()))
                allPasses = [results[x] for x in allStats]
                titleStr = "{:10} {:5}".format("Chip #","Pass")
                testsStr = "{:10} {:<5}".format(serial,thisPass)
                for stat in allStats:
                    nameLen = len(stat)
                    titleStr += (" {:"+str(nameLen)+"}")
                    testsStr += (" {:<"+str(nameLen)+"}")
                titleStr = titleStr.format(*allStats)
                testsStr = testsStr.format(*allPasses)
                print(titleStr)
                print(testsStr)
            results["pass"] = thisPass
            self.testResults[serial] = results

def main():
    from ...configuration.argument_parser import ArgumentParser
    from ...configuration import CONFIG
    import json

    parser = ArgumentParser(description="Summarizes ADC Tests")
    parser.add_argument("jsonfile",help="json raw summary file location")
    parser.add_argument("-t","--testOnly",help="Down output a json file, only run the test",action="store_true")
    args = parser.parse_args()

    config = CONFIG()

    outdir, outprefix = os.path.split(args.jsonfile)
    outprefix = "ADC_Summary_"+os.path.splitext(outprefix)[0]
    outprefix = os.path.join(outdir,outprefix)
  
    data = None
    with open(args.jsonfile) as jsonfile:
        data = json.load(jsonfile)

    summary = ADC_TEST_SUMMARY(config,data,None,None,None,None)
    if not args.testOnly:
        summary.write_jsons(outprefix)
    summary.checkPass(verbose=True)
