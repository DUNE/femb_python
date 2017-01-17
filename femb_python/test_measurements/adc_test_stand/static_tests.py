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
import glob
from uuid import uuid1 as uuid
import numpy
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
        self.NASICS = config.NASICS
        self.nBits = 12

    def analyzeLinearity(self,fileprefix):
        codeHists, bitHists = self.doHistograms(fileprefix)
        fig, ax = plt.subplots(figsize=(8,8))
        axRight = ax.twinx()
        figmanyDNL = plt.figure(figsize=(8,8))
        figmanyINL = plt.figure(figsize=(8,8))
        for iChip in range(self.NASICS):
            sumAllCodeHists = numpy.zeros(2**self.nBits)
            figmanyDNL.clf()
            figmanyINL.clf()
            manyaxesDNL = []
            manyaxesINL = []
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
                try:
                    codeHist = codeHists[iChip][iChan]
                    sumAllCodeHists += codeHist
                    indices, choppedCodeHist = self.chopOffUnfilledBins(codeHist)
                    dnl, inl = self.makeLinearityHistograms(indices,choppedCodeHist)
                    dnlKillStuckCodes, inlKillStuckCodes = self.makeLinearityHistograms(indices,choppedCodeHist,True)

                    ### Plot DNL
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
                    filename = "ADC_DNL_Chip{}_Chan{}".format(iChip,iChan)
                    fig.savefig(filename+".png")
                    #fig.savefig(filename+".pdf")
                    ax.cla()
                    axRight.cla()
                    
                    ### On to INL
                    ax.plot(indices,inl,"k-",label="All Codes")
                    manyaxesINL[iChan].plot(indices,inl,"k-",label="All Codes")
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
                    #ax.legend(loc='best')
                    filename = "ADC_INL_Chip{}_Chan{}".format(iChip,iChan)
                    fig.savefig(filename+".png")
                    #fig.savefig(filename+".pdf")
                    ax.cla()
                    axRight.cla()
                    
                    # Stuck Code Analysis
                    stuckCodeFraction, stuckCodeFractionShouldBe = self.getStuckCodeFraction(indices,choppedCodeHist)
                    print("chan {:2} stuckCodeFraction: {:6.3f}, should be: {:6.3f}".format(iChan,stuckCodeFraction,stuckCodeFractionShouldBe))
                    stuckCodeDNL, stuckCodeDNL0, stuckCodeDNL1 = self.getStuckCodeDNLs(indices,dnl)
                    stuckCodeBins = numpy.linspace(-1,50,200)
                    #ax.hist(dnlKillStuckCodes, bins=stuckCodeBins, histtype='step',label="LSB Not 000000 or 111111",log=True)
                    ax.hist(stuckCodeDNL, bins=stuckCodeBins, histtype='step',label="LSB: 000000 or 111111",log=True)
                    ax.hist(stuckCodeDNL0,bins=stuckCodeBins, histtype='step',label="LSB: 000000",log=True)
                    ax.hist(stuckCodeDNL1,bins=stuckCodeBins, histtype='step',label="LSB: 111111",log=True)
                    ax.legend()
                    ax.set_ylabel("Number of Codes")
                    ax.set_xlabel("DNL [bits]")
                    ax.set_ylim(0,ax.get_ylim()[1])
                    #ax.set_ylim(0.1,200)
                    filename = "ADC_StuckCodeHist_Chip{}_Chan{}".format(iChip,iChan)
                    fig.savefig(filename+".png")
                    #print("Avg, stddev of dnlNoStuckCodes: {} {}, Avg, stddev of stuck code dnl: {} {}".format(numpy.mean(dnlKillStuckCodes), numpy.std(dnlKillStuckCodes),numpy.mean(stuckCodeDNL),numpy.std(stuckCodeDNL)))
                    #print("65th, 80th, 90th percentile of non-stuck DNL: {:6.2f} {:6.2f} {:6.2f}, and stuck code dnl: {:6.2f} {:6.2f} {:6.2f}".format(numpy.percentile(dnlKillStuckCodes,65), numpy.percentile(dnlKillStuckCodes,80), numpy.percentile(dnlKillStuckCodes,90),numpy.percentile(stuckCodeDNL,65),numpy.percentile(stuckCodeDNL,80),numpy.percentile(stuckCodeDNL,90)))
                    print("chan {:2} 75th percentile of non-stuck DNL: {:6.2f}, and stuck code dnl: {:6.2f}".format(iChan,numpy.percentile(dnlKillStuckCodes,75),numpy.percentile(stuckCodeDNL,75)))
                except KeyError as e:
                    pass
            filename = "ADC_DNL_Chip{}".format(iChip)
            figmanyDNL.savefig(filename+".png")
            #figmanyDNL.savefig(filename+".pdf")
            filename = "ADC_INL_Chip{}".format(iChip)
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
            filename = "ADC_DNL_Sum_Chip{}".format(iChip)
            fig.savefig(filename+".png")
            #fig.savefig(filename+".pdf")
            ax.cla()

            #print("Chip: ",iChip)
            #for code in indicesAll[dnl > 1.5]:
            #   print("code: {}, code % 6: {} code % 12: {} code % 64: {}, bits: {:#014b} ".format(code,code % 6,code % 12, code % 64,code))

    def doHistograms(self,fileprefix):
        """
        Creates histograms of data doing a linear ramp of 
        the full ADC range + 10% on each end.

        Returns (codeHists, codeMod12Hists, bitHists):
            where each one is a list of dicts of histograms, 
            and the histograms are just arrays of counts.

            codeHists[iChip][iChan][iCode] = count
            bitHists[iChip][iChan][iBit] = count
        """

        fig, ax = plt.subplots(figsize=(8,8))
        codeHists = []
        bitHists = []
        for iChip in range(self.NASICS):
            codeHists.append({})
            bitHists.append({})
            for iChan in range(16):
               hist = self.makeRampHist(iChip,iChan,fileprefix)
               codeHists[iChip][iChan] = hist
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
               bitHists[iChip][iChan] = bitHist
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
        return codeHists,bitHists

    def makeRampHist(self,iChip,iChan,fileprefix):
        """
        Makes a histogram of linear ramp data between xLow and xHigh 
        for iChip and iChan. The histogram will have at leas nSamples entries.
        """
        #print("makeRampHist: ",iChip,iChan,xLow,xHigh,nSamples)

        samples = self.loadWaveforms(iChip,iChan,fileprefix)
        binning = [i-0.5 for i in range(2**self.nBits+1)]
        hist, bin_edges = numpy.histogram(samples,bins=binning)
        return hist

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
        sumAll = counts.sum()
        sumStuckCodes = 0
        nStuckCodes = 0
        for i,index in enumerate(indices):
            lsb6 = index & 0b111111
            isZeros = lsb6 == 0b111111
            isOnes = lsb6 == 9
            if isZeros or isOnes:
                sumStuckCodes += counts[i]
                nStuckCodes += 1
        return float(sumStuckCodes)/sumAll, float(nStuckCodes)/len(indices)

    def plotModXHistogram(self,hist,modNumber,iChip,iChan):
        fig, ax = plt.subplots(figsize=(8,8))
        codeModXHist = self.makeCodeModXHistogram(hist,modNumber)
        ax.plot(range(len(codeModXHist)),codeModXHist,"ko")
        ax.set_xlabel("ADC Code Mod {}".format(modNumber))
        ax.set_ylabel("Entries / (ADC Code Mod {})".format(modNumber))
        ax.set_title("ADC Chip {} Channel {}".format(iChip,iChan))
        ax.set_xlim(-1,modNumber)
        ax.set_xticks(range(0,modNumber))
        filename = "ADC_CodeMod{}Hist_Chip{}_Chan{}".format(modNumber,iChip,iChan)
        fig.savefig(filename+".png")
        #fig.savefig(filename+".pdf")
        fig.clf()
        return codeModXHist

    def makePercentFSRAxisOnLSBAxis(self,ax):
        ax2 = ax.twinx()
        ylow,yhigh = ax.get_ylim()
        ax2.set_ylim(ylow/2.**self.nBits*100,yhigh/2.**self.nBits*100)
        return ax2

    def loadWaveforms(self,iChip,iChan,fileprefix):
        filenames = glob.glob(fileprefix+"_chip{}_chan{}_functype3_*.root".format(iChip,iChan))
        assert(len(filenames)==1)
        files = []
        trees = []
        metadataTrees = []
        for fn in filenames:
            f = ROOT.TFile(fn)
            files.append(f)
            trees.append(f.Get("femb_wfdata"))
            metadataTrees.append(f.Get("metadata"))
        metadatas = []
        amplitudes = set()
        frequencies = set()
        for mdt in metadataTrees:
            mdt.GetEntry(0)
            md = {
                'funcType': mdt.funcType,
                'funcAmp': mdt.funcAmp,
                'funcOffset': mdt.funcOffset,
                'funcFreq': mdt.funcFreq,
                }
            metadatas.append(md)
            if not mdt.funcAmp in amplitudes:
                amplitudes.add(mdt.funcAmp)
            if not mdt.funcFreq in frequencies:
                frequencies.add(mdt.funcFreq)
        
        result = []
        for iTree in range(len(metadatas)):
          md = metadatas[iTree]
          if md['funcType'] == 3:
            tree = trees[iTree]
            for iEntry in range(tree.GetEntries()):
                tree.GetEntry(iEntry)
                thisChip = tree.chan//16
                thisChannel = tree.chan % 16
                if iChip == thisChip and iChan == thisChannel:
                    adccode = tree.wf
                    adccode = list(adccode)
                    if self.nBits < 12:
                        adccode = [i >> (12 - self.nBits) for i in adccode]
                    result.extend(adccode)
        if len(result) == 0:
            raise Exception("File not found")
        return result
        
def main():
    from ...configuration.argument_parser import ArgumentParser
    from ...configuration import CONFIG
    ROOT.gROOT.SetBatch(True)
    parser = ArgumentParser(description="Measures ADC Linearity")
    parser.addLoadWaveformRootFileArgs(True)
    parser.addNPacketsArgs(False,10)
    #parser.add_argument("outfilename",help="Output root file name")
    args = parser.parse_args()
  
    config = CONFIG()
  
    static_tests = STATIC_TESTS(config)
    if args.loadWaveformRootFile:
        static_tests.loadWaveformRootFileName = args.loadWaveformRootFile
    static_tests.analyzeLinearity(args.loadWaveformRootFile)
