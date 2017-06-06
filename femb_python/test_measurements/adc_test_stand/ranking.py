"""
Code for ranking ADCs. More generally analyzing multiple summary json files
produced in ADC tests.
"""

from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals
from __future__ import absolute_import
from builtins import range
from future import standard_library
standard_library.install_aliases()
import os
import os.path
import time
import datetime
import glob
from uuid import uuid1 as uuid
import json
import numpy
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.lines as mlines
from matplotlib.figure import Figure

class RANKING(object):

    def __init__(self,inglobstrs):
        """
        inglobstr is a string that can be parsed by glob to make a list of
        directories containing json files or json files to be analyzed.
        Directories found in the glob will be walked to find subdirectories 
        containing json files.
        """
        jsonpaths = []
        for inglobstr in inglobstrs:
            inpathlist = glob.glob(inglobstr)
            for inpath in inpathlist:
                for directory, subdirs, filenames in os.walk(inpath):
                    for filename in filenames:
                        if os.path.splitext(filename)[1] == ".json" and "adcTest" == filename[:7] and not ("Raw" in filename):
                            jsonpath = os.path.join(directory,filename)
                            jsonpaths.append(jsonpath)
                            print(jsonpath)
        datadicts = []
        for jsonpath in jsonpaths:
            with open(jsonpath) as jsonfile:
                datadict = json.load(jsonfile)
                datadicts.append(datadict)
        self.datadicts = datadicts

        # 0 for min 1 for max
        self.statsToDraw = {
            "DNL 75%": {"stat":"DNL75perc400"},
            "DNL Max": {"stat":"DNLmax400"},
            "INL 75%": {"stat":"INLabs75perc400"},
            "INL Max": {"stat":"INLabsMax400"},
            "Min Code": {"stat":"minCode","offsets":["-1"]},
            "Min Code V": {"stat":"minCodeV","offsets":["-1"]},
            "Max Code": {"stat":"maxCode","min":True,"offsets":["-1"]},
            "Max Code V": {"stat":"maxCodeV","min":True,"offsets":["-1"]},
            "Input Pin Mean": {"stat":"mean"},
            "Code for 0.2 V": {"stat":"meanCodeFor0.2V","offsets":["-1"]},
            "Code for 1.6 V": {"stat":"meanCodeFor1.6V","min":True,"offsets":["-1"]},
            "SINAD for 62 kHz": {"stat":"sinads","min":True,"freqs":["62365.0"],"offsets":["-1"]},
            "SINAD for 951 kHz": {"stat":"sinads","min":True,"freqs":["951512.5"],"offsets":["-1"]},
            "Stuck Code Fraction": {"stat":"stuckCodeFrac400"},
        }
        for stat in self.statsToDraw:
            self.statsToDraw[stat]["clocks"] = ["0"]

    def rank(self):
        datadicts = self.getlatestdata()
        minMaxDicts = {}
        statNames = set()
        for datadict in datadicts:
            asic_stats = {}
            serial = datadict["serial"]
            print(serial)
            static = datadict["static"]
            asic_stats.update(self.getstats(static))
            dynamic = datadict["dynamic"]
            asic_stats.update(self.getstats(dynamic,True))
            try:
                inputPin = datadict["inputPin"]
            except KeyError:
                print("Warning: now input pin stats for chip",serial)
            else:
                asic_stats.update(self.getstats(inputPin))
            try:
                dc = datadict["dc"]
            except KeyError:
                print("Warning: now input pin stats for chip",serial)
            else:
                asic_stats.update(self.getstats(dc))
            minMaxDicts[serial] = asic_stats
            for stat in asic_stats:
                statNames.add(stat)
        statNames = sorted(list(statNames))
        print("AllStatNames:")
        print(sorted(statNames))
        maxVals = {}
        minVals = {}
        for statName in statNames:
            minVals[statName] = []
            maxVals[statName] = []
            for serial in minMaxDicts:
                try:
                    minVals[statName].append(minMaxDicts[serial][statName][0])
                    maxVals[statName].append(minMaxDicts[serial][statName][1])
                except KeyError as e:
                    print("Warning KeyError for asic: ",serial," stat: ",statName," error: ",e)
                    pass
        statNamesToDraw = sorted(self.statsToDraw)
        nStats = len(statNamesToDraw)
        print("statNamesToDraw:")
        print(statNamesToDraw)
        nx = 4
        ny = 4
        nPerFig = nx*ny
        for iFig in range(int(numpy.ceil(nStats/nPerFig))):
            fig, axes2D = plt.subplots(4,4,figsize=(12,12))
            #fig.subplots_adjust(left=0.07,right=0.93,bottom=0.05,top=0.95,wspace=0.25)
            axes = [y for x in axes2D for y in x]
            for iAx, ax in enumerate(axes):
                try:
                    statName = statNamesToDraw[iFig*nPerFig+iAx]
                except IndexError:
                    ax.axis("off")
                    continue
                else:
                    ax.set_ylabel("ASICs / bin")
                    try:
                        doMin = False
                        try:
                            doMin = self.statsToDraw[statName]["min"]
                        except KeyError:
                            pass
                        if doMin: #min
                            ax.hist(minVals[statName],histtype="step")
                            ax.set_xlabel("min({})".format(statName))
                        else: #max
                            ax.hist(maxVals[statName],histtype="step")
                            ax.set_xlabel("max({})".format(statName))
                    except KeyError as e:
                        print("Warning: Could not find stat to draw",e)
                    self.set_xticks(ax)
                    ax.set_ylim(0,ax.get_ylim()[1]*1.2)
            plt.tight_layout()
            fig.savefig("ADC_ranking_page{}.png".format(iFig))
            fig.savefig("ADC_ranking_page{}.pdf".format(iFig))

    def histAllChannels(self):
        datadicts = self.getlatestdata()
        asicStatsDicts = {}
        statNames = set()
        for datadict in datadicts:
            asic_stats = {}
            serial = datadict["serial"]
            print(serial)
            static = datadict["static"]
            asic_stats.update(self.getstats(static,getAll=True))
            dynamic = datadict["dynamic"]
            asic_stats.update(self.getstats(dynamic,dynamic=True,getAll=True))
            try:
                inputPin = datadict["inputPin"]
            except KeyError:
                print("Warning: now input pin stats for chip",serial)
            else:
                asic_stats.update(self.getstats(inputPin,getAll=True))
            try:
                dc = datadict["dc"]
            except KeyError:
                print("Warning: now input pin stats for chip",serial)
            else:
                asic_stats.update(self.getstats(dc,getAll=True))
            asicStatsDicts[serial] = asic_stats
            for stat in asic_stats:
                statNames.add(stat)
        statNames = sorted(list(statNames))
        print("AllStatNames:")
        print(sorted(statNames))
        allVals = {}
        for statName in statNames:
            allVals[statName] = []
            for serial in asicStatsDicts:
                try:
                    allVals[statName].extend(asicStatsDicts[serial][statName])
                except KeyError as e:
                    print("Warning KeyError for asic: ",serial," stat: ",statName," error: ",e)
                    pass
        statNamesToDraw = sorted(self.statsToDraw)
        nStats = len(statNamesToDraw)
        print("statNamesToDraw:")
        print(statNamesToDraw)
        nx = 4
        ny = 4
        nPerFig = nx*ny
        for iFig in range(int(numpy.ceil(nStats/nPerFig))):
            fig, axes2D = plt.subplots(4,4,figsize=(12,12))
            #fig.subplots_adjust(left=0.07,right=0.93,bottom=0.05,top=0.95,wspace=0.25)
            axes = [y for x in axes2D for y in x]
            for iAx, ax in enumerate(axes):
                try:
                    statName = statNamesToDraw[iFig*nPerFig+iAx]
                except IndexError:
                    ax.axis("off")
                    continue
                else:
                    ax.set_ylabel("ASICs / bin")
                    try:
                        ax.hist(allVals[statName],histtype="step")
                        ax.set_xlabel("{}".format(statName))
                    except KeyError as e:
                        print("Warning: Could not find stat to draw",e)
                    self.set_xticks(ax)
                    ax.set_ylim(0,ax.get_ylim()[1]*1.2)
            plt.tight_layout()
            fig.savefig("ADC_chanHist_page{}.png".format(iFig))
            fig.savefig("ADC_chanHist_page{}.pdf".format(iFig))

    def set_xticks(self,ax):
        xlim = ax.get_xlim()
        xticks = numpy.linspace(xlim[0],xlim[1],4)
        xticklabels = ["{:.1g}".format(x) for x in xticks]
        ax.set_xticks(xticks)

    def getstats(self,data,dynamic=False,getAll=False):
        statsToDraw = self.statsToDraw
        result = {}
        stats = []
        clocks = sorted(data.keys())
        #clocks = clocks[:1]
        offsets = []
        amps = []
        freqs = []
        for clock in clocks:
            offsets = sorted(data[clock])
            for offset in offsets:
                stats = sorted(data[clock][offset])
                if dynamic:
                    for stat in stats: 
                        amps = data[clock][offset][stat]
                        for amp in amps:
                            freqs = data[clock][offset][stat][amp]
                            print(freqs)
                    break
                break
            break
        for statToDraw in statsToDraw:
            stat = None
            for s in stats:
                if s == statsToDraw[statToDraw]["stat"]:
                    stat = s
                    break
            if stat is None:
                continue
            minVal = 1e20
            maxVal = -1e20
            thisClocks = clocks
            thisOffsets = offsets
            thisAmps = amps
            thisFreqs = freqs
            try:
                thisClocks = statsToDraw[statToDraw]["clocks"]
            except KeyError:
                pass
            try:
                thisOffsets = statsToDraw[statToDraw]["offsets"]
            except KeyError:
                pass
            try:
                thisAmps = statsToDraw[statToDraw]["amps"]
            except KeyError:
                pass
            try:
                thisFreqs = statsToDraw[statToDraw]["freqs"]
            except KeyError:
                pass
            if dynamic:
                for amp in thisAmps:
                    for freq in thisFreqs:
                        minVal = 1e20
                        maxVal = -1e20
                        for clock in thisClocks:
                            for offset in thisOffsets:
                                for chan in range(16):
                                    val = data[clock][offset][stat][amp][freq][chan]
                                    minVal = min(val,minVal)
                                    maxVal = max(val,maxVal)
                                    if getAll:
                                        try:
                                            result[statToDraw].append(val)
                                        except KeyError:
                                            result[statToDraw] = [val]
                if not getAll:
                    result[statToDraw] = [minVal,maxVal]
            else:
                minVal = 1e20
                maxVal = -1e20
                for clock in thisClocks:
                    for offset in thisOffsets:
                          for chan in range(16):
                               val = data[clock][offset][stat][chan]
                               minVal = min(val,minVal)
                               maxVal = max(val,maxVal)
                               if getAll:
                                  try:
                                    result[statToDraw].append(val)
                                  except KeyError:
                                    result[statToDraw] = [val]
                if not getAll:
                    result[statToDraw] = [minVal,maxVal]
        return result

    def getlatestdata(self):
        """
        Returns list of data dicts, only the 
        latest timesamped one per serial.
        """
        datadicts = self.datadicts
        #for datadict in datadicts:
        #    print(datadict["serial"],datadict["timestamp"])
        resultdict = {} # key is serial, value is datadict
        for datadict in datadicts:
            serial = datadict["serial"]
            try:
                olddata = resultdict[serial]
            except KeyError:
                resultdict[serial] = datadict
            else:
                oldtimestamp = olddata["timestamp"]
                newtimestamp = datadict["timestamp"]
                oldtimestamp = datetime.datetime.strptime(oldtimestamp,"%Y-%m-%dT%H:%M:%S")
                newtimestamp = datetime.datetime.strptime(newtimestamp,"%Y-%m-%dT%H:%M:%S")
                if newtimestamp > oldtimestamp:
                  resultdict[serial] = datadict
        #print("result:")
        sortedserials = None
        try:
            sortedserials = sorted(resultdict,key=lambda x: int(x))
        except:
            sortedserials = sorted(resultdict)
        result = []
        for serial in sortedserials:
            datadict = resultdict[serial]
        #    print(datadict["serial"],datadict["timestamp"])
            result.append(datadict)
        return result

def main():
    from ...configuration.argument_parser import ArgumentParser
    parser = ArgumentParser(description="Plots a ranking of ADCs")
    parser.add_argument("infilename",help="Input json file names and/or glob string.",nargs="+")
    args = parser.parse_args()
  
    #from ...configuration import CONFIG
    #config = CONFIG()

    globstr =  "/home/jhugon/dune/coldelectronics/femb_python/hothdaq*"
    ranking = RANKING(args.infilename)
    ranking.rank()
    ranking.histAllChannels()
