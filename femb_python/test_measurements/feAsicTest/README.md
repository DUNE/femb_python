QUAD FE ASIC Test-stand Software
============================

This is the code for analysis of FE ASICs using the quad-chip tester

Production Electronics Validation
--------------

Output JSON File Keys
--------------

Both the adcSetup and adcTest json files contain the following metadata keys:

JSON Top Level Key  | Description
--------------------|------------
timestamp           | the test timestamp (a string of YYYYMMDDTHHMMSS)
hostname            | the test computer hostname
board_id            | the test board serial number
operator            | the operator name
