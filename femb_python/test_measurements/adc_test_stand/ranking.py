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
import re
import math
import numpy
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.lines as mlines
import matplotlib.dates
from matplotlib.figure import Figure

def getVersion(summaryDict):
    pathstr = summaryDict["sumatra"]["femb_python_location"]
    match = re.match(r"/opt/sw/releases/femb_python-(.*)/femb_python",pathstr)    
    if match:
        return match.group(1)
    else:
        return "Not Using Official Release"

def datetimeFromTimestamp(timestamp):
    result = None
    try:
        result = datetime.datetime.strptime(timestamp,"%Y%m%dT%H%M%S")
    except ValueError:
        result = datetime.datetime.strptime(timestamp,"%Y-%m-%dT%H:%M:%S")
    return result

class RANKING(object):

    def fileIsGood(self,jsonpath):
        filename = os.path.split(jsonpath)[1]
        if os.path.splitext(filename)[1] == ".json" and "adcTest_" == filename[:8] and not ("Raw" in filename):
            search = re.search(r"\d\d\d\d\d\d\d\dT\d\d\d\d\d\d",filename)
            if not search:
                search = re.search(r"\d\d\d\d-\d\d-\d\dT\d\d:\d\d:\d\d",filename)
            if not search:
                raise ValueError("Couldn't find valid timestamp in filepath: "+str(jsonpath))
            timestamp = search.group(0)
            timestamp = datetimeFromTimestamp(timestamp)
            if self.firstTime:
                if timestamp < self.firstTime:
                    return False
            if self.lastTime:
                if timestamp > self.lastTime:
                    return False
            return True
        return False

    def __init__(self,inglobstrs,firstTime=None,lastTime=None):
        """
        inglobstr is a string that can be parsed by glob to make a list of
        directories containing json files or json files to be analyzed.
        Directories found in the glob will be walked to find subdirectories 
        containing json files.

        firstTime and lastTime are datetimes or None that limit the range 
            of timestamps put in the ranking. The json content isn't used 
            only the timestamp in the filename.
        """

        self.firstTime = firstTime
        self.lastTime = lastTime
        self.colors = ["b","g","orange","gray","y","c","m","plum","sienna","sandybrown","seagreen","deepskyblue","navy"]*5
        jsonpaths = []
        for inglobstr in inglobstrs:
            inpathlist = glob.glob(inglobstr)
            for inpath in inpathlist:
                if os.path.isfile(inpath):
                    if self.fileIsGood(inpath):
                        jsonpaths.append(inpath)
                        print(inpath)
                else:
                    for directory, subdirs, filenames in os.walk(inpath):
                        for filename in filenames:
                            jsonpath = os.path.join(directory,filename)
                            if self.fileIsGood(jsonpath):
                                jsonpaths.append(jsonpath)
                                print(jsonpath)
        datadicts = []
        for jsonpath in jsonpaths:
            with open(jsonpath) as jsonfile:
                datadict = json.load(jsonfile)
                timestamp = datadict["timestamp"]
                timestamp = datetimeFromTimestamp(timestamp)
                if datadict["hostname"] == "hothdaq3":
                    if timestamp < datetime.datetime(2017,6,15,hour=13,minute=5):
                        continue
                if datadict["hostname"] == "hothdaq4":
                    if timestamp < datetime.datetime(2017,6,15,hour=10,minute=53):
                        continue
                datadicts.append(datadict)
        self.datadicts = datadicts

        # 0 for min 1 for max
        self.statsToDraw = {
            "DNL 75%": {"stat":"DNL75perc400"},
            "DNL Max": {"stat":"DNLmax400"},
            "INL 75%": {"stat":"INLabs75perc400","offsets":["-1"]},
            "INL Max": {"stat":"INLabsMax400","offsets":["-1"]},
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
#        for stat in self.statsToDraw:
#            self.statsToDraw[stat]["clocks"] = ["0"]

    def histWorstChannel(self,data,title,outfileprefix,legendTitle=""):
        if type(data) is dict:
            pass
        elif type(data) is list:
            data = {None:data}
        else:
            raise TypeError("data should be list or dict")
        statNames = set()
        sortedKeys = sorted(list(data.keys()))
        if data == {}:
            return
        elif len(sortedKeys) == 1:
            if len(data[sortedKeys[0]]) == 0:
                return
        maxValsPerCase = {}
        minValsPerCase = {}
        maxValsAll = {}
        minValsAll = {}
        for key in sortedKeys:
            datadicts = data[key]
            minMaxPerSerials = {}
            for datadict in datadicts:
                asic_stats = {}
                serial = datadict["serial"]
                static = datadict["static"]
                asic_stats.update(self.getstats(static))
                dynamic = datadict["dynamic"]
                asic_stats.update(self.getstats(dynamic,True))
                try:
                    inputPin = datadict["inputPin"]
                except KeyError:
                    print("Warning: no input pin stats for chip",serial)
                else:
                    asic_stats.update(self.getstats(inputPin))
                try:
                    dc = datadict["dc"]
                except KeyError:
                    print("Warning: no dc stats for chip",serial)
                else:
                    asic_stats.update(self.getstats(dc))
                minMaxPerSerials[serial] = asic_stats
                for stat in asic_stats:
                    statNames.add(stat)
            #print("AllStatNames:")
            #print(sorted(statNames))
            maxValsThis = {}
            minValsThis = {}
            for statName in statNames:
                minValsThis[statName] = []
                maxValsThis[statName] = []
                try:
                    maxValsAll[statName]
                except KeyError:
                    maxValsAll[statName] = []
                try:
                    minValsAll[statName]
                except KeyError:
                    minValsAll[statName] = []
                for serial in minMaxPerSerials:
                    try:
                        minValsThis[statName].append(minMaxPerSerials[serial][statName][0])
                        maxValsThis[statName].append(minMaxPerSerials[serial][statName][1])
                        minValsAll[statName].append(minMaxPerSerials[serial][statName][0])
                        maxValsAll[statName].append(minMaxPerSerials[serial][statName][1])
                    except KeyError as e:
                        print("Warning KeyError for asic: ",serial," stat: ",statName," error: ",e)
                        pass
            maxValsPerCase[key] = maxValsThis
            minValsPerCase[key] = minValsThis
        statNamesToDraw = sorted(self.statsToDraw)
        nStats = len(statNamesToDraw)
        #print("statNamesToDraw:")
        #print(statNamesToDraw)
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
                    ax.set_yscale("log")
                    doMin = False
                    try:
                        doMin = self.statsToDraw[statName]["min"]
                    except KeyError:
                        pass
                    histRange = (min(maxValsAll[statName]),max(maxValsAll[statName]))
                    nVals = len(maxValsAll[statName])
                    nBins = 10
                    if nVals > 30:
                        nBins = 20
                    if nVals > 100:
                        nBins = 40 
                    hist, bin_edges = numpy.histogram(maxValsAll[statName],nBins,range=histRange)
                    if doMin:
                        nVals = len(minValsAll[statName])
                        nBins = 10
                        if nVals > 30:
                            nBins = 20
                        if nVals > 100:
                            nBins = 40 
                        histRange = (min(minValsAll[statName]),max(minValsAll[statName]))
                        hist, bin_edges = numpy.histogram(minValsAll[statName],nBins,range=histRange)
                    for iKey, key in enumerate(sortedKeys):
                        try:
                            if doMin: #min
                                if len(minValsPerCase[key][statName])>0:
                                    ax.hist(minValsPerCase[key][statName],bin_edges,range=histRange,histtype="step",color=self.colors[iKey])
                                    ax.set_xlabel("min({})".format(statName))
                            else: #max
                                if len(maxValsPerCase[key][statName])>0:
                                    ax.hist(maxValsPerCase[key][statName],bin_edges,range=histRange,histtype="step",color=self.colors[iKey])
                                    ax.set_xlabel("max({})".format(statName))
                        except KeyError as e:
                            print("Warning: Could not find stat to draw",e)
                    ax.relim()
                    ax.autoscale_view(False,True,True)
                    ax.set_ylim(bottom=0.5)
                    ax.xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(nbins=7))
                    #ax.set_ylim(0,ax.get_ylim()[1]*1.2)
                    self.set_xticks(ax)
            plt.tight_layout()
            fig.subplots_adjust(top=0.95)
            fig.suptitle(title,fontsize="large")
            if len(sortedKeys) > 1 or not (sortedKeys[0] is None):
                self.doLegend(fig,sortedKeys,legendTitle=legendTitle)
            fig.savefig(outfileprefix+"_page{}.png".format(iFig))
            #fig.savefig(outfileprefix+"_page{}.pdf".format(iFig))

    def histAllChannels(self,data,title,outfileprefix,legendTitle=""):
        if type(data) is dict:
            pass
        elif type(data) is list:
            data = {None:data}
        else:
            raise TypeError("data should be list or dict")
        statNames = set()
        allValsPerCase = {}
        allVals = {}
        sortedKeys = sorted(list(data.keys()))
        if data == {}:
            return
        elif len(sortedKeys) == 1:
            if len(data[sortedKeys[0]]) == 0:
                return
        for key in sortedKeys:
            datadicts = data[key]
            statsPerSerial = {}
            for datadict in datadicts:
                asic_stats = {}
                serial = datadict["serial"]
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
                statsPerSerial[serial] = asic_stats
                for stat in asic_stats:
                    statNames.add(stat)
            #print("AllStatNames:")
            #print(sorted(statNames))
            allValsThis = {}
            for statName in statNames:
                allValsThis[statName] = []
                try:
                    allVals[statName]
                except KeyError:
                    allVals[statName] = []
                for serial in statsPerSerial:
                    try:
                        allValsThis[statName].extend(statsPerSerial[serial][statName])
                        allVals[statName].extend(statsPerSerial[serial][statName])
                    except KeyError as e:
                        print("Warning KeyError for asic: ",serial," stat: ",statName," error: ",e)
                        pass
            allValsPerCase[key] = allValsThis
        statNamesToDraw = sorted(self.statsToDraw)
        nStats = len(statNamesToDraw)
        #print("statNamesToDraw:")
        #print(statNamesToDraw)
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
                    ax.set_yscale("log")
                    ax.set_ylabel("Channels / bin")
                    ax.set_xlabel("{}".format(statName))
                    histRange = (min(allVals[statName]),max(allVals[statName]))
                    nVals = len(allVals[statName])
                    nBins = 10
                    if nVals > 30:
                        nBins = 20
                    if nVals > 100:
                        nBins = 40 
                    #print(allVals[statName])
                    #print(outfileprefix,statName)
                    #justinSilly = sorted(allVals[statName])
                    #print(justinSilly[:10],justinSilly[-10:])
                    #print(nVals,histRange)
                    hist, bin_edges = numpy.histogram(allVals[statName],nBins,range=histRange)
                    for iKey, key in enumerate(sortedKeys):
                        try:
                            ax.hist(allValsPerCase[key][statName],bin_edges,range=histRange,histtype="step",color=self.colors[iKey])
                        except KeyError as e:
                            print("Warning: Could not find stat to draw",e)
                    ax.relim()
                    ax.autoscale_view(False,True,True)
                    ax.set_ylim(bottom=0.5)
                    ax.xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(nbins=7))
                    #ax.set_ylim(0,ax.get_ylim()[1]*1.2)
                    self.set_xticks(ax)
            plt.tight_layout()
            fig.subplots_adjust(top=0.95)
            fig.suptitle(title,fontsize="large")
            if len(sortedKeys) > 1 or not (sortedKeys[0] is None):
                self.doLegend(fig,sortedKeys,legendTitle=legendTitle)
            fig.savefig(outfileprefix+"_page{}.png".format(iFig))
            #fig.savefig(outfileprefix+"_page{}.pdf".format(iFig))

    def worstChannelVVar(self,data,varfunc,title,outfileprefix,xlabel=None,xlims=None,legendTitle=""):
        if type(data) is dict:
            pass
        elif type(data) is list:
            data = {None:data}
        else:
            raise TypeError("data should be list or dict")
        statNames = set()
        maxValsPerCase = {}
        minValsPerCase = {}
        varsPerCase = {}
        sortedKeys = sorted(list(data.keys()))
        if data == {}:
            return
        elif len(sortedKeys) == 1:
            if len(data[sortedKeys[0]]) == 0:
                return
        for key in sortedKeys:
            datadicts = data[key]
            minLists = {}
            maxLists = {}
            varLists = {}
            for datadict in datadicts:
                asic_stats = {}
                serial = datadict["serial"]
                static = datadict["static"]
                asic_stats.update(self.getstats(static))
                dynamic = datadict["dynamic"]
                asic_stats.update(self.getstats(dynamic,True))
                try:
                    inputPin = datadict["inputPin"]
                except KeyError:
                    print("Warning: no input pin stats for chip",serial)
                else:
                    asic_stats.update(self.getstats(inputPin))
                try:
                    dc = datadict["dc"]
                except KeyError:
                    print("Warning: no dc stats for chip",serial)
                else:
                    asic_stats.update(self.getstats(dc))
                for stat in asic_stats:
                    statNames.add(stat)
                    try:
                        minLists[stat].append(asic_stats[stat][0])
                    except KeyError:
                        minLists[stat] = [ asic_stats[stat][0] ]
                    try:
                        maxLists[stat].append(asic_stats[stat][1])
                    except KeyError:
                        maxLists[stat] = [ asic_stats[stat][1] ]
                    try:
                        varLists[stat].append(varfunc(datadict))
                    except KeyError:
                        varLists[stat] = [ varfunc(datadict) ]
            maxValsPerCase[key] = maxLists
            minValsPerCase[key] = minLists
            varsPerCase[key] = varLists
        statNamesToDraw = sorted(self.statsToDraw)
        nStats = len(statNamesToDraw)
        #print("statNamesToDraw:")
        #print(statNamesToDraw)
        nx = 4
        ny = 4
        nPerFig = nx*ny
        for iFig in range(int(numpy.ceil(nStats/nPerFig))):
            fig, axes2D = plt.subplots(4,4,figsize=(12,12))
            #fig.subplots_adjust(left=0.07,right=0.93,bottom=0.05,top=0.95,wspace=0.25)
            axes = [y for x in axes2D for y in x]
            dateStr = ""
            for iAx, ax in enumerate(axes):
                try:
                    statName = statNamesToDraw[iFig*nPerFig+iAx]
                except IndexError:
                    ax.axis("off")
                    continue
                else:
                    doMin = False
                    try:
                        doMin = self.statsToDraw[statName]["min"]
                    except KeyError:
                        pass
                    xDates = False
                    for iKey, key in enumerate(sortedKeys):
                        try:
                            if doMin: #min
                                if len(minValsPerCase[key][statName])>0:
                                    if type(varsPerCase[key][statName][0]) == datetime.datetime:
                                        xDates = True
                                        ax.plot_date(varsPerCase[key][statName],minValsPerCase[key][statName],color=self.colors[iKey],markersize=3,markeredgewidth=0)
                                    else:
                                        ax.scatter(varsPerCase[key][statName],minValsPerCase[key][statName],color=self.colors[iKey],s=5)
                                        ax.set_xlabel(xlabel)
                                    ax.set_ylabel("min({})".format(statName))
                            else: #max
                                if len(maxValsPerCase[key][statName])>0:
                                    if type(varsPerCase[key][statName][0]) == datetime.datetime:
                                        xDates = True
                                        ax.plot_date(varsPerCase[key][statName],maxValsPerCase[key][statName],color=self.colors[iKey],markersize=3,markeredgewidth=0)
                                        ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%Y%m%dT%H%M"))
                                    else:
                                        ax.scatter(varsPerCase[key][statName],maxValsPerCase[key][statName],color=self.colors[iKey],s=5)
                                        ax.set_xlabel(xlabel)
                                    ax.set_ylabel("max({})".format(statName))
                        except KeyError as e:
                            print("Warning: Could not find stat to draw",e)
                    ax.relim()
                    if xDates:
                        # xlim are floats with units of days
                        xlim = ax.get_xlim()
                        ndays = xlim[1]-xlim[0]
                        # Round to midnight
                        xlim = (math.floor(xlim[0]),math.ceil(xlim[1]))
                        ax.set_xlim(xlim)
                        if ndays > 1.:
                            locator = matplotlib.dates.AutoDateLocator(minticks=3,maxticks=5,interval_multiples=True)
                            ax.xaxis.set_major_locator(locator)
                            ax.xaxis.set_minor_locator(matplotlib.dates.DayLocator(interval=1))
                            ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%Y-%m-%d"))
                        else:
                            ax.xaxis.set_major_locator(matplotlib.dates.HourLocator(interval=6))
                            ax.xaxis.set_minor_locator(matplotlib.dates.HourLocator(interval=1))
                            ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%H:%M"))
                            dateStr = " for "+str(matplotlib.dates.num2date(xlim[0]).strftime("%Y-%m-%d"))
                        for label in ax.get_xticklabels():
                            label.set_rotation(30)
                            label.set_ha("right")
                    else:
                            ax.xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(nbins=4))
                    if xlims:
                        ax.set_xlim(*xlims)

            plt.tight_layout()
            fig.subplots_adjust(top=0.95)
            fig.suptitle(title+dateStr,fontsize="large")
            if len(sortedKeys) > 1 or not (sortedKeys[0] is None):
                self.doLegend(fig,sortedKeys,patches=True,legendTitle=legendTitle)
            fig.savefig(outfileprefix+"_page{}.png".format(iFig))
            #fig.savefig(outfileprefix+"_page{}.pdf".format(iFig))

    def set_xticks(self,ax):
        xlim = ax.get_xlim()
        xticks = numpy.linspace(xlim[0],xlim[1],4)
        xticklabels = ["{:.1g}".format(x) for x in xticks]
        ax.set_xticks(xticks)

    def doLegend(self,ax,titles,patches=False,legendTitle=""):
        legendHandles = []
        legendLabels = []
        for iTitle, title in enumerate(titles):
            if patches:
                patch = mpatches.Patch(color=self.colors[iTitle],
                               label=title)
                legendHandles.append(patch)
            else:
                line = mlines.Line2D([], [], color=self.colors[iTitle],
                               label=title)
                legendHandles.append(line)
            legendLabels.append(title)
        self.legendHandles = legendHandles
        ncol = 1
        if len(titles) > 7:
            ncol = 2
        if isinstance(ax,Figure):
            ax.legend(self.legendHandles,legendLabels,loc="lower right",fontsize="large",frameon=False,ncol=ncol,title=legendTitle)
        else:
            ax.legend(handles=self.legendHandles,loc="best",fontsize="medium",frameon=False,ncol=ncol,title=legendTitle)

    def getstats(self,data,dynamic=False,getAll=False):
        statsToDraw = self.statsToDraw
        result = {}
        stats = []
        sampleRates = list(reversed(sorted(data.keys())))
        clocks = []
        noSampleRate = False
        if int(sampleRates[0]) < 1000000: # old style before sampleRates
            noSampleRate = True
            clocks = sampleRates
            sampleRates = [2000000]
        offsets = []
        amps = []
        freqs = []
        for sampleRate in sampleRates:
            thisData = None
            if noSampleRate:
                thisData = data
            else:
                thisData = data[sampleRate]
            clocks = sorted(thisData)
            for clock in clocks:
                offsets = sorted(thisData[clock])
                for offset in offsets:
                    stats = sorted(thisData[clock][offset])
                    if dynamic:
                        for stat in stats: 
                            amps = thisData[clock][offset][stat]
                            for amp in amps:
                                freqs = thisData[clock][offset][stat][amp]
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
            thisSampleRates = sampleRates
            thisClocks = clocks
            thisOffsets = offsets
            thisAmps = amps
            thisFreqs = freqs
            try:
                thisSampleRates = statsToDraw[statToDraw]["sampleRates"]
            except KeyError:
                pass
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
                        for sampleRate in thisSampleRates:
                            thisData = None
                            if noSampleRate:
                                thisData = data
                            else:
                                thisData = data[sampleRate]
                            if float(freq) > 0.5*float(sampleRate):
                                continue
                            for clock in thisClocks:
                                for offset in thisOffsets:
                                    for chan in range(16):
                                        try:
                                            val = thisData[clock][offset][stat][amp][freq][chan]
                                        except KeyError:
                                            continue
                                        else:
                                            if val is None:
                                                print("Warning: None found in {} {} {} {} {} {}".format(clock,offset,stat,amp,freq,chan))
                                                continue
                                            minVal = min(val,minVal)
                                            maxVal = max(val,maxVal)
                                            if getAll:
                                                try:
                                                    result[statToDraw].append(val)
                                                except KeyError:
                                                    result[statToDraw] = [val]
                if not getAll:
                    if minVal == 1e20: minVal = float('nan')
                    if maxVal == -1e20: maxVal = float('nan')
                    result[statToDraw] = [minVal,maxVal]
            else:
                minVal = 1e20
                maxVal = -1e20
                for sampleRate in thisSampleRates:
                    thisData = None
                    if noSampleRate:
                        thisData = data
                    else:
                        thisData = data[sampleRate]
                    for clock in thisClocks:
                        for offset in thisOffsets:
                            for chan in range(16):
                                try:
                                    val = thisData[clock][offset][stat][chan]
                                except KeyError:
                                    continue
                                else:
                                    minVal = min(val,minVal)
                                    maxVal = max(val,maxVal)
                                    if getAll:
                                        if val is None:
                                            print("Warning: None found in {} {} {} {}".format(clock,offset,stat,chan))
                                            continue
                                        try:
                                            result[statToDraw].append(val)
                                        except KeyError:
                                            result[statToDraw] = [val]
                if not getAll:
                    if minVal == 1e20: minVal = float('nan')
                    if maxVal == -1e20: maxVal = float('nan')
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
                oldtimestamp = datetimeFromTimestamp(oldtimestamp)
                newtimestamp = datetimeFromTimestamp(newtimestamp)
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
        #    print(datadict["sumatra"])
            result.append(datadict)
        print("getlatestdata result:")
        print("{:6}  {}".format("Chip #","Timestamp"))
        for d in result:
          print("{:6}  {}".format(d["serial"],d["timestamp"]))
        return result

    def getlatestdataperkey(self,funcToGetKey):
        """
        Returns a dict of list of data dicts, only the 
        latest timesamped one per serial in each list per 
        key, where the funcToGetKey gets the key from the 
        result json.
        """
        datadicts = self.datadicts
        resultdict = {} # resultdict[keyval][serial] value is datadict
        for datadict in datadicts:
            serial = datadict["serial"]
            try:
                keyval = funcToGetKey(datadict)
            except KeyError:
                keyval = "Not Yet Implemented"
            try:
                resultdict[keyval]
            except KeyError:
                resultdict[keyval] = {}
            try:
                olddata = resultdict[keyval][serial]
            except KeyError:
                resultdict[keyval][serial] = datadict
            else:
                oldtimestamp = olddata["timestamp"]
                newtimestamp = datadict["timestamp"]
                oldtimestamp = datetimeFromTimestamp(oldtimestamp)
                newtimestamp = datetimeFromTimestamp(newtimestamp)
                if newtimestamp > oldtimestamp:
                  resultdict[keyval][serial] = datadict
        #print(resultdict.keys())
        #print("result:")
        sortedserials = {}
        for keyval in resultdict:
            try:
                sortedserials[keyval] = sorted(resultdict[keyval],key=lambda x: int(x))
            except:
                sortedserials[keyval] = sorted(resultdict[keyval])
        result = {}
        print("getlatestdataperkey result:")
        print("{:30}  {:5}  {}".format("Key","Chip #","Timestamp"))
        for keyval in resultdict:
            result[keyval] = []
            for serial in sortedserials[keyval]:
                datadict = resultdict[keyval][serial]
                print("{:30}  {:5}  {}".format(keyval,datadict["serial"],datadict["timestamp"]))
                result[keyval].append(datadict)
        return result

    def getalldataperkey(self,funcToGetKey):
        """
        Returns a dict of list of data dicts, where the 
        funcToGetKey gets the key from the 
        result json. These lists contain all dicts that have the key
        """
        datadicts = self.datadicts
        resultdict = {} # resultdict[keyval] value is list of datadict
        for datadict in datadicts:
            try:
                keyval = funcToGetKey(datadict)
            except KeyError:
                keyval = "Not Yet Implemented"
            try:
                resultdict[keyval]
            except KeyError:
                resultdict[keyval] = []
            resultdict[keyval].append(datadict)
        #print(resultdict.keys())
        #print("result:")
        result = {}
        print("getalldataperkey result:")
        print("{:30}  {:5}  {}".format("Key","Chip #","Timestamp"))
        for keyval in resultdict:
            for datadict in resultdict[keyval]:
                print("{:30}  {:5}  {}".format(keyval,datadict["serial"],datadict["timestamp"]))
        return resultdict

