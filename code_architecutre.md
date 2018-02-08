# Single Socket ASIC Testing with PC to FPGA Using Python

(https://github.com/carlos-pereyra/single_socket_dev/blob/master/msc/fpga_mezzanine.jpg "food is good")

## I. Objective

This document is meant as an overview of the functionality of the python scripts needed to initialize and test ASIC using FPGA mezzanine boards. Descriptions of individual functions and relationships will be outlined for providing readers with proof of concept.

An essential understanding of how this python package relates the PC to the FPGA and ultimately the ASIC.

(https://github.com/carlos-pereyra/single_socket_dev/blob/master/msc/single_socket_schematic.png)

## II. Script hierarchy
1. run_main.py
	* femb_config.py
		+ user_settings.py
		+ adc_asic_reg_mapping.py
		+ femb_udp_cmdline.py
2. sbnd_femb_meas.py


## III. Function Initialization 

Myriads of code aspects (ie. functions, and registers) must be initialized in the early stages within the code.
Reasons for why the top level (run_main.py) can call members 'init_ports()' and 'resetFEMBBoard()' are because FEMB_DAQ is defined as self.sbnd as shown in the code below.

### run_main.py
```python
    from scripts.sbnd_femb_meas import FEMB_DAQ
    
    self.sbnd.femb_config.femb.init_ports()
    self.sbnd.femb_config.resetFEMBBoard()
	
    ...
    
    def __init__(self):
            self.sbnd = FEMB_DAQ()
```

### sbnd_femb_meas.py
(I have not had a chance yet to fully explore this function) However useful this function is, it is especially important for initization for accessing class members in the top level script. 
```python
    def __init__(self):

        ...

        self.femb_config = FEMB_CONFIG()

        self.adc_reg = ADC_ASIC_REG_MAPPING()
        self.fe_reg = FE_ASIC_REG_MAPPING() 
```

### femb_config_sbnd.py
Since most functions are scattered about in different scripts the most important script or most useful script in storing all the necessary ASIC ADC syncing functions (femb_config_sbnd.py) must be called from other scripts. The initialization is shown below.

The UDP script (femb_udp_cmdline.py) comes into play at various times to aid in 'reading' registers, 'writing' register, and 'initializing' ports. All of this is necessary and included under the UDP script due to the network (IPv4 and UDP) networking responsibilities.
```python
    from scripts.femb_udp_cmdline import FEMB_UDP

    ...

    def __init__(self):
        self.femb = FEMB_UDP()

        self.adc_reg = ADC_ASIC_REG_MAPPING()
        self.fe_reg = FE_ASIC_REG_MAPPING() 
```

## IV. Essential Procedures

Now that all the initiazliations have been made we can get into the major functional procedures used in testing asics. Before we get into the details, we should take a look at the main function. 

### Main
```python
class main:
    def loop(self):
        print ("Start")

        self.sbnd.femb_config.femb.init_ports(hostIP = settings.PC_IP, destIP = settings.FPGA_IP)
        
        self.sbnd.femb_config.resetFEMBBoard()
        self.sbnd.femb_config.initBoard()
            
        time.sleep(1)
        self.sbnd.femb_config.syncADC()
```

Sequentially the main function calls these functions:
1. ```python self.sbnd.femb_config.femb.init_ports() ```
2. ```python self.sbnd.femb_config.resetFEMBBoard() ```
3. ```python self.sbnd.femb_config.initBoard() ```
4. ```python self.sbnd.femb_config.syncADC() ```

---

An understanding of each of these functions reveals how the PC programs the FPGA and how the FPGA is able to test the ASIC.

### init_ports()					[udp.py]

Sends dummy packet from PC to FPGA to initiate 'ARP' (?) request and map FPGA to port.

In a nutshell this function sends data structured as a 6 bit word. Each 'H' option stores an integer of size 2 bits.
```python
WRITE_MESSAGE = struct.pack('HHH',socket.htons( self.KEY1  ), socket.htons( self.FOOTER  ), 0x0  )
```


To do this the internet protocol and communication method must be identified.
```python
sock_write = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
```

An esoteric line (below), is used in defining socket options. In this case SOL_SOCKET is used to define the family of options that can be used, which we chose SO__REUSEADDR. This option essentially keeps the socket open for use even after we close() it.

"the SO_REUSEADDR flag tells the kernel to reuse a local socket in the time_wait state without waiting for its natural timeout to expire"
```python
sock_write.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
```


Finally we send a hexadecimal 
```python
sock_write.sendto(WRITE_MESSAGE,(destIP, self.PORT_WREG ))
```

### resetFEMBBoard()					[config.py]

Here's a simple function to analyze. 

Recall that registers 0,1, and 2 exhibit unique behaviors in the FPGA. While every register will retain the value written to it, these 3 will only have high bits for one clock cycle. Meaning a true value (1) will have a reset effect instantly, but next clock cycle this will not carry through to the next instance. So writing a 0 to register 0 is only a pre-caution but is not necessary, since the FPGA will automatically set this to 0.

```python
    def resetFEMBBoard(self):
        self.femb.write_reg ( self.REG_RESET, 1) # REG_RESET <= reg0(1)
        time.sleep(5.)
        self.femb.write_reg ( self.REG_RESET, 0) # REG_RESET <= reg0(1)
```

This step is essential for purging the system of random bits set for each register. In the next step we will dictate register values.

### initBoard()						[config.py]

This function is pretty complicated and has multiple parts that are easier to explain if they are broken up into individual pieces.

#### a. Frame Size
```python
    def initBoard(self):
        frame_size = settings.frame_size
        if (frame_size%13 != 0):
            frame_size = 13 * (frame_size//13)
            
        self.femb.write_reg(10, frame_size)
        time.sleep(0.1)

        if (self.femb.read_reg(10) != frame_size):
```
This is where we define the buffer size of incoming data from the ASIC. Data must be a multiple of 13 (16 bit words) in our case, because the first 'word' in the data stream from the ASIC is 0xFACE, while the 12 remaining 'words' contain data from each of the 16 channels. 

It should be noted that each 'word' shares data with two channels. For instance each 'word' contains the full 12 bits of data from a single channel, while the remaining 4 bits pertain to another channel. 

The exact organization of how data maps to channels will be explained later.

#### b. WIB mode
```python
        self.femb.write_reg(8, 0x80000001)                  # WIB_MODE   <= reg8_p(0)
        self.femb.write_reg(7, 0x80000000)                  # CHN_select <= reg7_p(7 downto 0)
```


#### c. Latchloc
```python
        self.femb.write_reg(settings.LATCHLOC_reg, settings.LATCHLOC_data) # LATCH_LOC_0 <= reg4_p(7 downto 0) # Latch lock setting for ASIC
        
        self.femb.write_reg(settings.CLKPHASE_reg, settings.CLKPHASE_data) # CLK_selectx <= reg6_p(7 downto 0) # Phase settings for ASIC
```

#### d. Clock Tuning
```python
        self.femb.write_reg(22, settings.reg22_value[0])    # OFST_RST <= reg22_p      
        self.femb.write_reg(23, settings.reg23_value[0])    # WDTH_RST <= reg23_p;
        
        self.femb.write_reg(24, settings.reg24_value[0])    # OFST_READ <= reg24_p
        self.femb.write_reg(25, settings.reg25_value[0])    # WDTH_READ <= reg25_p
        
        self.femb.write_reg(26, settings.reg26_value[0])    # OFST_IDXM <= reg26_p
        self.femb.write_reg(27, settings.reg27_value[0])    # WDTH_IDXM <= reg27_p
        
        self.femb.write_reg(28, settings.reg28_value[0])    # OFST_IDXL <= reg28_p
        self.femb.write_reg(29, settings.reg29_value[0])    # WDTH_IDXL <= reg29_p
        
        self.femb.write_reg(30, settings.reg30_value[0])    # WDTH_IDXL <= reg29_p
        self.femb.write_reg(31, settings.reg31_value[0])    # WDTH_IDL_f1 <= reg31_p
                                                            
        self.femb.write_reg(32, settings.reg32_value[0])    # OFST_IDL_f2 <= reg32_p
        self.femb.write_reg(33, settings.reg33_value[0])    # WDTH_IDL_f2 <= reg33_p

        #Fine Control
        self.femb.write_reg(34, settings.reg34_value[0])    # pll_STEP0_L <= reg34_p [C0 & C1 fine clock settings]   
        self.femb.write_reg(35, settings.reg35_value[0])    # pll_STEP1_L <= reg35_p [C2 & C3 fine clock settings]
        self.femb.write_reg(36, settings.reg36_value[0])    # pll_STEP2_L <= reg36_p [C2 & C3 fine clock settings]
```

#### e. Global Register Settings
```python
        #clk = 2 is external
        #clk = 0 is internal
        self.adc_reg.set_adc_board( d=0, pcsr=0, pdsr=0, slp=0, tstin=1,
                 clk = 0, frqc = 1, en_gr = 0, f0 = 0, f1 = 0, 
                 f2 = 0, f3 = 0, f4 = 0, f5 = 1, slsb = 0)
```


#### f. SPI Write



#### g. Configure ADC ASIC



### syncADC()


