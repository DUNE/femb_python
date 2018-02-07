# FPGA Testing - Code Architecture

## Objective

This document is meant as an overview of the functionality of the python scripts needed to initialize and test ASIC using FPGA mezzanine boards. Descriptions of individual functions and relationships will be outlined for providing readers with proof of concept.

## Script hierarchy
1. run_main.py
	a.femb_config.py
		i.   user_settings.py
		ii.  adc_asic_reg_mapping.py
		iii. femb_udp_cmdline.py
2. sbnd_femb_meas.py


## Initialization Stages 

Myriads of code aspects (ie. functions, and registers) must be initialized in the early stages within the code.

Reasons for why the top level (run_main.py) can call members 'init_ports()' and 'resetFEMBBoard()' are because FEMB_DAQ is defined as self.sbnd as shown in the code below.

### Function Initialization
+ run_main.py
```python
    from scripts.sbnd_femb_meas import FEMB_DAQ
    
    self.sbnd.femb_config.femb.init_ports()
    self.sbnd.femb_config.resetFEMBBoard()
	
    ...
    
    def __init__(self):
            self.sbnd = FEMB_DAQ()
```

+ sbnd_femb_meas.py

(I have not had a chance yet to fully explore this function) However useful this function is, it is especially important for initization for accessing class members in the top level script. 

```python
    def __init__(self):

        ...

        self.femb_config = FEMB_CONFIG()

        self.adc_reg = ADC_ASIC_REG_MAPPING()
        self.fe_reg = FE_ASIC_REG_MAPPING() 
```

+ femb_config

```python
    def __init__(self):
        self.femb = FEMB_UDP()

        self.adc_reg = ADC_ASIC_REG_MAPPING()
        self.fe_reg = FE_ASIC_REG_MAPPING() 
```
### Register Initialization

## Essential Procedures







