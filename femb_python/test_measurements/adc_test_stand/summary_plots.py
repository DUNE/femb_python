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
import datetime
import glob
from uuid import uuid1 as uuid
import json
import numpy
import matplotlib.pyplot as plt

class SUMMARY_PLOTS(object):

    def __init__(self,stats):
        pass

def main():
    from ...configuration.argument_parser import ArgumentParser
    from ...configuration import CONFIG
    ROOT.gROOT.SetBatch(True)
    parser = ArgumentParser(description="Plots summary of ADC Tests")
    parser.add_argument("infilename",help="Input json file name.")
    args = parser.parse_args()
  
    config = CONFIG()

    with open(args.infilename) as infile:
        data = json.load(infile)
        plotter = SUMMARY_PLOTS(data)
    
