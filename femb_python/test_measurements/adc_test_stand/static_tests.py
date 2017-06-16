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
import glob
from uuid import uuid1 as uuid
import numpy
import matplotlib
if os.path.basename(sys.argv[0]) == "femb_adc_static_tests":
    print("Using matplotlib AGG backend")
    matplotlib.use("AGG")
import matplotlib.pyplot as plt
import ROOT

class STATIC_TESTS(object):
    """
    Tests of ADC at for ~DC performance
    """

    def __init__(self,config):
        """
        config is a femb_python.configuration.CONFIG object
        """
        self.config = config
        self.nBits = 12
        self.samplingFreq = 2e6

    def analyzeLinearity(self,infile,diagnosticPlots=True):
        codeHists, bitHists, minCodes, minCodeVs, maxCodes, maxCodeVs, iChip, metadata = self.doHistograms(infile)
        allStats = []
        figmanyDNL = None
        figmanyINL = None
        sumAllCodeHists = numpy.zeros(2**self.nBits)
        manyaxesDNL = []
        manyaxesINL = []
        if diagnosticPlots:
          figmanyDNL = plt.figure(figsize=(8,8))
          figmanyDNL.suptitle("ADC: {}, Offset: {}".format(iChip,metadata['adcOffset']))
          figmanyINL = plt.figure(figsize=(8,8))
          figmanyINL.suptitle("ADC: {}, Offset: {}".format(iChip,metadata['adcOffset']))
          figmanyDNL.clf()
          figmanyINL.clf()
          for iChan in range(16):
              manyaxesDNL.append(figmanyDNL.add_subplot(4,4,iChan+1))
              manyaxesDNL[iChan].set_xlim(-256,2**self.nBits+256)
              manyaxesDNL[iChan].set_ylim(-10,30)
              manyaxesDNL[iChan].set_title("Channel: {}".format(iChan),{'fontsize':'small'})
              manyaxesINL.append(figmanyINL.add_subplot(4,4,iChan+1))
              manyaxesINL[iChan].set_xlim(-256,2**self.nBits+256)
              manyaxesINL[iChan].set_ylim(-100,100)
              manyaxesINL[iChan].set_title("Channel: {}".format(iChan),{'fontsize':'small'})
              #xticks = [x*1024 for x in range(5)]
              xticks = [0,0.5*2**self.nBits,2**self.nBits]
              manyaxesDNL[iChan].set_xticks(xticks)
              manyaxesINL[iChan].set_xticks(xticks)
              if iChan % 4 != 0:
                  manyaxesDNL[iChan].set_yticklabels([])
                  manyaxesINL[iChan].set_yticklabels([])
              else:
                  manyaxesDNL[iChan].set_ylabel("DNL [LSB]")
                  manyaxesINL[iChan].set_ylabel("INL [LSB]")
              if iChan // 4 != 3:
                  manyaxesDNL[iChan].set_xticklabels([])
                  manyaxesINL[iChan].set_xticklabels([])
              else:
                  manyaxesDNL[iChan].set_xlabel("ADC Code")
                  manyaxesINL[iChan].set_xlabel("ADC Code")
        for iChan in range(16):
                chanStats = {}
                codeHist = codeHists[iChan]
                sumAllCodeHists += codeHist
                indices, choppedCodeHist = self.chopOffUnfilledBins(codeHist)
                indices256, choppedCodeHist256 = self.chopLowCodes(256,codeHist)
                indices400, choppedCodeHist400 = self.chopLowCodes(400,codeHist)
                indices512, choppedCodeHist512 = self.chopLowCodes(512,codeHist)
                dnl, inl = self.makeLinearityHistograms(indices,choppedCodeHist)
                dnl256, inl256 = self.makeLinearityHistograms(indices256,choppedCodeHist256)
                dnl400, inl400 = self.makeLinearityHistograms(indices400,choppedCodeHist400)
                dnl512, inl512 = self.makeLinearityHistograms(indices512,choppedCodeHist512)
                dnlKillStuckCodes, inlKillStuckCodes = self.makeLinearityHistograms(indices,choppedCodeHist,True)
                stuckCodeFraction, stuckCodeFractionShouldBe = self.getStuckCodeFraction(indices,choppedCodeHist)
                stuckCodeFraction400, stuckCodeFractionShouldBe400 = self.getStuckCodeFraction(indices400,choppedCodeHist400)
                stuckCodeDNL, stuckCodeDNL0, stuckCodeDNL1 = self.getStuckCodeDNLs(indices,dnl)
                DNL75perc = numpy.percentile(dnl,75)
                DNL75percNoStuck = numpy.percentile(dnlKillStuckCodes,75)
                DNL75percStuck = numpy.percentile(stuckCodeDNL,75)
                INLabs75perc = numpy.percentile(abs(inl),75)
                DNL75perc256 = numpy.percentile(dnl256,75)
                INLabs75perc256 = numpy.percentile(abs(inl256),75)
                DNL75perc400 = numpy.percentile(dnl400,75)
                INLabs75perc400 = numpy.percentile(abs(inl400),75)
                DNL75perc512 = numpy.percentile(dnl512,75)
                INLabs75perc512 = numpy.percentile(abs(inl512),75)

                chanStats["DNLmax"] = max(dnl)
                chanStats["INLabsMax"] = max(abs(inl))
                chanStats["DNLmax256"] = max(dnl256)
                chanStats["INLabsMax256"] = max(abs(inl256))
                chanStats["DNLmax400"] = max(dnl400)
                chanStats["INLabsMax400"] = max(abs(inl400))
                chanStats["DNLmax512"] = max(dnl512)
                chanStats["INLabsMax512"] = max(abs(inl512))
                chanStats["DNLmaxNoStuck"] = max(dnlKillStuckCodes)
                chanStats["INLabsNoStuck"] = max(abs(inlKillStuckCodes))
                chanStats["stuckCodeFrac"] = stuckCodeFraction
                chanStats["stuckCodeFracShouldBe"] = stuckCodeFractionShouldBe
                chanStats["stuckCodeFrac400"] = stuckCodeFraction400
                chanStats["stuckCodeFracShouldBe400"] = stuckCodeFractionShouldBe400
                chanStats["DNL75perc"] = DNL75perc
                chanStats["DNL75perc256"] = DNL75perc256
                chanStats["DNL75perc400"] = DNL75perc400
                chanStats["DNL75perc512"] = DNL75perc512
                chanStats["DNL75percNoStuck"] = DNL75percNoStuck
                chanStats["DNL75percStuck"] = DNL75percStuck
                chanStats["INLabs75perc"] = INLabs75perc
                chanStats["INLabs75perc256"] = INLabs75perc256
                chanStats["INLabs75perc400"] = INLabs75perc400
                chanStats["INLabs75perc512"] = INLabs75perc512
                lsbPerV = float(maxCodes[iChan] - minCodes[iChan]) / (maxCodeVs[iChan] - minCodeVs[iChan])
                codeAtZeroV = maxCodes[iChan] - lsbPerV * maxCodeVs[iChan]
                chanStats["lsbPerV"] = lsbPerV
                chanStats["codeAtZeroV"] = codeAtZeroV

                chanStats["minCode"] = int(minCodes[iChan])
                chanStats["minCodeV"] = float(minCodeVs[iChan])
                chanStats["maxCode"] = int(maxCodes[iChan])
                chanStats["maxCodeV"] = float(maxCodeVs[iChan])
                allStats.append(chanStats)

                if diagnosticPlots:
                    ## Stuck Code Analysis
                    stuckCodeBins = numpy.linspace(-1,50,200)
                    fig, ax = plt.subplots(figsize=(8,8))
                    ax.set_yscale('log')
                    print("chan {:2} stuckCodeFraction: {:6.3f}, should be: {:6.3f}".format(iChan,stuckCodeFraction,stuckCodeFractionShouldBe))
                    #ax.hist(dnlKillStuckCodes, bins=stuckCodeBins, histtype='step',label="LSB Not 000000 or 111111",log=True)
                    if numpy.isfinite(stuckCodeDNL).any():
                      ax.hist(stuckCodeDNL, bins=stuckCodeBins, histtype='step',label="LSB: 000000 or 111111",log=True)
                    if numpy.isfinite(stuckCodeDNL0).any():
                      ax.hist(stuckCodeDNL0,bins=stuckCodeBins, histtype='step',label="LSB: 000000",log=True)
                    if numpy.isfinite(stuckCodeDNL1).any():
                      ax.hist(stuckCodeDNL1,bins=stuckCodeBins, histtype='step',label="LSB: 111111",log=True)
                    ax.legend()
                    ax.set_ylabel("Number of Codes")
                    ax.set_xlabel("DNL [bits]")
                    ax.set_ylim(0,ax.get_ylim()[1])
                    #ax.set_ylim(0.1,200)
                    filename = "ADC_StuckCodeHist_Chip{}_Chan{}_Offset{}".format(iChip,iChan,metadata['adcOffset'])
                    fig.savefig(filename+".png")
                    #print("Avg, stddev of dnlNoStuckCodes: {} {}, Avg, stddev of stuck code dnl: {} {}".format(numpy.mean(dnlKillStuckCodes), numpy.std(dnlKillStuckCodes),numpy.mean(stuckCodeDNL),numpy.std(stuckCodeDNL)))
                    #print("65th, 80th, 90th percentile of non-stuck DNL: {:6.2f} {:6.2f} {:6.2f}, and stuck code dnl: {:6.2f} {:6.2f} {:6.2f}".format(numpy.percentile(dnlKillStuckCodes,65), numpy.percentile(dnlKillStuckCodes,80), numpy.percentile(dnlKillStuckCodes,90),numpy.percentile(stuckCodeDNL,65),numpy.percentile(stuckCodeDNL,80),numpy.percentile(stuckCodeDNL,90)))
                    print("chan {:2} 75th percentile of DNL: {:6.2f} non-stuck DNL: {:6.2f} stuck code dnl: {:6.2f}  INL: {:6.2f}".format(iChan,DNL75perc,DNL75percNoStuck,DNL75percStuck,INLabs75perc))
                    ax.cla()

                    ### Plot DNL
                    ax.set_yscale('linear')
                    axRight = ax.twinx()
                    ax.plot(indices,dnl,"k-",label="All Codes")
                    manyaxesDNL[iChan].plot(indices,dnl,"k-",label="All Codes",lw=1)
                    if self.nBits == 12:
                      ax.plot(indices,dnlKillStuckCodes,"b-",label="No LSBs: 000000 or 111111")
                      manyaxesDNL[iChan].plot(indices,dnlKillStuckCodes,"b-",label="No LSBs: 000000 or 111111 or 000001",lw=1)
                    ax.set_xlabel("ADC Code")
                    ax.set_ylabel("DNL [Least Significant Bits]")
                    ax.set_title("ADC Chip {} Channel {}".format(iChip,iChan))
                    ax.set_xticks([x*2**(self.nBits-2) for x in range(5)])
                    if self.nBits == 12:
                      ax.legend(loc='best')
                    xmin, xmax, ymin, ymax = ax.axis()
                    ymin *= 2**(-self.nBits)*100.
                    ymax *= 2**(-self.nBits)*100.
                    axRight.set_ylim(ymin,ymax)
                    axRight.set_ylabel("DNL [% of Full Scale]")
                    #axFSR = self.makePercentFSRAxisOnLSBAxis(ax)
                    #axFSR.set_label("DNL [% of FSR]")
                    filename = "ADC_DNL_Chip{}_Chan{}_Offset{}".format(iChip,iChan,metadata["adcOffset"])
                    fig.savefig(filename+".png")
                    #fig.savefig(filename+".pdf")
                    ax.cla()
                    axRight.cla()
                    
                    ### On to INL
                    #ax.plot(indices,inl,"k-",label="All Codes")
                    ax.plot(indices256,inl256,"b-",label="All Codes$\geq$256")
                    ax.plot(indices400,inl400,"b-",label="All Codes$\geq$400")
                    ax.plot(indices512,inl512,"c-",label="All Codes$\geq$512")
                    #manyaxesINL[iChan].plot(indices,inl,"k-",label="All Codes")
                    #manyaxesINL[iChan].plot(indices256,inl256,"b-",label="All Codes$\geq$256")
                    #manyaxesINL[iChan].plot(indices512,inl512,"c-",label="All Codes$\geq$512")
                    manyaxesINL[iChan].plot(indices400,inl400,"b-",label="All Codes$\geq$400")
                    #ax.plot(indices,inlKillStuckCodes,"b-",label="No LSBs: 000000 or 111111")
                    ax.set_xlabel("ADC Code")
                    ax.set_ylabel("INL [Least Significant Bits]")
                    ax.set_title("ADC Chip {} Channel {}".format(iChip,iChan))
                    ax.set_xticks([x*2**(self.nBits-2) for x in range(5)])
                    xmin, xmax, ymin, ymax = ax.axis()
                    ymin *= 2**(-self.nBits)*100.
                    ymax *= 2**(-self.nBits)*100.
                    axRight.set_ylim(ymin,ymax)
                    axRight.set_ylabel("INL [% of Full Scale]")
                    #axFSR = self.makePercentFSRAxisOnLSBAxis(ax)
                    #axFSR.set_label("DNL [% of FSR]")
                    ax.legend(loc='best')
                    filename = "ADC_INL_Chip{}_Chan{}_Offset{}".format(iChip,iChan,metadata["adcOffset"])
                    fig.savefig(filename+".png")
                    #fig.savefig(filename+".pdf")
                    ax.cla()
                    axRight.cla()
                    plt.close(fig)
        if diagnosticPlots:
            filename = "ADC_DNL_Chip{}_Offset{}".format(iChip,metadata["adcOffset"])
            figmanyDNL.savefig(filename+".png")
            #figmanyDNL.savefig(filename+".pdf")
            filename = "ADC_INL_Chip{}_Offset{}".format(iChip,metadata["adcOffset"])
            figmanyINL.savefig(filename+".png")
            #figmanyINL.savefig(filename+".pdf")

            indicesAll, choppedSumAllCodeHists = self.chopOffUnfilledBins(sumAllCodeHists)
            dnlAll, inlAll = self.makeLinearityHistograms(indicesAll,choppedSumAllCodeHists)
            dnlAllKillStuckCodes, inlAllKillStuckCodes = self.makeLinearityHistograms(indicesAll,choppedSumAllCodeHists,True)
            ax.plot(indicesAll,dnlAll,"k-",label="All Codes")
            if self.nBits == 12:
              ax.plot(indicesAll,dnlAllKillStuckCodes,"b-",label="No LSBs: 000000 or 111111 or 000001")
            ax.set_xlabel("ADC Code")
            ax.set_ylabel("DNL [LSB]")
            ax.set_title("Using Histograms Summed Over Channels of Chip: {0}".format(iChip))
            ax.set_xticks([x*2**(self.nBits-2) for x in range(5)])
            if self.nBits == 12:
              ax.legend(loc='best')
            filename = "ADC_DNL_Sum_Chip{}_Offset{}".format(iChip,metadata["adcOffset"])
            fig.savefig(filename+".png")
            #fig.savefig(filename+".pdf")
            ax.cla()
            plt.close(fig)
            plt.close(figmanyDNL)
            plt.close(figmanyINL)

            #print("Chip: ",iChip)
            #for code in indicesAll[dnl > 1.5]:
            #   print("code: {}, code % 6: {} code % 12: {} code % 64: {}, bits: {:#014b} ".format(code,code % 6,code % 12, code % 64,code))

        return allStats

    def doHistograms(self,infilename):
        """
        Creates histograms of data doing a linear ramp of 
        the full ADC range + 10% on each end.

        Returns (codeHists, codeMod12Hists, bitHists):
            where each one is a list of dicts of histograms, 
            and the histograms are just arrays of counts.

            codeHists[iChan][iCode] = count
            bitHists[iChan][iBit] = count
        """

        #fig, ax = plt.subplots(figsize=(8,8))
        codeHists = []
        bitHists = []
        minCodes = []
        minCodeVs = []
        maxCodes = []
        maxCodeVs = []
        iChip = -1
        metadata = None
        for iChan in range(16):
           hist, minCode, minCodeV, maxCode, maxCodeV, iChip, metadata = self.makeRampHist(iChan,infilename)
           minCodes.append(minCode)
           minCodeVs.append(minCodeV)
           maxCodes.append(maxCode)
           maxCodeVs.append(maxCodeV)
           codeHists.append(hist)
           #ax.plot(range(len(hist)),hist,"ko")
           #ax.set_xlabel("ADC Code")
           #ax.set_ylabel("Entries / ADC Code")
           #ax.set_title("ADC Chip {} Channel {}".format(iChip,iChan))
           #ax.set_xticks([x*2**(self.nBits-2) for x in range(5)])
           #filename = "ADC_Hist_Chip{}_Chan{}".format(iChip,iChan)
           #fig.savefig(filename+".png")
           ##fig.savefig(filename+".pdf")
           #ax.cla()

           #if iChan == 4:
           #    for modX in [6,8,12,16,64]:
           #        self.plotModXHistogram(hist,modX,iChip,iChan)

           bitHist = self.makeBitHistogram(hist)
           bitHists.append(bitHist)
           #ax.plot(range(len(bitHist)),bitHist,"ko")
           #ax.set_xlabel("ADC Bit")
           #ax.set_ylabel("Entries / ADC Bit")
           #ax.set_title("ADC Chip {} Channel {}".format(iChip,iChan))
           #ax.set_xlim(-1,self.nBits)
           #ax.set_xticks(range(0,self.nBits))
           #filename = "ADC_BitHist_Chip{}_Chan{}".format(iChip,iChan)
           #fig.savefig(filename+".png")
           ##fig.savefig(filename+".pdf")
           #ax.cla()
        #plt.close(fig)
        return codeHists, bitHists, minCodes, minCodeVs, maxCodes, maxCodeVs, iChip, metadata

    def makeRampHist(self,iChan,infilename):
        """
        Makes a histogram of linear ramp data between xLow and xHigh 
        for iChip and iChan. The histogram will have at leas nSamples entries.
        """
        #print("makeRampHist: ",iChan,infilename)

        samples, iChip, metadata = self.loadWaveform(iChan,infilename)
        cleanedSamples, minCode, minCodeV, maxCode, maxCodeV = self.cleanWaveform(samples,metadata)
        binning = [i-0.5 for i in range(2**self.nBits+1)]
        hist, bin_edges = numpy.histogram(cleanedSamples,bins=binning)
        return hist, minCode, minCodeV, maxCode, maxCodeV, iChip, metadata

    def makeCodeModXHistogram(self,counts,modNumber):
        """
        Makes a histogram of code % modNumber from code 
        histogram. Excludes bottom and top codes.

        counts is an array of counts 4096 long

        modNumber is the int to take the code mod

        Returns an array of counts modNumber long
        """
        assert(len(counts)==2**self.nBits)
        result = numpy.zeros(modNumber)
        indexArray = numpy.arange(len(counts))
        for i in range(modNumber):
            goodElements = (indexArray % modNumber) == i
            goodElements[0] = False
            goodElements[-1] = False
            result[i] = numpy.sum(counts[goodElements])
        return result

    def makeBitHistogram(self,counts):
        """
        Makes a histogram of times each bit=1. Excludes 
        bottom and top codes.

        counts is an array of counts 4096 long

        Returns an array of counts 12 long
        """
        assert(len(counts)==2**self.nBits)
        result = numpy.zeros(self.nBits)
        indexArray = numpy.arange(len(counts))
        for i in range(self.nBits):
            goodElements = ((indexArray >> i) & 0x1) > 0
            goodElements[0] = False
            goodElements[-1] = False
            result[i] = numpy.sum(counts[goodElements])
        return result

    def chopOffUnfilledBins(self,counts):
        """
        Chops the empty bins of the start and end of the histogram counts

        counts is an array of counts

        Returns an array of indices and an array of the corresponding counts
        """
        iStart = 0
        nCounts = len(counts)
        for i in range(nCounts-1):
          if counts[i] > 0. and counts[i+1] > 0.:
            iStart = i
            break
        iEnd = nCounts - 1
        for i in reversed(range(1,nCounts)):
          if counts[i] > 0. and counts[i-1] > 0.:
            iEnd = i
            break
        indices = numpy.arange(iStart,iEnd+1)
        outcounts = counts[iStart:iEnd+1]
        assert(len(indices)==len(outcounts))
        return indices, outcounts

    def chopLowCodes(self,lowestBin,counts):
        """
        Chops bins lower than lowestBin

        counts is an array of counts

        Returns an array of indices and an array of the corresponding counts
        """
        indices = numpy.arange(len(counts))
        indices = indices[lowestBin:]
        outcounts = counts[lowestBin:]
        assert(len(indices)==len(outcounts))
        return indices, outcounts

    def makeLinearityHistograms(self,indices,counts,killStuckCodes=False):
        """
        Makes arrays of DNL and INL.

        counts is an array of counts 4096 long

        Returns two arrays each 4096 long: (dnl,inl)

        If killStuckCodes=True, then the dnl for codes ending 
        in 0b000000 or 0b111111 is set to 0.
        """
        nIndices = len(indices)
        nGoodSamples = sum(counts[1:-1])
        if nGoodSamples == 0:
            return numpy.ones(counts.shape)*float('nan'), numpy.ones(counts.shape)*float('nan'),
        countIdeal = nGoodSamples / (nIndices - 2)
        dnl = counts/countIdeal - 1.
        dnl[0] = 0.
        dnl[-1] = 0.
        if killStuckCodes:
          for i,index in enumerate(indices):
            lsb6 = index & 0b111111
            if lsb6 == 0b111111 or lsb6 == 0:
                dnl[i] = 0.
        inl = numpy.zeros(dnl.shape)
        for i in range(len(dnl)-1):
            inl[i] = dnl[1:i+1].sum()
        return dnl,inl

    def getStuckCodeDNLs(self,indices,dnls):
        """
        Makes arrays of DNL of codes with LSBs of 000000 or 111111

        indices is an array of codes

        dnls is an array of dnl values correspoinding to the codes in indices

        Returns 3 arrays of dnl
            values of codes: One for 0b000000, one for 0b111111, and one 
            for either.

        """
        dnlStuck = []
        dnlStuck0 = []
        dnlStuck1 = []
        for i,index in enumerate(indices):
            lsb6 = index & 0b111111
            isZeros = lsb6 == 0b111111
            isOnes = lsb6 == 9
            if isZeros or isOnes:
                dnlStuck.append(dnls[i])
            if isZeros:
                dnlStuck0.append(dnls[i])
            if isOnes:
                dnlStuck1.append(dnls[i])
        dnlStuck.sort()
        dnlStuck0.sort()
        dnlStuck1.sort()
        #dnlBins = numpy.linspace(-1,100,1000)
        #dnlStuckHist = numpy.histogram(dnlStuck,dnlBins)
        #dnlStuck0Hist = numpy.histogram(dnlStuck0,dnlBins)
        #dnlStuck1Hist = numpy.histogram(dnlStuck1,dnlBins)
        return dnlStuck, dnlStuck0, dnlStuck1

    def getStuckCodeFraction(self,indices,counts):
        """
        Returns the fraction of counts in stuck code indices, and the fraction of codes that are 000000 or 111111

        indices is an array of codes

        counts in an array of counts correspoinding to the codes in indices

        """
        #print("first and last indices:",indices[0:10],indices[-10:])
        indices = numpy.array(indices)
        counts = numpy.array(counts)
        if indices[0] == 0:
            indices = indices[1:]
            counts = counts[1:]
        if indices[-1] == 4095:
            indices = indices[:-1]
            counts = counts[:-1]
        sumAll = counts.sum()
        sumStuckCodes = 0
        nStuckCodes = 0
        for i,index in enumerate(indices):
            lsb6 = index & 0b111111
            isZeros = lsb6 == 0
            isOnes = lsb6 == 0b111111
            if isZeros or isOnes:
                sumStuckCodes += counts[i]
                nStuckCodes += 1
        return float(sumStuckCodes)/sumAll, float(nStuckCodes)/len(indices)

    def plotModXHistogram(self,hist,modNumber,iChan):
        fig, ax = plt.subplots(figsize=(8,8))
        codeModXHist = self.makeCodeModXHistogram(hist,modNumber)
        ax.plot(range(len(codeModXHist)),codeModXHist,"ko")
        ax.set_xlabel("ADC Code Mod {}".format(modNumber))
        ax.set_ylabel("Entries / (ADC Code Mod {})".format(modNumber))
        ax.set_title("ADC Channel {}".format(iChan))
        ax.set_xlim(-1,modNumber)
        ax.set_xticks(range(0,modNumber))
        filename = "ADC_CodeMod{}Hist_Chan{}".format(modNumber,iChan)
        fig.savefig(filename+".png")
        #fig.savefig(filename+".pdf")
        fig.clf()
        plt.close(fig)
        return codeModXHist

    def makePercentFSRAxisOnLSBAxis(self,ax):
        ax2 = ax.twinx()
        ylow,yhigh = ax.get_ylim()
        ax2.set_ylim(ylow/2.**self.nBits*100,yhigh/2.**self.nBits*100)
        return ax2

    def cleanWaveform(self,waveform,metadata):
        freq = metadata["funcFreq"]
        nSamplesPeriod = self.samplingFreq/freq
        #print("nSamplesPeriod: ",nSamplesPeriod)
        iFirstPeak = None
        firstMax = numpy.max(waveform[int(0.5*nSamplesPeriod):min(int(1.7*nSamplesPeriod),len(waveform)-1)])
        #print("firstMax: ",firstMax)
        maxCodeV = None
        for iSample in range(int(0.5*nSamplesPeriod),min(int(1.7*nSamplesPeriod),len(waveform)-1)):
            if not (iFirstPeak is None):
                break
            if waveform[iSample] >= firstMax and waveform[iSample+1] < firstMax:
                for jSample in range(iSample,-1,-1):
                    if waveform[jSample-1] < firstMax:
                        iFirstPeak = 0.5*(iSample + jSample)
                        maxCodeV = metadata["funcOffset"]+metadata["funcAmp"]-(iSample-jSample)/nSamplesPeriod*metadata["funcAmp"]*2
                        break
        #print("iFirstPeak: ",iFirstPeak)
        #print("maxCodeV: ",maxCodeV)
        # Get rid of spurious jumps upward for very low voltage inputs
        # Also find the min ADC code and the time from the peak to it
        cleanWaveform = []
        minCodes = []
        minCodeVs = []
        for iPeak in range(int(numpy.ceil(iFirstPeak)),len(waveform),int(numpy.floor(nSamplesPeriod))):
            # First look before peak
            iStartLook = iPeak - int(0.3*nSamplesPeriod)
            iStopLook = iPeak - int(nSamplesPeriod/2.)
            iStopLook = max(iStopLook,0)
            minCode = numpy.min(waveform[iStopLook:iStartLook])
            iStart = iStopLook
            for iLook in range(iStartLook,iStopLook,-1):
                if waveform[iLook] <= minCode:
                    iStart = iLook
                    break
            minCodeV = metadata["funcOffset"]+metadata["funcAmp"]-(iPeak-iStart)/nSamplesPeriod*metadata["funcAmp"]*4
            minCodes.append(minCode)
            minCodeVs.append(minCodeV)
            # then look after peak
            iStartLook = iPeak + int(0.3*nSamplesPeriod)
            iStopLook = iPeak + int(nSamplesPeriod/2.) -1 # -1 to not double count 
            iStopLook = min(iStopLook,len(waveform))
            if iStartLook < len(waveform) and iStopLook > iStartLook + 1:
              minCode = numpy.min(waveform[iStartLook:iStopLook-1])
              iEnd = iStopLook-1
              for iLook in range(iStartLook,iStopLook-1):
                  if waveform[iLook] <= minCode:
                      iEnd = iLook
                      break
              minCodeV = metadata["funcOffset"]+metadata["funcAmp"]-(iEnd-iPeak)/nSamplesPeriod*metadata["funcAmp"]*4
              minCodes.append(minCode)
              minCodeVs.append(minCodeV)
              cleanWaveform.extend(waveform[iStart:iEnd+1])

        #print(minCodes)
        #print(minCodeVs)
        minCode = numpy.median(minCodes)
        minCodeV = numpy.median(minCodeVs)
        #print(minCode,minCodeV,metadata['funcOffset'],metadata['funcAmp'],nSamplesPeriod)

        #fig, ax = plt.subplots()
        #ax.plot(cleanWaveform)
        #plt.show()

        return numpy.array(cleanWaveform), minCode, minCodeV, firstMax, maxCodeV

    def loadWaveform(self,iChan,infilename):
        f = ROOT.TFile(infilename)
        tree = f.Get("femb_wfdata")
        metadataTree = f.Get("metadata")
        metadataTree.GetEntry(0)
        metadata = {
            'funcType': metadataTree.funcType,
            'funcAmp': metadataTree.funcAmp,
            'funcOffset': metadataTree.funcOffset,
            'funcFreq': metadataTree.funcFreq,
            'adcSerial': metadataTree.adcSerial,
            'adcOffset': metadataTree.adcOffset,
            }
        if metadata['funcType'] != 3:
            raise Exception("Input file is not funcType==3 ramp data")
        result = []
        for iEntry in range(tree.GetEntries()):
            tree.GetEntry(iEntry)
            if iChan == tree.chan:
                adccode = tree.wf
                adccode = list(adccode)
                if self.nBits < 12:
                    adccode = [i >> (12 - self.nBits) for i in adccode]
                result.extend(adccode)
        return result, metadata['adcSerial'], metadata

    def centralFiniteDifference(self,waveform,i):
        """
        1st deriv 4th order
        """
        #return 1/12.*waveform[i-2]-2/3.*waveform[i-1]+2/3.*waveform[i+1]-1/12.*waveform[i+2]
        return (0.25*waveform[i-2]-2*waveform[i-1]+2*waveform[i+1]-0.25*waveform[i+2])/3.

    def forwardFiniteDifference(self,waveform,i):
        """
        1st deriv 4th order
        """
        #return -25./12*waveform[i]+4*waveform[i+1]-3*waveform[i+2]+4/3*waveform[i+3]-0.25*waveform[i+4]
        return (-25./12*waveform[i]+4*waveform[i+1]-3*waveform[i+2]+4/3*waveform[i+3]-0.25*waveform[i+4])
        
def main():
    from ...configuration.argument_parser import ArgumentParser
    from ...configuration import CONFIG
    ROOT.gROOT.SetBatch(True)
    parser = ArgumentParser(description="Measures ADC Linearity")
    parser.add_argument("infilename",help="Input file name. The file created by femb_adc_collect_data that includes 'functype3'.")
    parser.add_argument("-q", "--quiet",help="Disables output plots and printing, just dumps stats to stdout.",action='store_true')
    args = parser.parse_args()
  
    config = CONFIG()
  
    static_tests = STATIC_TESTS(config)
    stats = static_tests.analyzeLinearity(args.infilename,diagnosticPlots=not args.quiet)
    if args.quiet:
        print(stats)
