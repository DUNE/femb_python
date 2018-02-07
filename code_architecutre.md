# FPGA Testing - Code Architecture

## Objective

This document is meant as an overview of the functionality of the python scripts needed to initialize and test ASIC using FPGA mezzanine boards. Descriptions of individual functions and relationships will be outlined for providing readers with proof of concept.

## Script hierarchy


## Initialization Stages 

Myriads of code aspects (ie. functions, and registers) must be initialized in the early stages within the code.

### Function Initialization
1. run_main.py
```python
    from scripts.sbnd_femb_meas import FEMB_DAQ
    
    ...
    
    def __init__(self):
            self.sbnd = FEMB_DAQ()
```
2. a) sbnd_femb_meas.py

(I have not had a chance yet to fully explore this function) However useful this function is, it is especially important for initization for accessing class members in the top level script. 

```python
    def __init__(self):
        self.femb_config = FEMB_CONFIG()
        self.adc_reg = ADC_ASIC_REG_MAPPING()
        self.fe_reg = FE_ASIC_REG_MAPPING() 
```

so now with these initializations inside this script (AKA. self.sbnd  - in run_main.py) the following members can be called at the top level.

+ self.sbnd.femb_config
+ self.sbnd.adc_reg
+ self.sbd.fe_reg

2. b) femb_config

```python
    def __init__(self):
        self.femb = FEMB_UDP()
        self.adc_reg = ADC_ASIC_REG_MAPPING()
        self.fe_reg = FE_ASIC_REG_MAPPING() 
```
### Register Initialization

## Essential Procedures