def main():
    import sys
    from ...configuration.argument_parser import ArgumentParser
    parser = ArgumentParser(description="Plots a ranking of ADCs")
    parser.add_argument("infilename",help="Input json file names and/or glob string.",nargs="+")
    parser.add_argument("--outprefix",help="Output file prefix",default="")
    parser.add_argument("-a","--all",help="Produce all plots",action="store_true")
    parser.add_argument("-f","--firstTime",help="Only accept times after this timestamp (uses filename)")
    parser.add_argument("-l","--lastTime",help="Only accept times before this timestamp (uses filename)")
    exclusiveArgs = parser.add_mutually_exclusive_group()
    exclusiveArgs.add_argument("--today",help="Only accept timestamps from today (since midnight)",action="store_true")
    exclusiveArgs.add_argument("--previousDay",help="Only accept timestamps from the previous day (midnight to midnight)",action="store_true")
    exclusiveArgs.add_argument("--thisWeek",help="Only accept timestamps from the current week (since Monday)",action="store_true")
    exclusiveArgs.add_argument("--previousWeek",help="Only accept timestamps from the previous week (Monday to Monday)",action="store_true")
    exclusiveArgs.add_argument("--thisWeekFriday",help="Only accept timestamps from the current week (since Friday)",action="store_true")
    exclusiveArgs.add_argument("--previousWeekFriday",help="Only accept timestamps from the previous week (Friday to Friday)",action="store_true")
    args = parser.parse_args()

    if args.firstTime or args.lastTime:
        if args.today or args.previousDay or args.thisWeek or args.previousWeek or args.thisWeekFriday or args.previousWeekFriday:
            print("Error: if --firstTime and/or --lastTime are set, then --today, --previousDay, --thisWeek, --previousWeek, --thisWeekFriday, and --previousWeekFriday must not be used")
            sys.exit(1)
    firstTime = None
    lastTime = None
    if args.firstTime:
        firstTime = datetimeFromTimestamp(args.firstTime)
    if args.lastTime:
        lastTime = datetimeFromTimestamp(args.lastTime)
    if args.previousDay:
        lastTime = datetime.datetime.now().replace(hour=0,minute=0,second=0,microsecond=0)
        firstTime = lastTime - datetime.timedelta(days=1)
    if args.today:
        firstTime = datetime.datetime.now().replace(hour=0,minute=0,second=0,microsecond=0)
    if args.thisWeek:
        firstTime = datetime.datetime.now().replace(hour=0,minute=0,second=0,microsecond=0)
        firstTime -= datetime.timedelta(days=firstTime.weekday())
    if args.previousWeek:
        lastTime = datetime.datetime.now().replace(hour=0,minute=0,second=0,microsecond=0)
        lastTime -= datetime.timedelta(days=lastTime.weekday())
        firstTime = lastTime - datetime.timedelta(days=7)
    if args.thisWeekFriday:
        firstTime = datetime.datetime.now().replace(hour=0,minute=0,second=0,microsecond=0)
        thisWeekday = firstTime.weekday()
        nDays = thisWeekday + (7-4)
        if thisWeekday >= 4: #it's friday or weekend
            nDays = thisWeekday - 4
        firstTime -= datetime.timedelta(days=nDays)
    if args.previousWeekFriday:
        lastTime = datetime.datetime.now().replace(hour=0,minute=0,second=0,microsecond=0)
        thisWeekday = lastTime.weekday()
        nDays = thisWeekday + (7-4)
        if thisWeekday >= 4: #it's friday or weekend
            nDays = thisWeekday - 4
        lastTime -= datetime.timedelta(days=nDays)
        firstTime = lastTime - datetime.timedelta(days=7)
    print("Using data from {} to {}".format(firstTime,lastTime))

    ranking = RANKING(args.infilename,firstTime,lastTime)

    latestData = ranking.getlatestdata()
    ranking.histWorstChannel(latestData,"Worst Channel Histogram for Latest Timestamp","ADC_worstHist")
    ranking.histAllChannels(latestData,"All Channel Histogram for Latest Timestamp","ADC_chanHist")
    for tlk in ["operator","hostname","board_id"]:
        print("Top Level Key: ",tlk)
        latestDataPerTLK = ranking.getlatestdataperkey(lambda x: str(x[tlk]))
        ranking.histWorstChannel(latestDataPerTLK,"Worst Channel for Latest Timestamp per {}".format(tlk),args.outprefix+"ADC_per_{}_worstHist".format(tlk),legendTitle=tlk)
        ranking.histAllChannels(latestDataPerTLK,"All Channel Histogram for Latest Timestamp per {}".format(tlk),args.outprefix+"ADC_per_{}_chanHist".format(tlk),legendTitle=tlk)
    if args.all:
        smtkeys = [
            "linux_username",
            "femb_config_name",
        ]
        for smtkey in smtkeys:
            print("Sumatra Key: ",smtkey)
            latestDataPerSMTKey = ranking.getlatestdataperkey(lambda x: str(x["sumatra"][smtkey]))
            ranking.histWorstChannel(latestDataPerSMTKey,"Worst Channel for Latest Timestamp per {}".format(smtkey),args.outprefix+"ADC_per_{}_worstHist".format(smtkey),legendTitle=smtkey)
            ranking.histAllChannels(latestDataPerSMTKey,"All Channel Histogram for Latest Timestamp per {}".format(smtkey),args.outprefix+"ADC_per_{}_chanHist".format(smtkey),legendTitle=smtkey)
    
    def getVersion(summaryDict):
        pathstr = summaryDict["sumatra"]["femb_python_location"]
        match = re.match(r"/opt/sw/releases/femb_python-(.*)/femb_python",pathstr)    
        if match:
            return match.group(1)
        else:
            return "Not Using Official Release"
    latestDataPerVersion = ranking.getlatestdataperkey(getVersion)
    ranking.histWorstChannel(latestDataPerVersion,"Worst Channel for Latest Timestamp Per Software Version",args.outprefix+"ADC_per_version_worstHist",legendTitle="femb_python version")
    ranking.histAllChannels(latestDataPerVersion,"All Channels for Latest Timestamp Per Software Version",args.outprefix+"ADC_per_version_chanHist",legendTitle="femb_python version")

    def getTemperature(summaryDict):
        cold = summaryDict["sumatra"]["cold"]
        if cold is None:
            return "Not Yet Implemented"
        elif cold:
            return "Cryogenic"
        else:
            return "Room Temperature"
    latestDataPerTemp = ranking.getlatestdataperkey(getTemperature)
    ranking.histWorstChannel(latestDataPerTemp,"Worst Channel for Latest Timestamp Per Temperature",args.outprefix+"ADC_per_temp_worstHist",legendTitle="Temperature")
    ranking.histAllChannels(latestDataPerTemp,"All Channels for Latest Timestamp Per Temperature",args.outprefix+"ADC_per_temp_chanHist",legendTitle="Temperature")


    def getTimestamp(data):
        timestamp = data["timestamp"]
        return datetimeFromTimestamp(timestamp)

    data = ranking.getalldataperkey(lambda x: str(x["sumatra"]["hostname"]))
    ranking.worstChannelVVar(data,getTimestamp,"All Tests, Worst Channel per Chip v. Timestamp",args.outprefix+"ADCVTime_per_hostname",legendTitle="Hostname")
    data = ranking.getalldataperkey(getTemperature)
    ranking.worstChannelVVar(data,getTimestamp,"All Tests, Worst Channel per Chip v. Timestamp",args.outprefix+"ADCVTime_per_temp",legendTitle="Temperature")

    ranking.worstChannelVVar(data,lambda x: x["serial"],"All Tests, Worst Channel per Chip v Chip #",args.outprefix+"ADCVserial_per_temp",xlabel="Chip #",legendTitle="Temperature")
    #ranking.worstChannelVVar(data,lambda x: x["serial"],"All Tests, Worst Channel per Chip v Chip #",args.outprefix+"ADCVserial_per_temp_zoom",xlabel="Chip #",xlims=(0,50),legendTitle="Temperature")

    def getBoard_version(summaryDict):
        #cold = summaryDict["sumatra"]["cold"]
        #temp = None
        #if cold is None:
        #    temp= "Not Yet Implemented"
        #elif cold:
        #    temp= "Cryogenic"
        #else:
        #    temp= "Room Temperature"
        board = summaryDict["board_id"]
        version = getVersion(summaryDict)
        return str(version) +" board "+ str(board)

    if args.all:
        d = ranking.getlatestdataperkey(getBoard_version)
        ranking.histWorstChannel(d,"Worst Channel for Latest Timestamp Per Software Version & Board",args.outprefix+"ADC_per_version_board_worstHist",legendTitle="femb_python version & Board ID")
        ranking.histAllChannels(d,"All Channels for Latest Timestamp Per Software Version & Board",args.outprefix+"ADC_per_version_board_chanHist",legendTitle="femb_python version & Board ID")
        ranking.worstChannelVVar(d,getTimestamp,"All Tests, Worst Channel per Chip v. Timestamp",args.outprefix+"ADCVTime_per_version_board",legendTitle="femb_python version & Board ID")
