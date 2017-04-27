from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import
from builtins import hex
from builtins import open
from builtins import range
from builtins import int
from builtins import str
from future import standard_library
standard_library.install_aliases()
from builtins import object
import sys
import string
from subprocess import call
from time import sleep
import os
import ntpath
import glob
import struct

#import required femb_python modules
#from femb_python.configuration import CONFIG
#from femb_python.write_data import WRITE_DATA
#from femb_python.configuration.cppfilerunner import CPP_FILE_RUNNER

#skeleton class provided as an example

class FEMB_TEST:

    def __init__(self):
        print("init")
        #set status variables
        self.status_check_setup = 0
        self.status_record_data = 0
        self.status_do_analysis = 0
        self.status_archive_results = 0

        #define femb_python objects
        #self.femb_udp = FEMB_UDP()
        #self.femb_config = CONFIG()
        #self.write_data = WRITE_DATA()

    def check_setup(self):
        self.status_check_setup = 0
        print("check_setup")
        self.status_check_setup = 1

    def record_data(self):
        if self.status_check_setup == 0:
            print("Please run check_setup method before trying to take data")
            return
        if self.status_record_data == 1:
            print("Data already recorded. Reset/restat GUI to begin a new measurement")
            return
        print("record_data")
        self.status_record_data = 1

    def do_analysis(self):
        if self.status_record_data == 0:
            print("Please record data before analysis")
            return
        if self.status_do_analysis == 1:
            print("Analysis already complete")
            return
        print("do_analysis")
        self.status_do_analysis = 1

    def archive_results(self):
        if self.status_do_analysis == 0:
            print("Please analyze data before archiving results")
            return
        if self.status_archive_results == 1:
            print("Results already archived")
            return
        print("archive_results")
        self.status_archive_results = 1

def main():
    print("Start example test")
    femb_test = FEMB_TEST()
    femb_test.check_setup()
    femb_test.record_data()
    femb_test.do_analysis()
    femb_test.archive_results()
    print("Done example test")

if __name__ == '__main__':
    main()
