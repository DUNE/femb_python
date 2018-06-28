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
import xml.dom.minidom as MD
from dateutil.relativedelta import relativedelta, MO

from femb_python.configuration import CONFIG

class CONFIG_FEMB_SBND(object):

  def __init__(self):
    self.xmlshapingtimeval = 0
    self.xmlgainval = 0
    self.configshapingtimeval = 0
    self.configgainval = 0
    self.femb_config = CONFIG()
    self.feasicLeakage = self.femb_config.feasicLeakage
    self.feasicLeakagex10 = self.femb_config.feasicLeakagex10
    self.feasicAcdc = self.femb_config.feasicAcdc
    self.feasicBaseline = self.femb_config.feasicBaseline
    self.feasicEnableTestInput = self.femb_config.feasicEnableTestInput
    self.feasicGain = self.femb_config.feasicGain
    self.feasicShape = self.femb_config.feasicShape
    self.feasicBuf = self.femb_config.feasicBuf
    self.femb_config.useLArIATmap = True
    
  def readin(self,xmlin):
    #reading in from xml file
    tree = ET.parse(xmlin)
    root = tree.getroot()
    for Gain in root.iter('Gain'):
        self.xmlgainval = float(Gain.text)
        if self.xmlgainval == 4.7:
          self.configgainval = 0
        elif self.xmlgainval == 7.8:
          self.configgainval = 2
        elif self.xmlgainval == 14:
          self.configgainval = 1
        else:
          self.configgainval = 3
        if self.xmlgainval not in (4.7, 7.8, 14, 25):
            raise ValueError("Invalid gain value in XML file.")
            return
    for ShapingTime in root.iter('ShapingTime'):
        self.xmlshapingtimeval = float(ShapingTime.text)
        if self.xmlshapingtimeval == 0.5:
          configshapingtimeval = 2
        elif self.xmlshapingtimeval == 1:
          configshapingtimeval = 0
        elif self.xmlshapingtimeval == 2:
          configshapingtimeval = 3
        else:
          configshapingtimeval = 1
        if self.xmlshapingtimeval not in (0.5, 1, 2, 3):
            raise ValueError("Invalid shaping time value in XML file.")
            return
    print("Finished reading xml file: ", xmlin)


  def doconfig(self):
    self.femb_config.feasicShape = self.configshapingtimeval
    self.femb_config.feasicGain = self.configgainval


    for wib in range(0,2):
      self.wibNum = wib
      self.femb_config.initWib()      
      if wib==0:
        for femb in range(0,1):
          self.femb_config.fembNum = femb

          #Dummy for testing at BNL
          self.femb_config.fembNum = 1

          self.femb_config.initFemb()
      elif wib==1:
        self.femb_config.fembNum = 4 #Only one femb on WIB#1
        self.femb_config.initFemb()
        
    print("Finished configuring CE")
    return

  def indent(self, elem, level=0):
    i = "\n" + level*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            self.indent(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i
  
  def writeout(self):
    now = time.time()
    tsnow = str(time.strftime("%Y%m%dT%H%M%S", time.localtime(now)))
    
    #tree structure for xml file
    root = ET.Element("ASICSettings")
    
    gain = ET.SubElement(root, "Gain").text = str(self.xmlgainval)
    shaping_time = ET.SubElement(root, "Shaping_Time").text = str(self.xmlshapingtimeval)

    #Convert remaining indices to real settings:
    if self.feasicLeakage == 0:
      feLeakage = 0.5
    else:
      feLeakage = 0.1
    if self.feasicLeakagex10 == 1:
      feLeakage = feleakage*10
    FEasicleakage = ET.SubElement(root, "FE-ASIC_Leakage").text = str(feLeakage)+"nA"

    if self.feasicAcdc == 0:
      acdc = "AC"
    else:
      acdc = "DC"
    FEasicacdc = ET.SubElement(root, "FE-ASIC_ACDC").text = acdc

    if self.feasicEnableTestInput == 0:
      testin = "Disabled"
    else:
      testin = "Enabled"
    FEsaictestinput = ET.SubElement(root, "FE-ASIC_testinput").text = testin

    if self.feasicBuf == 0:
      buffer = "Off"
    else:
      buffer = "On"
    FEasicbuffer = ET.SubElement(root, "FE_ASIC_buffer").text = buffer
    timestamp = ET.SubElement(root, "Timestamp").text = tsnow

    #formatting tree
    self.indent(root)
    tree = ET.ElementTree(root)
    sbndpath = "/sbnd/data/ce_config/"
    fileout = "ASICSettings_"+tsnow+".xml"
    try:
      tree.write(sbndpath+fileout, encoding='unicode')
      print("Finished writing xml file: ", sbndpath+fileout)
    except:
      tree.write(fileout, encoding='unicode')
      print("Finished writing xml file: ", fileout)

      
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

        
        
