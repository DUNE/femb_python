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
variety of signal generator input waveforms and ADC settings.  

The other modules in this directory analyze this data and summarize it in .json
format. The data is reorganized for ease of analysis and a .json file is created
for each ASIC chip with filename `adcTest_<timestamp>_<ASIC serial
number>.json` (another .json with the data before reorganization is saved as
`adcTestData_<timestamp>_statsRaw.json` the format of this file is not
discussed here).

JSON File Keys
--------------

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
"clock" is the ADC clock type: 0 external, 1 internal.  "offset" is the ADC
input offset current setting: -1 for disabled and 0 to 15 for the various
settings. Statistic name is the various statistics computed for each channel.
Signal amplitude and signal frequency describe the input sin wave used for
dynamic tests. Channel is the channel number of the ADC ASIC 0 to 15.

ADC Test ROOT Files
-------------------

Raw ADC data is recorded in ROOT trees that are stored in ROOT files. The
filenames look like:

```
adcTestData_<timestamp>_chip<ASIC serial number>_adcClock<clock>_adcOffset<offset>_sampleRate<sample rate (Hz)>_functype<functype>_freq<signal frequency (Hz)>_offset<signal offset (V)>_amplitude<signal amplitude (V)>.root
```

The values in the filename are similar to the keys of the json file described
at the end of the previous section. Additionally, Signal offset voltage is the
offset voltage of the input signal, and "functype" describes the type of input
signal: 0 for none, 1 for DC, 2 for sin, 3 for ramp (the sloping up and sloping
down kind, `/\/\/\`, NOT the abruptly coming down kind `/|/|/|`).

The ROOT files are created and trees filled using the code in
`../../write_root_tree.py`. Each ROOT file contains two trees, "femb_wfdata" and
"metadata". "femb_wfdata" contains waveform samples. For each entry, the branch
"chan" contains the corresponding channel number, and "wf" contains a vector of
sample values. "metadata" contains information similar to that contained in the
filename.

Another ROOT file is created by `calibrate_ramp.py` for each ramp (functype3) file:

```
adcTestData_<timestamp>_chip<ASIC serial number>_adcClock<clock>_adcOffset<offset>_sampleRate<sample rate (Hz)>_functype3_freq<signal frequency (Hz)>_offset<signal offset (V)>_amplitude<signal amplitude (V)>_calib.root
```

This tree is identical to the uncalibrated tree, except the "femb_wfdata" tree
also contains a branch "voltage" which is a vector of floats. Each value in
this vector corresponds to a value in the wf vector. Also, a third tree is
created, "calibration". For each entry in "femb_wfdata", this tree contains two
doubles, "voltsPerADC" and "voltsIntercept". The first should be self
explanatory, while the second is the linear fit voltage where the ADC should be
zero.

ADC Test Cuts
-------------

The cuts to pass the test for an ADC ASIC:

For all sample rates, clock types, offset currents, and channels:

Statistic           | Cut
--------------------|------------
DNLmax400           | < 28 LSBs
DNL75perc400        | < 0.48 LSBs
stuckCodeFrac400    | < 0.1

For all sample rates, clock types, and channels, only offset current off:

Statistic           | Cut
--------------------|------------
INLabsMax400        | < 60 LSBs
INLabs75perc400     | < 50 LSBs
minCode             | < 240
minCodeV            | < 0.2 V
maxCode             | > 4090
maxCodeV            | > 1.3 V
meanCodeFor0.2V     | < 800
meanCodeFor1.6V     | > 3500

For all sample rates, signal frequencies, signal amplitudes, and channels, only
offset current off and external clock:

Statistic           | Cut
--------------------|------------
SINAD               | > 25 dBc

