from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()

def powersupply():

    from ..configuration.argument_parser import ArgumentParser
    from ..configuration import CONFIG
    parser = ArgumentParser(description="Control bench power supply. If run without arguments, turns off all channels.")
    parser.add_argument("--turnOn",help="Turn on all channels listed in configuration file",action='store_true')
    parser.add_argument("--turnOff",help="Turn off all channels",action='store_true')
    args = parser.parse_args()

    config = CONFIG()
    ps = config.POWERSUPPLYINTER
    
    if args.turnOn and args.turnOff:
        print("Error: Can't turn on and turn off at the same time")
        sys.exit(1)
    elif args.turnOn:
      ps.on()
    elif args.turnOff:
      ps.off()
    else:
      ps.off()

def funcgen():

    from ..configuration.argument_parser import ArgumentParser
    from ..configuration import CONFIG
    parser = ArgumentParser(description="Control bench function generator. If run without arguments, stops generator.")
    parser.add_argument("--dc",help="Start DC signal, argument is voltage [V]",type=float,default=-99999)
    parser.add_argument("--sin",help="Start sin signal",action='store_true')
    parser.add_argument("--ramp",help="Start ramp signal",action='store_true')
    parser.add_argument("--offset",help="Set voltage offset [V], default=0.75",type=float,default=0.75)
    parser.add_argument("--amplitude",help="Set voltage amplitude [V], default=0.25",type=float,default=0.25)
    parser.add_argument("--frequency",help="Set signal frequency [Hz], default=100000",type=float,default=100000)
    args = parser.parse_args()

    if(args.dc > -100 and args.sin):
        print("Error: You may not run DC and sin at the same time, exiting.")
        sys.exit(1)
    if(args.dc > -100 and args.ramp):
        print("Error: You may not run DC and ramp at the same time, exiting.")
        sys.exit(1)
    if(args.sin and args.ramp):
        print("Error: You may not run sin and ramp at the same time, exiting.")
        sys.exit(1)

    config = CONFIG()
    funcgen = config.FUNCGENINTER

    funcgen.stop()
    
    if args.ramp:
      funcgen.startRamp(args.frequency,args.offset-args.amplitude,args.offset+args.amplitude)
    elif args.sin:
      funcgen.startSin(args.frequency,args.amplitude,args.offset)
    elif args.dc > -100:
      funcgen.startDC(args.dc)

