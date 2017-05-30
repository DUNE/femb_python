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

class SUMMARY_PLOTS(object):

    def __init__(self,stats,outfileprefix,plotAll=False):
        try:
            print("static keys: ",stats["static"].keys())
        except KeyError:
            print("No static")
        try:
            print("dynamic keys: ",stats["dynamic"].keys())
        except KeyError:
            print("No dynamic")
        self.stats = stats
        self.time = stats['time']
        self.serial = stats['serial']
        self.outfileprefix = outfileprefix
        colors = ["grey","m","plum","darkorchid","firebrick","red","sienna","sandybrown","gold","olivedrab","chartreuse","seagreen","paleturquoise","deepskyblue","navy","blue"]*2
        colors.reverse()
        clocks = [-1,0,1,2] # clock int: -1 undefined, 0 external, 1 internal monostable, 2 internal FIFO
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
            try:
                self.offsets = self.stats["static"][iClock]
            except KeyError:
                try:
                    self.offsets = self.stats["static"][str(iClock)]
                except KeyError:
                    try:
                        self.offsets = self.stats["dynamic"][iClock]
                    except KeyError:
                        try:
                            self.offsets = self.stats["dynamic"][str(iClock)]
                        except KeyError:
                            print("Not using iClock: ",iClock)
                            continue  # skip this iClock if no data for it
            self.offsets = list(self.offsets.keys())
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
            fig.suptitle("ADC {}, {}, \nTest Time: {}".format(self.serial,clockLabel,self.time),fontsize='x-large')
            self.staticSummary(iClock,ax1,ax3,ax2,ax9)
            self.dynamicSummary(iClock,ax5,ax6)
            self.baselineSummary(iClock,ax7,ax8)
            self.doLegend(fig,self.colorDict,patches=True,offsets=True)
            fig.savefig(self.outfileprefix + "_"+clockFn+".png")
            fig.savefig(self.outfileprefix + "_"+clockFn+".pdf")
            plt.close(fig)
            if not plotAll:
                break

    def staticSummary(self,iClock,ax1,ax2,ax3,ax4):
        data = None
        try:
            data = self.stats["static"][iClock]
        except KeyError:
            print("No staticSummary for iClock: ",iClock)
            return
        ax1.set_xlabel("Channel")
        ax2.set_xlabel("Channel")
        ax3.set_xlabel("Channel")
        ax4.set_xlabel("Channel")
        ax1.set_ylabel("DNL [LSB]")
        ax2.set_ylabel("Stuck Code Fraction")
        ax3.set_ylabel("INL [LSB]")
        ax4.set_ylabel("Min ADC Code or Max ADC Code - 4095")
        ax4.set_ylim(-50,400)
        linestyle = ['solid',"dashed","dashdot","dotted"]*10
        markerstyle = ['o','s','*','p','^']*10
        legendDict1 = {}
        legendDict2 = {}
        legendDict3 = {}
        legendDict4 = {}
        for offset in self.offsets:
            color = self.colorDict[offset]
            i1 = 0
            im1 = 0
            i2 = 0
            i3 = 0
            i4 = 0
            for stat in sorted(data[offset]):
              if stat[:13] == "stuckCodeFrac":
                if not ("400" in stat):
                    continue
                if stat[:21] == "stuckCodeFracShouldBe":
                  ax2.plot(data[offset][stat],label=stat,c='k',ls="dotted")
                  legendDict2[stat] = ("dotted",None)
                else:
                  #ax2.plot(data[offset][stat],label=stat,c=color,marker=markerstyle[i2],ls="")
                  ax2.plot(data[offset][stat],label=stat,c=color,ls=linestyle[i2])
                  legendDict2[stat] = (linestyle[i2],None)
                  i2 += 1
              elif stat[:3] == "DNL":
                if not ("400" in stat):
                    continue
                if "max" in stat:
                  ax1.plot(data[offset][stat],label=stat,c=color,marker=markerstyle[im1],ls="")
                  legendDict1[stat] = ("",markerstyle[im1])
                  im1 += 1
                else:
                  ax1.plot(data[offset][stat],label=stat,c=color,ls=linestyle[i1])
                  legendDict1[stat] = (linestyle[i1],None)
                  i1 += 1
              elif stat[:3] == "INL":
                if not ("400" in stat):
                    continue
                #ax3.plot(data[offset][stat],label=stat,c=color,marker=markerstyle[i3],ls="")
                ax3.plot(data[offset][stat],label=stat,c=color,ls=linestyle[i3])
                legendDict3[stat] = (linestyle[i3],None)
                i3 += 1
              else:
                data4 = numpy.array(data[offset][stat])
                if stat[-1] == "V":
                    data4 = data4*100
                elif stat == "maxCode":
                    data4 -= 4095
                ax4.plot(data4,label=stat,c=color,ls=linestyle[i4])
                legendDict4[stat] = (linestyle[i4],None)
                i4 += 1
        ax1.set_yscale("log")
        ax3.set_yscale("log")
        self.doLegend(ax1,legendDict1)
        #self.doLegend(ax2,legendDict2)
        self.doLegend(ax3,legendDict3)
        self.doLegend(ax4,legendDict4)
        ax4Right = ax4.twinx()
        ax4Right.set_ylim(0.010*numpy.array(ax4.get_ylim()))
        ax4Right.set_ylabel("Min/Max ADC Code Voltage [V]")

    def dynamicSummary(self,iClock,ax1,ax2):
        data = None
        try:
            data = self.stats["dynamic"][iClock]
        except KeyError:
            print("No dynamicSummary for iClock: ",iClock)
            return
        linestyle = ['solid',"dashed","dashdot","dotted"]*10
        markerstyle = ['o','s','*','p','^']*10
        freq1 = 0.
        freq2 = 0.
        for offset in self.offsets:
            color = self.colorDict[offset]
            i1 = 0
            i2 = 0
            for stat in sorted(data[offset]):
              if stat.lower() == "sinads":
                for amp in reversed(sorted(data[offset][stat])): # largest amp
                  freqs = sorted(data[offset][stat][amp],key=lambda x: float(x))
                  for freq in freqs[:1]:
                    ax1.plot(data[offset][stat][amp][freq],label=stat,c=color,ls=linestyle[i1])
                    i1 += 1
                    freq1 = float(freq)/1000.
                  for freq in freqs[-1:]:
                    ax2.plot(data[offset][stat][amp][freq],label=stat,c=color,ls=linestyle[i2])
                    i2 += 1
                    freq2 = float(freq)/1000.
                  break
        ax1.set_xlabel("Channel")
        ax1.set_ylabel("SINAD for {:.1f} kHz [dBc]".format(freq1))
        ax2.set_xlabel("Channel")
        ax2.set_ylabel("SINAD for {:.1f} kHz [dBc]".format(freq2))

    def baselineSummary(self,iClock,ax1,ax2):
        data = None
        try:
            data = self.stats["inputPin"][iClock]
        except KeyError:
            print("No baselineSummary for iClock: ",iClock)
            return
        ax1.set_xlabel("Channel")
        ax2.set_xlabel("Channel")
        ax1.set_ylabel("Input Pin Mean [ADC]")
        ax2.set_ylabel("Input Pin RMS [ADC]")
        linestyle = ['solid',"dashed","dashdot","dotted"]*10
        markerstyle = ['o','s','*','p','^']*10
        legendDict1 = {}
        legendDict2 = {}
        for offset in self.offsets:
            color = self.colorDict[offset]
            i1 = 0
            i2 = 0
            for stat in sorted(data[offset]):
              if stat.lower() == "mean":
                ax1.plot(data[offset][stat],label=stat,c=color,ls=linestyle[i1])
                legendDict1[stat] = (linestyle[i1],None)
                i1 += 1
              elif stat.lower() == "rms":
                ax2.plot(data[offset][stat],label=stat,c=color,ls=linestyle[i2])
                legendDict2[stat] = (linestyle[i2],None)
                i2 += 1
        #self.doLegend(ax1,legendDict1)
        #self.doLegend(ax2,legendDict2)

    def doLegend(self,ax,legendDict,patches=False,offsets=False):
        legendHandles = []
        legendLabels = []
        if patches:
            for title in sorted(legendDict.keys(),key=lambda x: int(x)):
                color = legendDict[title]
                if offsets:
                    if title == "-1":
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
            ax.text(0.87,0.978,"Offset:")
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
    
