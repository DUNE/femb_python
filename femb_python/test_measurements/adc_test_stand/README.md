ADC ASIC Test-stand Software
============================

This is the code for analysis of ADC ASICs. The main program is the GUI, which
is located in gui.py and can be started by running `femb_adc_gui` on the
command line.

The main gui program has two main steps. First, it tries to power-up and
initialize the board and sync the ASIC(s) using the code in setup_board.py. The
results of this step go in `adcSetup_<timestamp>.json`. If this succeeds, it
goes on to the next step which collects data and runs the main tests. It uses
the code in `collect_data.py` to put a bunch of data in ROOT files for a
variety of signal generator input waveforms and ADC settings. The data format
is the one in ../../write_root_tree.py

The other modules in this directory analyze this data and summarize it in .json
format. The data is reorganized for ease of analysis and a .json file is created
for each ASIC chip with filename `adcTest_<timestamp>_<ASIC serial
number>.json` (another .json with the data before reorganization is saved as
`adcTestData_<timestamp>_statsRaw.json` the format of this file is not
discussed here).

Both the adcSetup and adcTest json files contain the following metadata keys:

JSON Top Level Key  | Description
--------------------|------------
serial              | the chip serial number
timestamp           | the test timestamp (a string of YYYYMMDDTHHMMSS)
hostname            | the test computer hostname
board_id            | the test board serial number
operator            | the operator name
sumatra             | the sumatra params dictionary used for the test

The adcSetup json also contains these keys:

JSON Top Level Key  | Description
--------------------|------------
init                | A boolean set to true if the board successfully initializes
sync                | A boolean set to true if the board successfully synchronizes the ADC ASIC
pass                | A boolean set to true if the board is successfully setup (init and sync)

The adcTest json also contains these keys:

JSON Top Level Key  | Description
--------------------|------------
static              | static analysis statistics
dynamic             | dynamic analysis statistics
dc                  | mean and rms for DC input signals
inputPin            | mean and rms of the unconnected input pin
testResults         | booleans whether the chip passed various tests

The static, dc, and inputPin keys refer to nested dictionaries where the keys for a statistic are:

[sample rate (Hz)][clock][offset][statistic name][channel (int)]

For dynamic, the keys are:

[sample rate (Hz)][clock][offset][statistic name][signal amplitude (V)][signal frequency (Hz)][channel (int)]

All of the keys are strings except for the channel which is an int from 0 to 15. 
Sample rate is the ADC sample rate in Hz, either 1000000 or 2000000.
"clock" is the ADC clock type: -1 undefined, 0 external, 1 internal,
monostable, 2 internal FIFO.  "offset" is the ADC input offset current setting:
-1 for disabled and 0 to 15 for the various settings. Statistic name is the
various statistics computed for each channel. Signal amplitude and signal
frequency describe the input sin wave used for dynamic tests. Channel is the
channel number of the ADC ASIC 0 to 15.
