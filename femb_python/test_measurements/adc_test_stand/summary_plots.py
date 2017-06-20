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
import os.path
import json
import numpy
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.lines as mlines
from matplotlib.figure import Figure

class SUMMARY_PLOTS(object):

    def __init__(self,stats,outfileprefix,plotAll=False):
        try:
            stats["static"].keys()
        except KeyError:
            print("No static")
        try:
            stats["dynamic"].keys()
        except KeyError:
            print("No dynamic")
        self.stats = stats
        self.time = stats['timestamp']
        self.serial = stats['serial']
        self.outfileprefix = outfileprefix
        colors = ["grey","m","plum","darkorchid","firebrick","red","sienna","sandybrown","gold","y","olivedrab","chartreuse","seagreen","paleturquoise","deepskyblue","navy","blue"]*2
        colors.reverse()
        clocks = [-1,0,1,2] # clock int: -1 undefined, 0 external, 1 internal monostable, 2 internal FIFO
        sampleRates = [2000000,1000000]
        for sampleRate in sampleRates:
            try:
                self.stats["static"][sampleRate]
            except KeyError:
                try:
                    self.stats["static"][str(sampleRate)]
                except KeyError as e:
                    try:
                        self.stats["dynamic"][sampleRate]
                    except KeyError:
                        try:
                            self.stats["dynamic"][str(sampleRate)]
                        except KeyError as e:
                            print("Not using sampleRate: ",sampleRate)
                            continue  # skip this sampleRate if no data for it
                        else:
                            sampleRate = str(sampleRate)
                else:
                    sampleRate = str(sampleRate)
            sampleRateFn = "2MHz"
            sampleRateLabel = "2 MHz"
            if int(sampleRate) == 1000000:
                sampleRateFn = "1MHz"
                sampleRateLabel = "1 MHz"
            for iClock in clocks:
                self.legendHandles = []
                clockFn = "extClock"
                clockLabel="External Clock"
                if int(iClock) == -1:
                  clockFn = "undefClock"
                  clockLabel="Undefined Clock"
                elif int(iClock) == 0:
                  clockFn = "extClock"
                  clockLabel="External Clock"
                elif int(iClock) == 1:
                  clockFn = "intClock"
                  clockLabel="Internal Clock"
                elif int(iClock) == 2:
                  clockFn = "fifoClock"
                  clockLabel="FIFO Clock"
                ## json dict keys must be strings, so these keys are strings when read from json
                self.offsets = set()
                try:
                    self.offsets.update(self.stats["static"][sampleRate][iClock].keys())
                except KeyError:
                    try:
                        self.offsets.update(self.stats["static"][sampleRate][str(iClock)].keys())
                    except KeyError:
                        pass
                try:
                    self.offsets.update(self.stats["dynamic"][sampleRate][iClock].keys())
                except KeyError:
                    try:
                        self.offsets.update(self.stats["dynamic"][sampleRate][str(iClock)].keys())
                    except KeyError:
                        pass
                if len(self.offsets) == 0:
                    print("Not using iClock: ",iClock, "for sampleRate: ",sampleRate)
                    continue  # skip this iClock if no data for it
                self.offsets = list(self.offsets)
                self.offsets.sort(key=lambda x: int(x))
                if not plotAll:
                    self.offsets = self.offsets[:1]
                self.colorDict = {}
                for i, offset in enumerate(self.offsets):
                    self.colorDict[offset] = colors[i]
                fig, ((ax1,ax2,ax3),(ax4,ax5,ax6),(ax7,ax8,ax9)) = plt.subplots(3,3,figsize=(12,12))
                if plotAll:
                    fig.subplots_adjust(left=0.07,right=0.91,bottom=0.05,top=0.92,wspace=0.27)
                else:
                    fig.subplots_adjust(left=0.07,right=0.93,bottom=0.05,top=0.92,wspace=0.27)
                fig.suptitle("ADC {}, {}, {}, \nTest Time: {}".format(self.serial,clockLabel,sampleRateLabel,self.time),fontsize='x-large')
                self.staticSummary(sampleRate,iClock,ax1,ax3,ax2,ax4,ax5)
                self.dynamicSummary(sampleRate,iClock,ax7)
                self.inputPinSummary(sampleRate,iClock,ax8)
                self.dcSummary(sampleRate,iClock,ax6)
                self.doLegend(fig,self.colorDict,patches=True,offsets=True)
                ax9.set_visible(False)
                fig.savefig(self.outfileprefix + "_"+clockFn+"_"+sampleRateFn+".png")
                fig.savefig(self.outfileprefix + "_"+clockFn+"_"+sampleRateFn+".pdf")
                plt.close(fig)
                if not plotAll:
                    break

    def staticSummary(self,sampleRate,iClock,ax1,ax2,ax3,ax4,ax5):
        data = None
        try:
            data = self.stats["static"][sampleRate][iClock]
        except KeyError:
            try:
                data = self.stats["static"][sampleRate][str(iClock)]
            except KeyError:
                print("No staticSummary for iClock: ",iClock)
                return
        ax1.set_xlabel("Channel")
        ax2.set_xlabel("Channel")
        ax3.set_xlabel("Channel")
        ax4.set_xlabel("Channel")
        ax5.set_xlabel("Channel")
        ax1.set_ylabel("DNL [LSB]")
        ax2.set_ylabel("Stuck Code Fraction")
        ax3.set_ylabel("INL [LSB]")
        ax4.set_ylabel("Min ADC Code or Max ADC Code - 4095")
        ax5.set_ylabel("V at Min or Max ADC Code [V]")
        linestyle = ['solid',"dashed","dashdot","dotted"]*10
        markerstyle = ['o','s','*','p','^']*10
        legendDict1 = {}
        legendDict2 = {}
        legendDict3 = {}
        legendDict4 = {}
        legendDict5 = {}
        for offset in self.offsets:
            try:
                data[offset]
            except KeyError:
                continue
            color = self.colorDict[offset]
            i1 = 0
            im1 = 0
            i2 = 0
            i3 = 0
            i4 = 0
            i4 = 0
            for stat in sorted(data[offset]):
              if stat[:13] == "stuckCodeFrac":
                if not ("400" in stat):
                    continue
                if stat[:21] == "stuckCodeFracShouldBe":
                  ax2.plot(data[offset][stat],label=stat,c='k',ls="dotted")
                  legendDict2[stat] = ("dotted",None)
                else:
                  ax2.plot(data[offset][stat],label=stat,c=color,ls=linestyle[i2],drawstyle="steps-mid")
                  legendDict2[stat] = (linestyle[i2],None)
                  i2 += 1
              elif stat[:3] == "DNL":
                if not ("400" in stat):
                    continue
                if "max" in stat.lower():
                  ax1.plot(data[offset][stat],label="Max",c=color,marker=markerstyle[im1],ls="")
                  legendDict1["Max"] = ("",markerstyle[im1])
                  im1 += 1
                else:
                  ax1.plot(data[offset][stat],label="75th Percentile",c=color,ls=linestyle[i1],drawstyle="steps-mid")
                  legendDict1["75th Percentile"] = (linestyle[i1],None)
                  i1 += 1
              elif stat[:3] == "INL":
                if not ("400" in stat):
                    continue
                if not str(offset) == "-1":
                    continue
                if "max" in stat.lower():
                  ax3.plot(data[offset][stat],label="Max",c=color,marker=markerstyle[0],ls="")
                  legendDict3["Max"] = ("",markerstyle[0])
                else:
                  ax3.plot(data[offset][stat],label="75th Percentile",c=color,ls=linestyle[0],drawstyle="steps-mid")
                  legendDict3["75th Percentile"] = (linestyle[0],None)
              elif stat == "lsbPerV" or stat == "codeAtZeroV":
                continue
              elif stat == "maxCode":
                if str(offset) != "-1": continue
                dataTmp = numpy.array(data[offset][stat])
                ax4.plot(dataTmp-4095,label="Max Code",c=color,ls=linestyle[0],drawstyle="steps-mid")
              elif stat == "minCode":
                if str(offset) != "-1": continue
                dataTmp = numpy.array(data[offset][stat])
                ax4.plot(dataTmp,label="Min Code",c=color,ls=linestyle[1],drawstyle="steps-mid")
              elif stat == "maxCodeV":
                if str(offset) != "-1": continue
                dataTmp = numpy.array(data[offset][stat])
                ax5.plot(dataTmp,label="V at Max Code",c=color,ls=linestyle[0],drawstyle="steps-mid")
              elif stat == "minCodeV":
                if str(offset) != "-1": continue
                dataTmp = numpy.array(data[offset][stat])
                ax5.plot(dataTmp,label="V at Min Code",c=color,ls=linestyle[1],drawstyle="steps-mid")
        ax1.set_yscale("log")
        ax3.set_yscale("log")
        ylim = ax1.get_ylim()
        newylim = [x for x in ylim]
        if ylim[0] > 0.1:
            newylim[0] = 0.1
        if ylim[1] < 100:
            newylim[1] = 100
        ax1.set_ylim(*newylim)
        ylim = ax2.get_ylim()
        newylim = [x for x in ylim]
        if ylim[0] > 0:
            newylim[0] = 0
        if ylim[1] < 0.1:
            newylim[1] = 0.1
        ax2.set_ylim(*newylim)
        ylim = ax3.get_ylim()
        newylim = [x for x in ylim]
        if ylim[0] > 1:
            newylim[0] = 1
        if ylim[1] < 1000:
            newylim[1] = 1000
        ax3.set_ylim(*newylim)
        ylim = ax4.get_ylim()
        newylim = [x for x in ylim]
        if ylim[0] > -100:
            newylim[0] = -100
        if ylim[1] < 400:
            newylim[1] = 400
        ax4.set_ylim(*newylim)
        self.doLegend(ax1,legendDict1)
        #self.doLegend(ax2,legendDict2)
        #self.doLegend(ax3,legendDict3)
        ax3.legend(loc="best",fontsize="medium",frameon=False)
        ax4.legend(loc="best",fontsize="medium",frameon=False)
        ax5.legend(loc="best",fontsize="medium",frameon=False)

    def dynamicSummary(self,sampleRate,iClock,ax1):
        data = None
        try:
            data = self.stats["dynamic"][sampleRate][iClock]
        except KeyError:
            try:
                data = self.stats["dynamic"][sampleRate][str(iClock)]
            except KeyError:
                print("No dynamicSummary for iClock: ",iClock)
                return
        linestyle = ['solid',"dashed","dashdot","dotted"]*10
        markerstyle = ['o','s','*','p','^']*10
        legendDict1 = {}
        for offset in self.offsets:
            if int(offset) != -1:
                continue
            try:
                data[offset]
            except KeyError:
                continue
            color = self.colorDict[offset]
            i1 = 0
            for stat in sorted(data[offset]):
              if stat.lower() == "sinads":
                for amp in reversed(sorted(data[offset][stat])): # largest amp
                  freqs = sorted(data[offset][stat][amp],key=lambda x: float(x))
                  for freq in reversed(freqs):
                    freqStr = "{:.1f} kHz".format(float(freq)/1000.)
                    ax1.plot(data[offset][stat][amp][freq],label=freqStr,c=color,ls=linestyle[i1],drawstyle="steps-mid")
                    legendDict1[freqStr] = (linestyle[i1],None)
                    i1 += 1
                  break
        ylim = ax1.get_ylim()
        newylim = [x for x in ylim]
        if ylim[0] > 0:
            newylim[0] = 0
        if ylim[1] < 70:
            newylim[1] = 70
        ax1.set_ylim(*newylim)
        ax1.set_xlabel("Channel")
        ax1.set_ylabel("SINAD [dBc]")
        #self.doLegend(ax1,legendDict1)
        ax1.legend(loc="best",fontsize="medium",frameon=False)

    def inputPinSummary(self,sampleRate,iClock,ax1):
        data = None
        try:
            data = self.stats["inputPin"][sampleRate][iClock]
        except KeyError:
            try:
                data = self.stats["inputPin"][sampleRate][str(iClock)]
            except KeyError:
                ax1.set_visible(False)
                print("No inputPinSummary for iClock: ",iClock)
                return
        ax1.set_xlabel("Channel")
        ax1.set_ylabel("Input Pin Mean [ADC]")
        linestyle = ['solid',"dashed","dashdot","dotted"]*10
        markerstyle = ['o','s','*','p','^']*10
        legendDict1 = {}
        legendDict2 = {}
        for offset in data:
            color = self.colorDict[offset]
            i1 = 0
            for stat in sorted(data[offset]):
              if stat.lower() == "mean":
                ax1.plot(data[offset][stat],label=stat,c=color,ls=linestyle[i1],drawstyle="steps-mid")
                legendDict1[stat] = (linestyle[i1],None)
                i1 += 1
        ylim = ax1.get_ylim()
        newylim = [x for x in ylim]
        if ylim[0] > 0:
            newylim[0] = 0
        if ylim[1] < 4000:
            newylim[1] = 4000
        ax1.set_ylim(*newylim)
        #self.doLegend(ax1,legendDict1)

    def dcSummary(self,sampleRate,iClock,ax1):
        data = None
        try:
            data = self.stats["dc"][sampleRate][iClock]
        except KeyError:
            try:
                data = self.stats["dc"][sampleRate][str(iClock)]
            except KeyError:
                print("No dcSummary for iClock: ",iClock)
                return
        ax1.set_xlabel("Channel")
        ax1.set_ylabel("ADC Code")
        linestyle = ['solid',"dashed","dashdot","dotted"]*10
        markerstyle = ['o','s','*','p','^']*10
        legendDict1 = {}
        for offset in self.offsets:
            if str(offset) != "-1": 
                continue
            try:
                data[offset]
            except KeyError:
                continue
            color = self.colorDict[offset]
            for stat in reversed(sorted(data[offset])):
              if stat == "meanCodeFor1.6V":
                 ax1.plot(data[offset][stat],label=stat[-4:],c=color,marker=markerstyle[0],ls="")
              elif stat == "meanCodeFor0.2V":
                 ax1.plot(data[offset][stat],label=stat[-4:],c=color,ls=linestyle[0],drawstyle="steps-mid")
        ylim = ax1.get_ylim()
        newylim = [x for x in ylim]
        if ylim[0] > -100:
            newylim[0] = -100
        if ylim[1] < 5000:
            newylim[1] = 5000
        ax1.set_ylim(*newylim)
        ax1.legend(loc="best",fontsize="medium",frameon=False)

    def doLegend(self,ax,legendDict,patches=False,offsets=False):
        legendHandles = []
        legendLabels = []
        if patches:
            for title in sorted(legendDict.keys(),key=lambda x: int(x)):
                color = legendDict[title]
                if offsets:
                    if str(title) == "-1":
                        title = "Off"
                    else:
                        title = str(title)
                patch = mpatches.Patch(color=color, label=title)
                legendLabels.append(title)
                legendHandles.append(patch)
        else:
            for title in sorted(legendDict):
                ls, marker = legendDict[title]
                line = mlines.Line2D([], [], color='k', marker=marker,
                              ls=ls, label=title)
                legendLabels.append(title)
                legendHandles.append(line)
        self.legendHandles = legendHandles
        if isinstance(ax,Figure):
            ax.legend(self.legendHandles,legendLabels,loc="upper right",fontsize="medium",frameon=False)
            ax.text(0.89,0.978,"Offset:")
        else:
            ax.legend(handles=self.legendHandles,loc="best",fontsize="medium",frameon=False)

def main():
    from ...configuration.argument_parser import ArgumentParser
    from ...configuration import CONFIG
    parser = ArgumentParser(description="Plots summary of ADC Tests")
    parser.add_argument("infilename",help="Input json file name.")
    parser.add_argument("-a","--plotAllOffsets",help="Plot all offset currents, default: only offset disabled",action="store_true")
    args = parser.parse_args()
  
    config = CONFIG()

    with open(args.infilename) as infile:
        data = json.load(infile)
        plotter = SUMMARY_PLOTS(data,os.path.splitext(args.infilename)[0],plotAll=args.plotAllOffsets)
    
