from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from builtins import range
from builtins import int
from future import standard_library
standard_library.install_aliases()
from builtins import object
import string
import ROOT
#from ROOT import TFile, TTree
from array import array
from .femb_udp import FEMB_UDP
import uuid
import datetime
import time
import sys

class WRITE_ROOT_TREE(object):

    def __init__(self,femb_config,iChip,filename,numpacketsrecord,highSpeed=False,packedHighSpeed=False):
    #data taking variables
        if iChip >= femb_config.NASICS:
            print("Error WRITE_ROOT_TREE: iChip >= NASICS")
            sys.exit(1)

        self.numpacketsrecord = numpacketsrecord
        self.highSpeed = highSpeed
        self.packedHighSpeed = packedHighSpeed
        #file name and metadata variables
        self.filename = filename
        self.treename = 'femb_wfdata'
        self.metaname = 'metadata'
        self.date = int( datetime.datetime.today().strftime('%Y%m%d%H%M') )
        self.iChip = iChip
        self.adcSerial = -1
        self.feSerial = -1
        runid = uuid.uuid4()
        self.runidMSB = ( (runid.int >> 64) & 0xFFFFFFFFFFFFFFFF )
        self.runidLSB = ( runid.int & 0xFFFFFFFFFFFFFFFF)
        self.run = 0
        self.subrun = 0
        self.runtype = 0
        self.runversion = 0
        self.par1 = 0
        self.par2 = 0
        self.par3 = 0
        self.gain = 0
        self.shape = 0
        self.base = 0
        self.adcOffset = -2 # -2 undefined, -1 off, 0-15 on with various values
        self.adcClock = -1 # -1 undefined, 0 external, 1 internal monostable, 2 internal FIFO
        self.sampleRate = -1. # Hz, -1 undefined.
        # func generator
        self.funcType = 0 # 0 means not active, 1 constant, 2 sin, 3 ramp
        self.funcFreq = 0.
        self.funcOffset = 0.
        self.funcAmp = 0.
        #initialize FEMB UDP object
        self.femb = FEMB_UDP()
        self.femb_config = femb_config

    def record_data_run(self):
        f = ROOT.TFile( self.filename, 'recreate' )
        t = ROOT.TTree( self.treename, 'wfdata' )

        chan = array( 'I', [0])
        wf = ROOT.std.vector( int )()
        t.Branch( 'chan', chan, 'chan/i')
        t.Branch( 'wf', wf )
        self.femb.MAX_NUM_PACKETS = 7200
        npackets = min(self.femb.MAX_NUM_PACKETS,self.numpacketsrecord)
        if self.highSpeed:
            self.femb_config.selectChannel( self.iChip, 0, hsmode=0) # all channels at once
            time.sleep(0.01)
            data = self.femb.get_data(npackets)
            for ch in range(16):
                chan[0] = int(ch)
                wf.clear()
                samples = None
                if self.packedHighSpeed:
                    samples = self.convertHighSpeedSimple(data)
                else:
                    samples = self.convertHighSpeedPacked(data)
                for samp in samples[ch]:
                    wf.push_back( samp )
                t.Fill()
        else:
            for ch in range(16):
                chan[0] = int(ch)
                self.femb_config.selectChannel( self.iChip, ch)
                time.sleep(0.01)
                wf.clear()
                data = self.femb.get_data(npackets)
                for samp in data:
                    chNum = ((samp >> 12 ) & 0xF)
                    sampVal = (samp & 0xFFF)
                    wf.push_back( sampVal )
                t.Fill()

        #define metadata
        _date = array( 'L' , [self.date] )
        _iChip = array( 'L' , [self.iChip] )
        _adcSerial = ROOT.std.string(self.adcSerial)
        _feSerial = array( 'l' , [self.feSerial] )
        _runidMSB = array( 'L', [self.runidMSB] )
        _runidLSB = array( 'L', [self.runidLSB] )
        _run = array( 'L', [self.run] )
        _subrun = array( 'L', [self.subrun] )
        _runtype = array( 'L', [self.runtype] )
        _runversion = array( 'L', [self.runversion] )
        _par1 = array( 'd', [self.par1] )
        _par2 = array( 'd', [self.par2] )
        _par3 = array( 'd', [self.par3] )
        _gain = array( 'H', [self.gain] )
        _shape = array( 'H', [self.shape] )
        _base = array( 'H', [self.base] )
        _adcOffset = array( 'h', [self.adcOffset] )
        _adcClock = array( 'h', [self.adcClock] )
        _sampleRate = array( 'f', [self.sampleRate] )
        _funcType = array( 'H', [self.funcType] )
        _funcAmp = array( 'f', [self.funcAmp] )
        _funcOffset = array( 'f', [self.funcOffset] )
        _funcFreq = array( 'f', [self.funcFreq] )
        metatree = ROOT.TTree( self.metaname, 'metadata' )
        metatree.Branch( 'date', _date, 'date/l')
        metatree.Branch( 'iChip', _iChip, 'iChip/l')
        metatree.Branch( 'adcSerial', _adcSerial)
        metatree.Branch( 'feSerial', _feSerial, 'feSerial/L')
        metatree.Branch( 'runidMSB', _runidMSB, 'runidMSB/l')
        metatree.Branch( 'runidLSB', _runidLSB, 'runidLSB/l')
        metatree.Branch( 'run', _run, 'run/l')
        metatree.Branch( 'subrun', _subrun, 'subrun/l')
        metatree.Branch( 'runtype', _runtype, 'runtype/l')
        metatree.Branch( 'runversion', _runversion, 'runversion/l')
        metatree.Branch( 'par1', _par1, 'par1/D')
        metatree.Branch( 'par2', _par2, 'par2/D')
        metatree.Branch( 'par3', _par3, 'par3/D')
        metatree.Branch( 'gain',_gain, 'gain/s')
        metatree.Branch( 'shape',_shape, 'shape/s')
        metatree.Branch( 'base',_base, 'base/s')
        metatree.Branch( 'adcOffset',_adcOffset, 'adcOffset/S')
        metatree.Branch( 'adcClock',_adcClock, 'adcClock/S')
        metatree.Branch( 'sampleRate',_sampleRate, 'sampleRate/F')
        metatree.Branch( 'funcType',_funcType, 'funcType/s')
        metatree.Branch( 'funcAmp',_funcAmp, 'funcAmp/F')
        metatree.Branch( 'funcOffset',_funcOffset, 'funcOffset/F')
        metatree.Branch( 'funcFreq',_funcFreq, 'funcFreq/F')
        metatree.Fill()

        f.Write()
        f.Close()

    def convertHighSpeedSimple(self,data):
        result = [[] for chan in range(16)]
        for samp in data:
            chNum = ((samp >> 12 ) & 0xF)
            sampVal = (samp & 0xFFF)
            result[chNum].append(sampVal)
        return result

    def convertHighSpeedPacked(self,data):
        packetNum = 0
        wordArray = []
        result = [[] for chan in range(16)]
        for word in data:
            #print(str(packetNum) + "\t" + str(hex(word)) )
            if str(hex(word)) == "0xface" :
              packetNum = 0
              wordArray = []
            if packetNum > 0 and packetNum < 13 :
              wordArray.append( word )
            if packetNum == 12 :
              result[0].append(((wordArray[5] & 0xFFF0 ) >> 4))
              result[1].append(((wordArray[4] & 0xFF00 ) >> 8) | ((wordArray[5] & 0x000F ) << 8))
              result[2].append(((wordArray[4] & 0x00FF ) << 4) | ((wordArray[3] & 0xF000 ) >> 12))
              result[3].append(((wordArray[3] & 0x0FFF ) >> 0))
              result[4].append(((wordArray[2] & 0xFFF0 ) >> 4))
              result[5].append(((wordArray[2] & 0x000F ) << 8) | ((wordArray[1] & 0xFF00 ) >> 8))
              result[6].append(((wordArray[1] & 0x00FF ) << 4) | ((wordArray[0] & 0xF000 ) >> 12))
              result[7].append(((wordArray[0] & 0x0FFF ) >> 0)				)
              result[8].append(((wordArray[11] & 0xFFF0 ) >> 4))
              result[9].append(((wordArray[11] & 0x000F ) << 8) | ((wordArray[10] & 0xFF00 ) >> 8))
              result[10].append(((wordArray[10] & 0x00FF ) << 4) | ((wordArray[9] & 0xF000 ) >> 12))
              result[11].append(((wordArray[9] & 0x0FFF )))
              result[12].append(((wordArray[8] & 0xFFF0 ) >> 4))
              result[13].append(((wordArray[8] & 0x000F ) << 8) | ((wordArray[7] & 0xFF00 ) >> 8))
              result[14].append(((wordArray[7] & 0x00FF ) << 4) | ((wordArray[6] & 0xF000 ) >> 12))
              result[15].append(((wordArray[6] & 0x0FFF ) ))
            packetNum = packetNum + 1
        return result

def main():
  from .configuration.argument_parser import ArgumentParser
  from .configuration import CONFIG
  parser = ArgumentParser(description="Dumps data to a root tree named 'femb_wfdata'")
  parser.addNPacketsArgs(False,10)
  parser.add_argument("chip_number",help="ADC chip number to read out",type=int)
  parser.add_argument("outfilename",help="Output root file name")
  parser.add_argument("-p", "--profiler",help="Enable python timing profiler and save to given file name",type=str,default=None)
  parser.add_argument("-f","--highSpeed",help="High Speed data readout mode",action="store_true")
  args = parser.parse_args()

  config = CONFIG()

  wrt = WRITE_ROOT_TREE(config,args.chip_number,args.outfilename,args.nPackets,highSpeed=args.highSpeed)
  if args.profiler:
      import cProfile
      cProfile.runctx('wrt.record_data_run()',globals(),locals(),args.profiler)
  else:
      wrt.record_data_run()
