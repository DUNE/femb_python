from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals
from __future__ import absolute_import
from builtins import range
from future import standard_library
standard_library.install_aliases()
import sys
import os.path
import glob
import numpy
import ROOT

class CALIBRATE_RAMP(object):
    """
    Calibrates ADC ramp data--finds the voltage for each ADC sample
    """

    def __init__(self,infilename):
        self.infilename = infilename
        self.outfilename = os.path.splitext(infilename)[0]+"_calib.root"
        self.samplingFreq = 2e6

    def write_calibrate_tree(self):
        f = ROOT.TFile(self.infilename)

        metadataTree = f.Get("metadata")
        metadataTree.GetEntry(0)
        funcType = metadataTree.funcType
        frequency = metadataTree.funcFreq
        offset = metadataTree.funcOffset
        amplitude = metadataTree.funcAmp
        if funcType != 3:
            print("Calibration error: file not ramp data")
            sys.exit(1)
        intree = f.Get("femb_wfdata")
        print("Creating file: ",self.outfilename)
        fout = ROOT.TFile( self.outfilename, 'recreate' )
        fout.cd()
        metadataTree.CloneTree()
        outtree = intree.CloneTree()

        wfBranch = outtree.GetBranch("wf")
        voltage = ROOT.std.vector( float )()
        voltageBranch = outtree.Branch( 'voltage', voltage )

        for iEntry in range(outtree.GetEntries()):
            outtree.GetEntry(iEntry)
            waveform = numpy.array(list(outtree.wf))
            voltage.resize(len(waveform))
            self.doCalibration(waveform,voltage,frequency,offset,amplitude)
            break
            #for iSample in range(outtree.wf.size()):
            #    #print(outtree.wf[iSample])
            #    voltage.push_back(iSample)
            #voltageBranch.Fill()
            #    if iSample > 10:
            #        break
            #if iEntry > 10:
            #    break

        outtree.Print()
        fout.Write()
        fout.Close()

    def doCalibration(self,waveform,voltage,freq,funcOffset,funcAmp):
        nSamplesPeriod = self.samplingFreq/freq
        iFirstPeak = None
        firstMax = numpy.max(waveform[int(nSamplesPeriod//2.):min(int(3*nSamplesPeriod//2.),len(waveform)-1)])
        maxCodeV = None
        for iSample in range(int(nSamplesPeriod//2.),min(int(3*nSamplesPeriod//2.),len(waveform)-1)):
            if not (iFirstPeak is None):
                break
            if waveform[iSample] >= firstMax and waveform[iSample+1] < firstMax:
                for jSample in range(iSample,-1,-1):
                    if waveform[jSample-1] < firstMax:
                        iFirstPeak = 0.5*(iSample + jSample)
                        maxCodeV = funcOffset+funcAmp-(iSample-jSample)/nSamplesPeriod*funcAmp*2
                        break

        maxCodes = []
        iPeaks = []
        for iTryPeak in range(int(numpy.ceil(iFirstPeak)),len(waveform),int(numpy.floor(nSamplesPeriod))):
            iStartLook = int(iTryPeak - 0.3*nSamplesPeriod)
            iStopLook = int(iTryPeak + 0.3*nSamplesPeriod)
            iStopLook = max(iStopLook,len(waveform))
            maxCode = numpy.max(waveform[iStartLook:iStopLook])
            iStart = None
            iStop = None
            for iLook in range(iStartLook,iStopLook):
                if not(iStart is None) and not (iStop is None):
                    break
                elif (iStart is None) and waveform[iLook] == maxCode:
                    iStart = iLook
                elif not (iStart is None) and (iStop is None) and waveform[iLook] != maxCode:
                    iStop = iLook
            iPeak = 0.5*(iStart + iStop)
            iPeaks.append(iPeak)
        iPeaks = numpy.array(iPeaks)
        print(iPeaks)
        print(iPeaks % nSamplesPeriod)
        print(nSamplesPeriod)
        iAvgPeak = numpy.mean(iPeaks)
        slopePos = 4.*funcAmp/nSamplesPeriod
        print(slopePos)
        for iSample in range(len(waveform)):
            xintercept = ((iSample // nSamplesPeriod) + 0.75)*nSamplesPeriod
            slope = slopePos
            if (float(iSample) % nSamplesPeriod) < 0.5*nSamplesPeriod:
                slope = -slopePos
                xintercept -= 0.5*nSamplesPeriod
            yintercept = - slope * xintercept
            voltage[iSample] = slope*iSample + yintercept + funcOffset
            print(iSample,waveform[iSample],voltage[iSample],xintercept,yintercept)
        
        #import matplotlib.pyplot as plt
        #fig, ax = plt.subplots()
        #ax.plot(waveform)
        #ax.plot(list(voltage))
        #plt.show()
        
        ## Get rid of spurious jumps upward for very low voltage inputs
        ## Also find the min ADC code and the time from the peak to it
        #cleanWaveform = []
        #minCodes = []
        #minCodeVs = []
        #for iPeak in range(int(numpy.ceil(iFirstPeak)),len(waveform),int(numpy.floor(nSamplesPeriod))):
        #    # First look before peak
        #    iStartLook = iPeak - int(0.3*nSamplesPeriod)
        #    iStopLook = iPeak - int(nSamplesPeriod/2.)
        #    iStopLook = max(iStopLook,0)
        #    minCode = numpy.min(waveform[iStopLook:iStartLook])
        #    iStart = iStopLook
        #    for iLook in range(iStartLook,iStopLook,-1):
        #        if waveform[iLook] <= minCode:
        #            iStart = iLook
        #            break
        #    minCodeV = funcOffset+funcAmp-(iPeak-iStart)/nSamplesPeriod*funcAmp*4
        #    minCodes.append(minCode)
        #    minCodeVs.append(minCodeV)
        #    # then look after peak
        #    iStartLook = iPeak + int(0.3*nSamplesPeriod)
        #    iStopLook = iPeak + int(nSamplesPeriod/2.) -1 # -1 to not double count 
        #    iStopLook = min(iStopLook,len(waveform))
        #    if iStartLook < len(waveform):
        #      minCode = numpy.min(waveform[iStartLook:iStopLook-1])
        #      iEnd = iStopLook-1
        #      for iLook in range(iStartLook,iStopLook-1):
        #          if waveform[iLook] <= minCode:
        #              iEnd = iLook
        #              break
        #      minCodeV = funcOffset+funcAmp-(iEnd-iPeak)/nSamplesPeriod*funcAmp*4
        #      minCodes.append(minCode)
        #      minCodeVs.append(minCodeV)
        #      cleanWaveform.extend(waveform[iStart:iEnd+1])

        ##print(minCodes)
        ##print(minCodeVs)
        #minCode = numpy.mean(minCodes)
        #minCodeVs = numpy.mean(minCodeVs)
        ##print(minCode,minCodeV,funcOffset,funcAmp,nSamplesPeriod)

        ##fig, ax = plt.subplots()
        ##ax.plot(cleanWaveform)
        ##plt.show()

        #return numpy.array(cleanWaveform), minCode, minCodeV, firstMax, maxCodeV
        
def main():
    from ...configuration.argument_parser import ArgumentParser
    ROOT.gROOT.SetBatch(True)
    parser = ArgumentParser(description="Calibrates ADC ramp data")
    parser.add_argument("infilename",help="Input file name. The file created by femb_adc_collect_data that includes 'functype3'.")
    args = parser.parse_args()
  
    cal_ramp = CALIBRATE_RAMP(args.infilename)
    cal_ramp.write_calibrate_tree()
