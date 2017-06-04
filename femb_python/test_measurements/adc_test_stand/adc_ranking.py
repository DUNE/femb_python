"""
Code for ranking ADCs. More generally analyzing multiple summary json files
produced in ADC tests.
"""

from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals
from __future__ import absolute_import
from builtins import range
from future import standard_library
standard_library.install_aliases()
import os
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

class ADC_RANKING(object):

    def __init__(self,inglobstr):
        """
        inglobstr is a string that can be parsed by glob to make a list of
        directories containing json files or json files to be analyzed.
        Directories found in the glob will be walked to find subdirectories 
        containing json files.
        """
        inpathlist = glob.glob(inglobstr)
        jsonpaths = []
        for inpath in inpathlist:
            for directory, subdirs, filenames in os.walk(inpath):
                for filename in filenames:
                    if os.path.splitext(filename)[1] == ".json" and "adcTest" == filename[:7] and not ("Raw" in filename):
                        jsonpath = os.path.join(directory,filename)
                        jsonpaths.append(jsonpath)
                        print(jsonpath)
        datadicts = []
        for jsonpath in jsonpaths:
            with open(jsonpath) as jsonfile:
                datadict = json.load(jsonfile)
                datadicts.append(datadict)
        self.datadicts = datadicts

    def rank(self):
        datadicts = self.getlatestdata()
        stats = {}
        for datadict in datadicts:
            serial = datadict["serial"]
            print(serial)
            static = datadict["static"]
            dynamic = datadict["dynamic"]
            inputPin = None
            dc = None
            try:
                inputPin = datadict["inputPin"]
            except KeyError:
                print("Warning: now input pin stats for chip",serial)
            try:
                dc = datadict["dc"]
            except KeyError:
                print("Warning: now input pin stats for chip",serial)

    def getlatestdata(self):
        """
        Returns list of data dicts, only the 
        latest timesamped one per serial.
        """
        datadicts = self.datadicts
        #for datadict in datadicts:
        #    print(datadict["serial"],datadict["timestamp"])
        resultdict = {} # key is serial, value is datadict
        for datadict in datadicts:
            serial = datadict["serial"]
            try:
                olddata = resultdict[serial]
            except KeyError:
                resultdict[serial] = datadict
            else:
                oldtimestamp = olddata["timestamp"]
                newtimestamp = datadict["timestamp"]
                oldtimestamp = datetime.datetime.strptime(oldtimestamp,"%Y-%m-%dT%H:%M:%S")
                newtimestamp = datetime.datetime.strptime(newtimestamp,"%Y-%m-%dT%H:%M:%S")
                if newtimestamp > oldtimestamp:
                  resultdict[serial] = datadict
        #print("result:")
        sortedserials = None
        try:
            sortedserials = sorted(resultdict,key=lambda x: int(x))
        except:
            sortedserials = sorted(resultdict)
        result = []
        for serial in sortedserials:
            datadict = resultdict[serial]
        #    print(datadict["serial"],datadict["timestamp"])
            result.append(datadict)
        return result

def main():
    from ...configuration.argument_parser import ArgumentParser
    parser = ArgumentParser(description="Plots a ranking of ADCs")
    #parser.add_argument("infilename",help="Input json file names and/or glob string.")
    args = parser.parse_args()
  
    #from ...configuration import CONFIG
    #config = CONFIG()

    globstr =  "/home/jhugon/dune/coldelectronics/femb_python/hothdaq*"
    adc_ranking = ADC_RANKING(globstr)
    adc_ranking.rank()
