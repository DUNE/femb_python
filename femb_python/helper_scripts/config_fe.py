from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
from ..configuration import CONFIG
from ..configuration.argument_parser import ArgumentParser

def main():
    parser = ArgumentParser(description="Configures the FE ASIC chip")
    parser.add_argument("gain",help="Set the gain. Choices: 0-3",type=int,choices=range(4))
    parser.add_argument("shape",help="Set the shaping time. Choices: 0-3.",type=int,choices=range(4))
    parser.add_argument("baseline",help="Set the baseline. Choices: 0-1.",type=int,choices=range(2))
    parser.add_argument("--pulser",help="Enable pulser. Choices: 0-31.",type=int,choices=range(32),default=-1)
    args = parser.parse_args()
    femb_config = CONFIG()
    femb_config.configFeAsic(args.gain,args.shape,args.baseline)
    if args.pulser >= 0:
      femb_config.setInternalPulser(1,args.gain)
    else:
      femb_config.setInternalPulser(0,0)
