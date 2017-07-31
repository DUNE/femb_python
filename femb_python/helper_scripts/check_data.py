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
import datetime
from dateutil.relativedelta import relativedelta, MO

class FEMB_CHECK_DATA(object):

  def __init__(self):
    self.status_read_args = 0
    self.status_get_data = 0
    self.datapath = "/dsk/1/data/sync-json/"
    self.what = None
    self.when = None
    self.verbose = True

  def readargs(self, what=None, when=None, verbose=False):
    print("Read arguments")

    supported_what = ["adc_cold","adc_warm","fe_cold","fe_warm","osc"]
    supported_when = ["today", "this_week", "all"]

    if what.lower() in supported_what:
      self.what = what.lower()
    else:
      print("in here")
      waiting = True
      while waiting:
        print ("Please enter test to search (",supported_what,"):")
        userwhat = input()
        if userwhat.lower() in supported_what:
          waiting = False
          self.what = userwhat

    if when.lower() in supported_when:
      self.when = when.lower()
    else:
        print("in here")
        waiting = True
        while waiting:
          print ("Please enter time range to search (",supported_when,"):")
          userwhen = input()
          if userwhen.lower() in supported_when:
            waiting = False
            self.when = userwhen

    if verbose:
      self.Verbose = True
    
    self.status_read_args = 1
  
  def getdata(self):
    print("Get data")
    now = time.time()
    tsnow = time.strftime("%Y%m%dT%H%M%S", time.localtime(now))
    whatdirs = []

    if ("adc_cold" in self.what):
      search_dir = self.datapath+"hothdaq*/dsk/*/oper/adcasic/*cold*/*"

    elif("adc_warm" in self.what):
      search_dir = self.datapath+"hothdaq*/dsk/*/oper/adcasic/*single/*"

    if ("fe_cold" in self.what):
      search_dir = self.datapath+"hothdaq*/dsk/*/oper/feasic/quadFeAsic_cold/*"

    elif("fe_warm" in self.what):
      search_dir = self.datapath+"hothdaq*/dsk/*/oper/feasic/quadFeAsic/*"
      #print(search_dir)
      
    elif("osc" in self.what):
      search_dir = self.datapath+"hothdaq*/dsk/*/oper/osc/osc/*"
      
    whatdirs = glob.glob(search_dir)

    if ("today" in self.when):
      search_time = tsnow[0:8]
    elif("this_week" in self.when):
      search_day = (datetime.datetime(int(tsnow[0:4]), int(tsnow[4:6]), int(tsnow[6:8])) + relativedelta(weekday=MO(-1))).day
      search_time = tsnow[0:4]+tsnow[4:6]+str(search_day)
    elif("all" in self.when):
      search_time = "20170101"

    directories_found = []
    for dir in whatdirs:
      date_of_this_dir = dir[-15:].split("T")[0]
      if (datetime.datetime(int(date_of_this_dir[0:4]), int(date_of_this_dir[4:6]), int(date_of_this_dir[6:8])) >=
                            datetime.datetime(int(search_time[0:4]), int(search_time[4:6]), int(search_time[6:8]))):
        directories_found.append(dir)

    print(directories_found)
    if self.Verbose:
      for dir in directories_found: print(dir)
    print("Number of tests ("+self.when+"): ", len(directories_found))
    self.status_get_data = 1

def main():
  doit = FEMB_CHECK_DATA()
  doit.readargs("", "", "False")
  doit.getdata()
  

if __name__ == '__main__':
        main()
