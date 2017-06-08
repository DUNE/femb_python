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
import array
import numpy
import numpy.linalg
import ROOT

class CALIBRATE_RAMP(object):
    """
    Calibrates ADC ramp data--finds the voltage for each ADC sample
    """

    def __init__(self,infilename,samplingFreq,dcCalibrationFiles=[]):
        self.infilename = infilename
        self.dcCalibrationFiles = dcCalibrationFiles
        self.outfilename = os.path.splitext(infilename)[0]+"_calib.root"
        self.samplingFreq = samplingFreq

    def write_calibrate_tree(self):
        f = ROOT.TFile(self.infilename)

        metadataTree = f.Get("metadata")
        metadataTree.GetEntry(0)
        funcType = metadataTree.funcType
        frequency = metadataTree.funcFreq
        offset = metadataTree.funcOffset
        amplitude = metadataTree.funcAmp
        if funcType != 3:
            print("Calibration error: file not ramp data",file=sys.stderr)
            sys.exit(1)
        intree = f.Get("femb_wfdata")
        #print("Creating file: ",self.outfilename,file=sys.stderr)
        fout = ROOT.TFile( self.outfilename, 'recreate' )
        fout.cd()
        outmetadataTree = metadataTree.CloneTree()
        outtree = intree.CloneTree()

        wfBranch = outtree.GetBranch("wf")
        voltage = ROOT.std.vector( float )()
        voltageBranch = outtree.Branch( 'voltage', voltage )

        calibrationTree = ROOT.TTree("calibration","calibration information")
        voltsPerADCArray = array.array('d',[0.])
        voltsInterceptArray = array.array('d',[0.])
        calibrationTree.Branch( 'voltsPerADC', voltsPerADCArray, 'voltsPerADC/D')
        calibrationTree.Branch( 'voltsIntercept', voltsInterceptArray, 'voltsIntercept/D')

        for iEntry in range(outtree.GetEntries()):
            outtree.GetEntry(iEntry)
            waveform = numpy.array(list(outtree.wf))
            voltage.resize(len(waveform))
            slope, intercept = self.doCalibration(waveform,voltage,frequency,offset,amplitude)
            voltageBranch.Fill()
            voltsPerADCArray[0] = slope
            voltsInterceptArray[0] = intercept
            calibrationTree.Fill()

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
            iStopLook = min(iStopLook,len(waveform))
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
            if iStart is None:
                continue
            if iStop is None:
                continue
            iPeak = 0.5*(iStart + iStop)
            iPeaks.append(iPeak)
        iPeaks = numpy.array(iPeaks)
        iAvgPeak = numpy.mean(iPeaks % nSamplesPeriod)
        slopePos = 4.*funcAmp/nSamplesPeriod
        for iSample in range(len(waveform)):
            iShiftedSample = iSample - iAvgPeak# + 4*nSamplesPeriod # keep iSample > 0
            #iShiftedSample = iSample
            xintercept = ((iShiftedSample // nSamplesPeriod) + 0.75)*nSamplesPeriod
            slope = slopePos
            if (float(iShiftedSample) % nSamplesPeriod) < 0.5*nSamplesPeriod:
                slope = -slopePos
                xintercept -= 0.5*nSamplesPeriod
            yintercept = - slope * xintercept
            voltage[iSample] = slope*iShiftedSample + yintercept + funcOffset
            #print(iSample,iShiftedSample,waveform[iSample],voltage[iSample],xintercept,yintercept)

        voltages = numpy.array(voltage)
        goodOnes = voltages > 0.2
        goodOnes = numpy.logical_and(voltages < 1.2, goodOnes)
        goodOnes = numpy.logical_and(waveform > 400, goodOnes)
        goodOnes = numpy.logical_and(waveform < 4000, goodOnes)
        waveformLast6Bits = waveform & 0b111111
        goodOnes = numpy.logical_and(waveformLast6Bits != 0b111111,goodOnes)
        goodOnes = numpy.logical_and(waveformLast6Bits != 0,goodOnes)
        voltages = voltages[goodOnes]
        samples = waveform[goodOnes]
        A = numpy.vstack([samples, numpy.ones(len(samples))]).T
        parameters, residuals, rank, s = numpy.linalg.lstsq(A,voltages)

        #from matplotlib import pyplot as plt
        #fig, ax = plt.subplots()
        #ax.plot(waveform)
        #ax.plot(numpy.array(list(voltage))/parameters[0]-parameters[1]/parameters[0])
        #axRight = ax.twinx()
        #axRight.set_ylim(numpy.array(ax.get_ylim())*parameters[0]+parameters[1])
        #plt.show()

        return parameters[0], parameters[1]
        
def main():
    from ...configuration.argument_parser import ArgumentParser
    from ...configuration import CONFIG

    ROOT.gROOT.SetBatch(True)
    parser = ArgumentParser(description="Calibrates ADC ramp data")
    parser.add_argument("infilename",help="Input file name. The file created by femb_adc_collect_data that includes 'functype3'.")
    parser.add_argument("DCcalibrationfile",help="DC calibration file names. These files are created by femb_adc_collect_data and include 'functype1'.",nargs="*")
    args = parser.parse_args()

    config = CONFIG()

    cal_ramp = CALIBRATE_RAMP(args.infilename,config.SAMPLERATE,args.DCcalibrationfile)
    cal_ramp.write_calibrate_tree()
