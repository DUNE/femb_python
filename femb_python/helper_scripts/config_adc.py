import sys 
from ..femb_udp import FEMB_UDP
from ..configuration.argument_parser import ArgumentParser, convert_int_literals
from ..configuration.config_file_finder import get_env_config_file, config_file_finder
from ..configuration import CONFIG
from ..configuration.asic_reg_packing import ASIC_REG_PACKING
#from ..configuration.adc_asic_reg_mapping import ADC_ASIC_REG_MAPPING

def main():
    helpStr = "Configure the ADC ASIC"
    parser = ArgumentParser(description=helpStr)
    parser.addConfigFileArgs()
    parser.add_argument("global_register",
                            help="Integer to put in the global registers on all chips. Can be an int or int literal 0b... or 0x....")
    parser.add_argument("channel_register",
                            help="Integer to put in all channel registers on all chips. Can be an int or int literal 0b... or 0x....")
  
    args = parser.parse_args()
  
    config_filename = args.config
    if config_filename:
      config_filename = config_file_finder(config_filename)
    else:
      config_filename = get_env_config_file()
    config = CONFIG(config_filename)
  
    if not config.hasADC:
      print("There are no ADC ASICS in the configuration '{}'".format(config_filename))
      sys.exit(-1)

    global_register = convert_int_literals(args.global_register)
    channel_register = convert_int_literals(args.channel_register)

    reg_mapping = ASIC_REG_PACKING()
    reg_mapping.set_board(global_register,channel_register)
  
    registers = reg_mapping.getREGS()
    config.configAdcAsic(registers)
