#!/usr/bin/env python33
import sys
from subprocess import call

print("Specify which type of board used in setup:")
print("1 = 35t FEMB")
print("2 = SBND FEMB")
print("3 = ADC Test Board")

try:
    num = int(input("Please enter the number corresponding to your board: "))
except:
    print("Invalid number.  Exiting script.")
    sys.exit(0)

if (num < 1 ) or (num > 3):
    print("Invalid number.  Exiting script.")
    sys.exit(0)

if num == 1:
    # Do the thing
    print("35T selected")
    call(["cp","configs/femb_config_35t.py","femb_config.py"])
elif num == 2:
    # Do the other thing
    print("SBND selected")
    call(["cp","configs/femb_config_sbnd.py","femb_config.py"])
    call(["cp","configs/adc_asic_reg_mapping.py","adc_asic_reg_mapping.py"])
    call(["cp","configs/fe_asic_reg_mapping.py","fe_asic_reg_mapping.py"])
elif num == 3:
    # Do yet another thing
    print("ADC Test Board")
    call(["cp","configs/femb_config_adcTest.py","femb_config.py"])
else:
    # Do the default
    print("Should not get here, setup.py script has an error!")
