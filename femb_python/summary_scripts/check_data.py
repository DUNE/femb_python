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
from dateutil.relativedelta import relativedelta, MO

class FEMB_CHECK_DATA(object):

  def __init__(self):
    self.status_read_args = 0
    self.status_get_data = 0
    self.datapath = "/dsk/1/data/sync-json/"
    self.what = None
    self.when = None
    self.verbose = False

  def readargs(self, what=None, when=None, verbose=False):

    print("Read arguments")

    supported_what = ["adc_cold", "osc", "femb","fe_warm","femb","flash"]
    supported_when = ["today", "yesterday", "this_week", "all"]

    if what.lower() in supported_what:
      self.what = what.lower()
    else:
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
        waiting = True
        while waiting:
          print ("Please enter time range to search (",supported_when,"):")
          userwhen = input()
          if userwhen.lower() in supported_when:
            waiting = False
            self.when = userwhen

    self.verbose = verbose
    self.status_read_args = 1
  
  def getdata(self):
    now = time.time()
    tsnow = time.strftime("%Y%m%dT%H%M%S", time.localtime(now))
    whatdirs = []

    if ("adc_cold" in self.what):
      search_dir = self.datapath+"hoth*/dsk/*/oper/adcasic/*cold*/*"

    elif("adc_warm" in self.what):
      search_dir = self.datapath+"hoth*/dsk/*/oper/adcasic/*single/*"

    if ("fe_cold" in self.what):
      search_dir = self.datapath+"hoth*/dsk/*/oper/feasic/quadFeAsic_cold/*"

    elif("fe_warm" in self.what):
      search_dir = self.datapath+"hoth*/dsk/*/oper/feasic/quadFeAsic/*"
      
    elif("osc" in self.what):
      search_dir = self.datapath+"hoth*/dsk/*/oper/osc/osc/*"

    elif("flash" in self.what):
      search_dir = self.datapath+"hoth*/dsk/*/oper/FlashTesting/quadEpcsTester*/*"
      
    elif("femb" in self.what):
      search_dir = self.datapath+"hoth*/dsk/*/oper/femb/wib_sbnd_v109_femb_protodune_v308/*"
      
    whatdirs = glob.glob(search_dir)

    search_time_upper = "20301231"
    if ("today" in self.when):
      search_time = tsnow[0:8]
    elif("yesterday" in self.when):
      search_date = datetime.datetime(int(tsnow[0:4]), int(tsnow[4:6]), int(tsnow[6:8])) + relativedelta(days=-1)
      search_month = str(search_date.month).zfill(2)
      search_day = str(search_date.day).zfill(2)
      search_time = tsnow[0:4]+search_month+search_day
      search_time_upper = tsnow[0:8]
    elif("this_week" in self.when):
      search_date = datetime.datetime(int(tsnow[0:4]), int(tsnow[4:6]), int(tsnow[6:8])) + relativedelta(weekday=MO(-1))
      search_month = str(search_date.month).zfill(2)
      search_day = str(search_date.day).zfill(2)
      search_time = tsnow[0:4]+search_month+search_day
    elif("all" in self.when):
      search_time = "20170101"

    directories_found = []
    for dir in whatdirs:
      date_of_this_dir = dir[-15:].split("T")[0]
      if ((datetime.datetime(int(date_of_this_dir[0:4]),
                             int(date_of_this_dir[4:6]),
                             int(date_of_this_dir[6:8])) >=
           datetime.datetime(int(search_time[0:4]),
                             int(search_time[4:6]),
                             int(search_time[6:8]))) and
          (datetime.datetime(int(date_of_this_dir[0:4]),
                             int(date_of_this_dir[4:6]),
                             int(date_of_this_dir[6:8])) <
           datetime.datetime(int(search_time_upper[0:4]),
                             int(search_time_upper[4:6]),
                             int(search_time_upper[6:8])))):
        directories_found.append(dir)

    if "femb" in self.what:
      useful_directories = []
      boxes_tested_rt = []
      boxes_tested_ct = []
      ct_dirs = {}
      rt_dirs = {}
      for dir in directories_found:
        subdirs = glob.glob(dir+"/*")
        if len(subdirs)==20:
          useful_directories.append(dir)
          params_file = dir+"/fembTest_summary/params.json"
          if os.path.isfile(params_file):
            params = json.loads(open(params_file).read())
            isRoomTemp = params['isRoomTemp']
            boxids = params['box_ids']
            for box in boxids:
              if (isRoomTemp):
                boxes_tested_rt.append(box)
                rt_dirs[box] = dir
              else:
                boxes_tested_ct.append(box)
                ct_dirs[box] = dir
      print("***Number of tests completed ("+self.when+"): ", len(useful_directories))
      boxes_tested_rt_excl = sorted(list(set(boxes_tested_rt)))
      boxes_tested_ct_excl = sorted(list(set(boxes_tested_ct)))
      print("***",len(boxes_tested_rt_excl)," Boxes Fully Tested RT: ", boxes_tested_rt_excl)
      print("***",len(boxes_tested_ct_excl)," Boxes Fully Tested CT: ", boxes_tested_ct_excl)
      if self.verbose:
        print("Directories (RT): ")
        for mykey,dir in rt_dirs.items(): print("Box ",mykey, ": ",dir)
        print("Directories (CT): ")
        for mykey,dir in ct_dirs.items(): print("Box ",mykey, ": ",dir)

        
    if "osc" in self.what:
      useful_directories = []
      for dir in directories_found:
        subdirs = glob.glob(dir+"/*")
        if "OscillatorTestingSummary" in [os.path.basename(x) for x in subdirs]:
          useful_directories.append(dir)
      print("***Number of tests ("+self.when+"): ", len(useful_directories))
      if self.verbose:
        print("Directories: ", useful_directories)

    if "flash" in self.what:
      useful_directories = []
      npass = 0
      for dir in directories_found:
        results_file = dir+"/QuadEpcsTester/QuadEpcsTester.json"
        if os.path.isfile(results_file):
          useful_directories.append(dir)
          #results = json.load(open(results_file).read())
          #passlist = results["Passed? : "]
          #for test in passlist:
            #if test: npass+=1
      print("***Number of tests ("+self.when+"): ", len(useful_directories))
      #print("***Number of flash qualified: ", npass)
      if self.verbose:
        print("Directories: ", useful_directories)
        
    if "femb" in self.what:
      useful_directories = {}
      chips_tested = []
      chips_daonly = []

    if "fe_warm" in self.what:
      useful_directories = []
      chips_tested = []
      for dir in directories_found:
        tests = glob.glob(dir+"/gain_enc_sequence*")
        for test in tests:
          if "sequence-g2s2b0" in test:
            params_file = test+"/params.json"
            if os.path.isfile(params_file):
              params = json.loads(open(params_file).read())
              for iasic in range(0,4):
                if "asic"+str(iasic)+"id" in params:
                  chips_tested.append(params["asic"+str(iasic)+"id"])
              useful_directories.append(dir)
      #chips_tested_excl = sorted(list(set(chips_tested)),key=lambda x:int(x))
      chips_tested_excl = list(set(chips_tested))
      print("***Number of tests completed ("+self.when+"): ", len(useful_directories), " (4 chips per test)")
      print("***",len(chips_tested_excl)," Chips Fully Tested: :", chips_tested_excl)
      
    if "adc_cold" in self.what:
      useful_directories = {}
      chips_tested = []
      chips_daonly = []
      for dir in directories_found:
        setup_file = glob.glob(dir+"/adcTest_*.json")
        if setup_file:
          setup_file = setup_file[0]
          if os.path.isfile(setup_file):
            params = json.loads(open(setup_file).read())
            chips_tested.append(params['serial'])
            useful_directories[params['serial']] = dir
        else:
          setup_file_daonly = glob.glob(dir+"/david_adams_only*.json")
          if setup_file_daonly:
            setup_file_daonly = setup_file_daonly[0]
            if os.path.isfile(setup_file_daonly):
              params = json.loads(open(setup_file_daonly).read())
              chips_daonly.append(params['serials'][0])
              useful_directories[params['serials'][0]] = dir                                 
              
      chips_tested_full = list(set(chips_tested))
      chips_tested_daonly = list(set(chips_daonly))
      print("***Number of tests started ("+self.when+"): ", len(directories_found), "\n")
      print("***",len(chips_tested_full)," Chips Fully Tested: ", chips_tested_full, "\n")
      print("***",len(chips_tested_daonly)," Chips w/ Only DA Data Attempted: ", chips_tested_daonly, "\n")
      if self.verbose:
        print("Directories: ")
        for mykey,dir in useful_directories.items(): print(mykey, dir)

    self.status_get_data = 1

    

def main():

  if len(sys.argv)>1:
    what = sys.argv[1]
  else:
    what = ""

  if len(sys.argv)>2:
    when = sys.argv[2]
  else:
    when = ""

  if len(sys.argv)>3:
    verbose = True
  else:
    verbose = ""

    host = os.uname()[1]
    if not ("hothstor2" in host):
      print("Running on "+host+" -- you must be logged in to hothstor2")
      return
    
    
  doit = FEMB_CHECK_DATA()
  doit.readargs(what, when, verbose)
  doit.getdata()
  

if __name__ == '__main__':
        main()
