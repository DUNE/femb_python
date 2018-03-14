from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import
from builtins import range
from future import standard_library
standard_library.install_aliases()
from ..configuration import CONFIG
from ..configuration.argument_parser import ArgumentParser

def main():
    parser = ArgumentParser(description="Configures the FE ASIC chip")
    parser.add_argument("gain",help="Set the gain. Choices: 0-3",type=int,choices=range(4))
    parser.add_argument("shape",help="Set the shaping time. Choices: 0-3.",type=int,choices=range(4))
    parser.add_argument("baseline",help="Set the baseline. Choices: 0-1.",type=int,choices=range(2))
    parser.add_argument("--pulser",help="Enable pulser. Choices: 0-31.",type=int,choices=range(1,32),default=-1)
    parser.add_argument("--slk",help="Leackage current, 0 = 500 pA, 1 = 100 pA. 0 is default",type=int,choices=[0,1],default=0)
    parser.add_argument("--slkh",help="Leackage current multiplier, 0 = 1x, 1 = 10x. 0 is default",type=int,choices=[0,1],default=0)
    parser.add_argument("--monitorBandgap",help="Monitor bandgap instead of signal",action='store_true')
    parser.add_argument("--monitorTemp",help="Monitor temperature instead of signal",action='store_true')
    args = parser.parse_args()
    femb_config = CONFIG()
    femb_config.configFeAsic(args.gain,args.shape,args.baseline,slk=args.slk,slkh=args.slkh,
                                monitorBandgap=args.monitorBandgap,monitorTemp=args.monitorTemp)
    if args.pulser >= 0:
      femb_config.setInternalPulser(1,args.pulser)
    else:
      femb_config.setInternalPulser(0,0)
