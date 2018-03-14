from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()

def check_status():

    from ..configuration.argument_parser import ArgumentParser
    from ..configuration import CONFIG
    parser = ArgumentParser(description="Check the status of the firmware programmer.")
    args = parser.parse_args()

    config = CONFIG()
    try:
        if hasattr(config,"programFirmware"):
            config.checkFirmwareProgrammerStatus()
        else:
            print("Error: Config doesn't implement firmware check")
    except FileNotFoundError as e:
        print("Error: couldn't find programmer",e)

def program():

    from ..configuration.argument_parser import ArgumentParser
    from ..configuration import CONFIG
    parser = ArgumentParser(description="Program the FEMB with the firmware programmer. By default, uses the 2 MHz firmware in the config file.")
    parser.add_argument("-f","--firmwarePath",help="Alternate firmware file path",default=None)
    parser.add_argument("-1","--oneMHz",help="Use the 1 MHz firmware from the config file",action='store_true')
    args = parser.parse_args()

    config = CONFIG()
    try:
        if not (args.firmwarePath is None):
            if hasattr(config,"programFirmware"):
                config.programFirmware(args.firmwarePath)
            else:
                print("Error: Config doesn't implement firmware programming")
        elif args.oneMHz:
            if hasattr(config,"programFirmware1Mhz"):
                config.programFirmware1Mhz()
            else:
                print("Error: Config doesn't implement 1MHz firmware programming")
        else:
            if hasattr(config,"programFirmware2Mhz"):
                config.programFirmware2Mhz()
            else:
                print("Error: Config doesn't implement 2MHz firmware programming")
    except AttributeError as e:
        print(dir(e))
        print(e.args)
        #help(e)
        raise e
    except FileNotFoundError as e:
        print("Error: couldn't find programmer",e)
