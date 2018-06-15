#!/usr/bin/python3.4
from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import
from builtins import int
from builtins import str
from future import standard_library
standard_library.install_aliases()
import sys
import time
import glob
import os
import json
import datetime
import xml.etree.cElementTree as ET
from dateutil.relativedelta import relativedelta, MO

from femb_python.configuration import CONFIG

# Copied from summary_scripts
# Will be totally overhauled to write configuration scripts
# Steps for configuration
# 1. Read in desired gain/shaping time from xml script
# 2. Configure all WIBs/Boards/Chips with desired settings (globally set everything the same right now)
# 3. Write out xml file with timestamp and all settings
# Once this is done, also set up an executable to configure only single channels at a time

class CONFIG_FEMB_SBND(object):

  def __init__(self):
    self.xmlshapingtimeval = 0
    self.xmlgainval = 0
    self.configshapingtimeval = 0
    self.configgainval = 0
    self.femb_config = CONFIG()
    
  def readin(self,xmlin):
    #reading in from xml file
    tree = ET.parse(xmlin)
    root = tree.getroot()
    for Gain in root.iter('Gain'):
        self.xmlgainval = float(Gain.text)
        if self.xmlgainval == 4.7:
          self.configgainval = 0
        elif self.xmlgainval = 7.8:
          self.configgainval = 1
        elif self.xmlgainval = 14:
          self.configgainval = 2
        else:
          self.configgainval = 3
        if self.inputgainval not in (4.7, 7.8, 14, 25):
            raise ValueError("Invalid gain value in XML file.")
            return
    for ShapingTime in root.iter('ShapingTime'):
        self.xmlshapingtimeval = float(ShapingTime.text)
        if xmlshapingtimeval = 0.5:
          configshapingtimeval = 0
        elif xmlshapingval = 1:
          configshapingtimeval = 1
        elif xmlshapingtimeval = 2:
          configshapingtimeval = 2
        else:
          configshapingtimeval = 3
        if self.xmlshapingtimeval not in (0.5, 1, 2, 3):
            raise ValueError("Invalid shaping time value in XML file.")
            return
    print("Finished reading xml file: ", xmlin)


  def doconfig(self):
    self.femb_config.feasicShape = self.configshapingtimeval
    self.femb_config.feasicGain = self.configgainval
    self.femb_config.initWib()
    self.femb_config.initFemb()
    
    print("Finished configuring CE")
    return

  def writeout(self):
    now = time.time()
    tsnow = str(time.strftime("%Y%m%dT%H%M%S", time.localtime(now)))
    
    #tree structure for xml file
    root = ET.Element("Current Settings")
    
    gain = ET.SubElement(root, "Gain").text = str(self.xmlgainval)
    shaping_time = ET.SubElement(root, "Shaping Time").text = str(self.xmlshapingtimeval)
    FEasicleakage = ET.SubElement(root, "FE-ASIC Leakage").text = #str(self.feasicLeakage)
    FEasicleakagex10 = ET.SubElement(root, "FE-ASIC Leakagex10").text = #str(self.feasicLeakagex10)
    FEasicacdc = ET.SubElement(root, "FE-ASIC AC/DC").text = #str(self.feasicAcdc)
    FEsaictestinput = ET.SubElement(root, "FE-ASIC test input").text = #str(self.feasicEnableTestInput)
    FEasicbaseline = ET.SubElement(root, "FE-ASIC Baseline").text = #str(self.feasicBaseline)
    FEasicbuffer = ET.SubElement(root, "FE_ASIC buffer").text = #str(self.feasicBuf)
    timestamp = ET.SubElement(root, "Timestamp").text = tsnow

    tree = ET.ElementTree(root)
    tree.write(tsnow + 'TestSettings.xml')
    print("Finished writing xml file: ","TestSettings.xml") 
      
def main():

  if len(sys.argv)>1:
    xmlin = sys.argv[1]
  else:
    print("Must provide path to xml file")
    return

  myconfig = CONFIG_FEMB_SBND()
  myconfig.readin(xmlin)
  myconfig.doconfig()
  myconfig.writeout()
  return
    

if __name__ == '__main__':
        main()

        
        
