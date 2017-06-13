ADC ASIC Test-stand Software
============================

This is the code for analysis of ADC ASIC test stand software. The main program
is the GUI, which is located in gui.py and can be started by running
`femb_adc_gui` on the command line.

The main gui program has two main steps. First, it tries to power-up and
initialize the board and sync the ASIC(s) using the code in setup_board.py. The
results of this step go in `adcSetup_<timestamp>.json`. If this succeeds, it
goes on to the next step which collects data and runs the main tests. It uses
the code in `collect_data.py` to put a bunch of data in ROOT files for a
variety of signal generator input waveforms and ADC settings. The data format
is the one in ../../write_root_tree.py

The other modules in this directory analyze this data and summarize it in .json
format. The data is reorganized for ease of analysis and .json file is created
for each ASIC chip with filename `adcTest_<timestamp>_<ASIC serial
number>.json` (another .json with the data before reorganization is saved as
`adcTestData_<timestamp>_statsRaw.json` the format of this file is not
discussed here).

The json file contains the top level keys:

static: static analysis statistics
dynamic: dynamic analysis statistics
dc: mean and rms for DC input signals
inputPin: mean and rms of the unconnected input pin
testResults: booleans whether the chip passed various tests
serial: the chip serial number
timestamp: the test timestamp (a string of YYYYMMDDTHHMMSS)
hostname: the test computer hostname
board_id: the test board serial number
operator: the operator name
sumatra: the sumatra params dictionary used for the test

The static, dc, and inputPin keys refer to nested dictionaries where the keys for a statistic are:

[sample rate][clock][offset][statistic name][channel (int)]

For dynamic, the keys are:

[sample rate][clock][offset][statistic name][signal amplitude in volts][sample frequency in hertz][channel (int)]

All of the keys are strings except for the channel which is an int from 0 to 15.
