from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
from ..configuration import CONFIG
from ..configuration.argument_parser import ArgumentParser, convert_int_literals

def main():
    helpStr = "Configure the ADC ASIC"
    parser = ArgumentParser(description=helpStr)
    parser.add_argument("--offsetCurrent",help="Amount of offset current. Choices: 0-16.",type=int,choices=range(16),default=-1)
    parser.add_argument("--testInput",help="Enable test input, otherwise normal input",action='store_true')
    parser.add_argument("--freqInternal",help="Internal clock generator frequency: 0 for 1 MHz, 1 for 2 MHz, default 1",type=int,choices=[0,1],default=1)
    parser.add_argument("--sleep",help="Enable sleep mode",action='store_true')
    parser.add_argument("--pdsr",help="Set pdsr, default 1",type=int,choices=[0,1],default=1)
    parser.add_argument("--pcsr",help="Set pcsr, default 1",type=int,choices=[0,1],default=1)
    parser.add_argument("--clockMonostable",help="Use monostable for ADC clock",action='store_true')
    parser.add_argument("--clockExternal",help="Use external for ADC clock",action='store_true')
    parser.add_argument("--clockFromFIFO",help="Use FIFO digital generator for ADC clock, default",action='store_true')
    parser.add_argument("--sLSB",help="LSB current steering mode: 0 for full, 1 for partial, default 0",type=int,choices=[0,1],default=0)
    parser.add_argument("--f0",help="Set f0",type=int,choices=[0,1],default=0)
    parser.add_argument("--f1",help="Set f1",type=int,choices=[0,1],default=0)
    parser.add_argument("--f2",help="Set f2, default 1",type=int,choices=[0,1],default=1)
    parser.add_argument("--f3",help="Set f3",type=int,choices=[0,1],default=0)
    parser.add_argument("--f4",help="Set f4",type=int,choices=[0,1],default=0)
    parser.add_argument("--f5",help="Set f5",type=int,choices=[0,1],default=0)
  
    args = parser.parse_args()
  
    femb_config = CONFIG()
    enableOffsetCurrent = 0
    offsetCurrent = 0
    if args.offsetCurrent >= 0:
      enableOffsetCurrent = 1
      offsetCurrent = args.offsetCurrent
    testInput=0
    if args.testInput:
      testInput=1
    clockFromFIFO = True
    if not args.clockFromFIFO and (args.clockMonostable or args.clockExternal):
      clockFromFIFO = False
        
    femb_config.configAdcAsic(enableOffsetCurrent=enableOffsetCurrent,offsetCurrent=offsetCurrent,testInput=testInput,
                            freqInternal=args.freqInternal,sleep=args.sleep,pdsr=args.pdsr,pcsr=args.pcsr,
                            clockMonostable=args.clockMonostable,clockExternal=args.clockExternal,clockFromFIFO=clockFromFIFO,
                            sLSB=args.sLSB,f0=args.f0,f1=args.f1,f2=args.f2,f3=args.f3,f4=args.f4,f5=args.f5)
