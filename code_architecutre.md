# Single Socket ASIC Testing with PC to FPGA Using Python

![](https://github.com/carlos-pereyra/single_socket_dev/blob/master/msc/fpga_mezzanine.jpg "")

## I. Objective

This document is an overview of the python scripts needed to write registers to the ADC ASIC. Outlined are the procedures necessary to sync the ADC ASIC with the PC.

A detailed description of each function in the python code will provided, as well as an explanation of the back-end vhdl code programmed on to the FPGA.

## II. Python script hierarchy
1. run_main.py
	* femb_config.py
		+ user_settings.py
		+ adc_asic_reg_mapping.py
		+ femb_udp_cmdline.py
2. sbnd_femb_meas.py

The overall purpose of these script are to provide basic communication between the PC and ADC ASIC through the FPGA.
![food](https://github.com/carlos-pereyra/single_socket_dev/blob/master/msc/single_socket_schematic.png)

## III. Python Procedures 
A basic overview of the functions within the python scripts are detailed in the following.
### III.a Initialization
Functions and registers must be initialized in the early stages within the code. Member functions from other scripts can be readily called due to ```python self.sbnd = FEMB_DAQ()```. This enables the functions initPorts() and resetFEMBBoard() to be accessed.
#### III.a.1 run_main.py
```python
    from scripts.sbnd_femb_meas import FEMB_DAQ
    ...
    self.sbnd.femb_config.femb.init_ports()
    self.sbnd.femb_config.resetFEMBBoard()	
    ...
    def __init__(self):
            self.sbnd = FEMB_DAQ()
```
#### III.a.2 sbnd_femb_meas.py 
```python
    def __init__(self):
        ...
        self.femb_config = FEMB_CONFIG()
	...
        self.adc_reg = ADC_ASIC_REG_MAPPING()
        self.fe_reg = FE_ASIC_REG_MAPPING()
```
#### III.a.3 femb_config_sbnd.py
Since most functions are scattered about in different scripts the most important script or most useful script in storing all the necessary ASIC ADC syncing functions (femb_config_sbnd.py) must be called from other scripts. The initialization is shown below.
The UDP script (femb_udp_cmdline.py) comes into play at various times to aid in 'reading' registers, 'writing' register, and 'initializing' ports. All of this is necessary and included under the UDP script due to the network (IPv4 and UDP) networking responsibilities.
```python
    from scripts.femb_udp_cmdline import FEMB_UDP
    ...
    def __init__(self):
        self.femb = FEMB_UDP()
	...
        self.adc_reg = ADC_ASIC_REG_MAPPING()
        self.fe_reg = FE_ASIC_REG_MAPPING()
```
### III.b ADC Sync Procedures
Now that all the initiazliations have been made we can get into the major procedures necessary for syncing the ADC ASIC. A look at the main function tells us the top level procedures.

#### III.b.1 def loop(self)
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
An understanding of the (1) first ```python self.sbnd.femb_config.femb.init_ports()```, (2) second ```python self.sbnd.femb_config.resetFEMBBoard() ```, (3) third ```python self.sbnd.fembconfig.initBoard```, and (4) finally the```python self.sbnd.fembconfig.syncADC() ``` will be provided.

#### III.b.2 init_ports()
Sends dummy packet from PC to FPGA to initiate 'ARP' (?) request and map FPGA to port.
##### III.b.2.1 Packets
In a nutshell this function sends data structured as a 6 bit bus. Each 'H' option stores an integer of size 2 bits. Where KEY1, KEY2, and FOOTER are _.
```python
WRITE_MESSAGE = struct.pack('HHH',socket.htons( self.KEY1  ), socket.htons( self.FOOTER  ), 0x0  )
```
##### III.b.2.2 Protocols
Specifying internet protocol and communication method must be identified. The option AFINET calls for IPv4, while SOCKDGRAM specfies UDP.
```python
sock_write = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
```
##### III.b.2.3 Listening for Packets
The PC must keep listening to the ports for any packets being sent and received. After sending a packet out, it may take time for the packet to be sent back to the PC. So "SOL_SOCKET" is used to define the family of options that can be used, which enables "SO__REUSEADDR" as an option, which is used to keep the socket open for use even after we close() it. Thereby enabling the PC to keep listening for UDP packets. 
According to a webpage on the microsoft website, "the SO_REUSEADDR flag tells the kernel to reuse a local socket in the time_wait state without waiting for its natural timeout to expire".
```python
sock_write.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
```
##### III.b.2.4 Sending a Message to the FPGA
Finally we send a hexadecimal 
```python
sock_write.sendto(WRITE_MESSAGE,(destIP, self.PORT_WREG ))
```

#### III.b.3 resetFEMBBoard()
Here's a simple function to analyze. Recall that registers 0,1, and 2 exhibit unique behaviors in the FPGA. While every register will retain the value written to it, these 3 will only have high bits for one clock cycle. Meaning a true value (1) will have a reset effect instantly, but next clock cycle this will not carry through to the next instance. So writing a 0 to register 0 is only a pre-caution but is not necessary, since the FPGA will automatically set this to 0.
```python
    def resetFEMBBoard(self):
        self.femb.write_reg ( self.REG_RESET, 1) # REG_RESET <= reg0(1)
        time.sleep(5.)
        self.femb.write_reg ( self.REG_RESET, 0) # REG_RESET <= reg0(1)
```
This step is essential for purging the system of random bits set for each register. In the next step we will dictate register values. Now Reg_0 is set to 0.

#### III.b.4 initBoard()
This function is the first phase in syncing the ADC ASIC with the PC. This is where the essential registers for the ADC ASIC are being written to, as a first pass at syncing.
##### III.b.4.1 Frame Size
When WIB mode is on, the frame size is essentially the number of packets that should be received, so that data from all 16 channels have been received.
```python
    def initBoard(self):
        frame_size = settings.frame_size
        if (frame_size%13 != 0):
            frame_size = 13 * (frame_size//13)
            
        self.femb.write_reg(10, frame_size)
        time.sleep(0.1)

        if (self.femb.read_reg(10) != frame_size):
```
Since WIB mode is on (at least for ASIC testing), we define the buffer size of incoming data from the ASIC. The frame size must be a multiple of 13, so the FPGA interprets this through to vhdl to send an appropriate number of packets.
The first packet from the FPGA in our case, is 0xFACE. The 12 remaining packets contain data from each of the 16 channels. The way in which data in each packet is formed is non-trivial. Each packet shares data with two channels. For instance each 'word' contains the full 12 bits of data from a single channel, while the remaining 4 bits pertain to another channel. 
Essentially, the whole recieving data process (seen by the PC) is due to VHDL code which has instructed the FPGA to behave in a certain way. The behavior of the FPGA is to output data to the PC, which then the PC interprets the 13 (16 bit words) knowing that the header must be 0xFACE, then the proceeding data is actual numerical readings from the ADC ASIC.
The exact organization of how data maps to channels will be explained later.
##### III.b.4.2 WIB mode
When writing to any register, that register value should be verified in the vhdl code. In this case it can be seen that WIB mode is indeed register 8 at the top level, where the register map is defined. It will also become apparent, that register 8 is a vector of length 8 total bits. 
```python
        self.femb.write_reg(8, 0x80000001)                  # WIB_MODE   <= reg8_p(0)
        self.femb.write_reg(7, 0x80000000)                  # CHN_select <= reg7_p(7 downto 0)
```
Inside the FPGA it has been programmed to use the zero bit otherwise known as the first bit, which in our case is 1. So WIB mode is on, and thereby enables the 'selected channel' to be 0x10 in hex, which is 16 in decimnal. A look at the actual vhdl will show that _. We know that there is 16 channels for each ADC ASIC so there is some _.
```vhdl 
process(clk_sys) 	
  begin
	if (clk_sys'event AND clk_sys = '1') then	
			if(CHN_select(4) = '1') and (WIB_MODE = '0') then	-- execute if WIB_MODE is OFF
				UDP_DATA_LATCH <= Data_Latch;
				CHN_select_s	<= x"0" & CHN_select(3 downto 0);
			else							-- execute if WIB_MODE is ON
				if(Data_Latch	= '1') and (Data_Latch_dly = '0') then -- where is Data_Latch Set High?
					if (WIB_MODE = '0') then
						CHN_select_s		<= x"00";
					else
						CHN_select_s		<= x"10"; -- dec 16
					end if;
					UDP_DATA_LATCH 	<= '1';			-- UDP_DATA_LATCH stays high until..
					Data_Latch_dly 	<= '1';
				end if;
				
				if (Data_Latch_dly = '1') then
					CHN_select_s	<= CHN_select_s + 1;
				end if;	
				if(CHN_select_s >= x"0f") and (Data_Latch_dly = '1') and (WIB_MODE = '0') then
					UDP_DATA_LATCH <= '0';
					Data_Latch_dly <= '0';
				elsif(CHN_select_s >= x"1C") and (Data_Latch_dly = '1') and (WIB_MODE = '1') then
					UDP_DATA_LATCH <= '0';
					Data_Latch_dly <= '0';
				end if;
			end if;
```
##### III.b.4.3 Latchloc
In most cases the data output from the FPGA to the PC will not be received in the order we expect it. We expect to see the header 0xFACE, however due the packet arriving offset by some bits, it must be shifted. Latch loc tells the PC to shift the contents of the packet by n number of bits, so that 0xFACE is the first of the 13 packets received.
```python
        self.femb.write_reg(settings.LATCHLOC_reg, settings.LATCHLOC_data) # LATCH_LOC_0 <= reg4_p(7 downto 0)
        self.femb.write_reg(settings.CLKPHASE_reg, settings.CLKPHASE_data) # CLK_selectx <= reg6_p(7 downto 0)
```
Inside the vhdl top level register 4 is mapped to a signal called "latch loc 0" which is then mapped to the entity "ADC S SKT RDOUT". Where inside the "ADC S SKT RDOUT" entity the sublevel entity "ADC PLL" is then used to map "latch loc 0" to the first element of the signal "LATCH LOC".
```vhdl
ARCHITECTURE behavior OF ADC_s_SKT_RDOUT IS
	SIGNAL	LATCH_LOC		: SL_ARRAY_7_TO_0(0 to 7);
...
ADC_PLL_inst1 : entity work.ADC_PLL
			 LATCH_LOC(0)	<= LATCH_LOC_0;
```
Then even further inside "ADC S SKT RDOUT" there is a sublevel entity called "SBND ASIC RDOUT" where "LATCH LOC(i)" where i is zero, then this is then mapped to an input "LATCH_LOC" for "SBND ASIC RDOUT".
```
SBND_ASIC_RDOUT_V2 : entity work.SBND_ASIC_RDOUT_V2
	PORT MAP
	(
			...
			LATCH_LOC		=> LATCH_LOC(i)
```
So what happens then? The FPGA then tries to sync the ADC ASIC with the PC only when a counter "BIT CNT" matches the first two bits of "LATCH LOC", which thereby shifts the data output by this delay due to the counter.
```vhdl
	elsif (clk_200Mhz'event AND clk_200Mhz = '1') then
		CASE state IS
		when S_IDLE =>	
			BIT_CNT			<= x"00";
			sys_sync		<= '0';
			asic_empty_rst		<= '1';
			if (ADC_CONV_DLY1 = '1' and ADC_CONV_DLY2 = '0') then
				asic_empty_rst	<= '0';
				state 		<= S_READ_SDATA;				
				end if;		  
		when S_READ_SDATA =>	
			BIT_CNT		<= BIT_CNT + 1;
			sys_sync	<= '0';
			if(BIT_CNT = LATCH_LOC) then
				sys_sync 	<= '1';
```
##### III.b.4.4 Clock Tuning
The clocks that determine the performance of the ADC are the (a.) RESET, (b.) READ, (c.) IDXM, (d.) IDXL, (e.) IDL1, and (f.) IDL2 clocks. It has been found via empirical observation that the ADC ASIC performance is optimized by aligning the falling edge of all the clocks - with the fall edge of the RESET clock. As mentioned earlier it is important to always check that the registers you are writing to on the FPGA correspond to the registers defined in the python code.
```python
        self.femb.write_reg(22, settings.reg22_value[0])    # OFST_RST <= reg22_p      
        self.femb.write_reg(23, settings.reg23_value[0])    # WDTH_RST <= reg23_p;
        
        self.femb.write_reg(24, settings.reg24_value[0])    # OFST_READ <= reg24_p
        self.femb.write_reg(25, settings.reg25_value[0])    # WDTH_READ <= reg25_p
        
        self.femb.write_reg(26, settings.reg26_value[0])    # OFST_IDXM <= reg26_p
        self.femb.write_reg(27, settings.reg27_value[0])    # WDTH_IDXM <= reg27_p
        
        self.femb.write_reg(28, settings.reg28_value[0])    # OFST_IDXL <= reg28_p
        self.femb.write_reg(29, settings.reg29_value[0])    # WDTH_IDXL <= reg29_p
        
        self.femb.write_reg(30, settings.reg30_value[0])    # OFST_IDL_f1 <= reg30_p
        self.femb.write_reg(31, settings.reg31_value[0])    # WDTH_IDL_f1 <= reg31_p
                                                            
        self.femb.write_reg(32, settings.reg32_value[0])    # OFST_IDL_f2 <= reg32_p
        self.femb.write_reg(33, settings.reg33_value[0])    # WDTH_IDL_f2 <= reg33_p

        #Fine Control
        self.femb.write_reg(34, settings.reg34_value[0])    # pll_STEP0_L <= reg34_p [C0 & C1 fine clock settings]   
        self.femb.write_reg(35, settings.reg35_value[0])    # pll_STEP1_L <= reg35_p [C2 & C3 fine clock settings]
        self.femb.write_reg(36, settings.reg36_value[0])    # pll_STEP2_L <= reg36_p [C2 & C3 fine clock settings]
```
{insert image of clocks}
The low logic level of a clock cycle is defined as the offset (OFST), while the high logic level of a clock cycle is defined as the width (WDTH). This is of course opposite case when these clocks have been defined as inverted. In the settings python script is where the clocks can be defined. The clock settings are always in hex, as any other register is.
##### III.b.4.5 Global Register Settings
In the fifth order of procedures needed to sync the ADC ASIC with the PC, is configuring the global and individual channel registers. After configuring the register settings here for the first time, you can change individual registers one at a time. The registers that are set here will remain the same, until you change them by calling "set adc board" again.
```python
        #clk = 2 is external
        #clk = 0 is internal
        self.adc_reg.set_adc_board( d=0, pcsr=0, pdsr=0, slp=0, tstin=1,
                 clk = 0, frqc = 1, en_gr = 0, f0 = 0, f1 = 0, 
                 f2 = 0, f3 = 0, f4 = 0, f5 = 1, slsb = 0)
```
###### Inside set_adc_board()
Inside the function "set_adc_board" there is nested functions that ultimately separate the inputs to be handled by the "set_adc_chp" and "set_adc_global" functions.
```python
    def set_adc_board():
        asic = 1
        for chip in range(asic):
            self.set_adc_chip( chip, d, pcsr, pdsr, slp, tstin,
                 clk, frqc, en_gr, f0, f1, f2, f3, f4, f5, slsb)
    def set_adc_chip(self, chip=0,
                 d=0, pcsr=1, pdsr=1, slp=0, tstin=0,
                 clk = 0, frqc = 0, en_gr = 0, f0 = 0, f1 = 0, 
                 f2 = 0, f3 = 0, f4 = 0, f5 = 1, slsb = 0): #set f5 = 1 1/30/18 cp
        for chn in range(16):
            self.set_adc_chn(chip, chn, d, pcsr, pdsr, slp, tstin )
        self.set_adc_global (chip, clk, frqc, en_gr, f0, f1, f2, f3, f4, f5, slsb)
```
Inside the "set_adc_chn" function is a great example of bit wise masking. It is necessary to use bitwise masking for writing binary values that correspond to specific channels, hence we are trying to write register values for each channel.
```python
def set_adc_chn(self, chip=0, chn=0, d=-1, pcsr=-1, pdsr=-1, slp=-1, tstin=-1):
        tuple_num = 5 * chip + ((15 - chn) // 4)
        ...
        chn_reg = d_bit + pcsr_bit + pdsr_bit + slp_bit  + tstin_bit
	...
        or_mask = (chn_reg << bitshift) #holds the 8 bits we care about - tuple 3 => ch12,13,14,15
        ...
        self.REGS[tuple_num] = self.REGS[tuple_num] & (and_mask)                
        self.REGS[tuple_num] = self.REGS[tuple_num] | (or_mask)
```
Ultimately this long list of logic redefines the _.
An attempt to outline all the logic _. 
How this "tuple_num" maps to each channel will be shown. {include table} {show and explain example logic}
##### III.b.4.6 SPI Write
At the vhdl top level.
```vhdl
begin
----- register map -------
	...
	WRITE_ADC_ASIC_SPI 	<= reg2_p(0);
	...
ProtoDUNE_ASIC_CNTRL_inst :	entity work.ProtoDUNE_ASIC_CNTRL
	PORT MAP
	(
		...
		WRITE_SPI	=> WRITE_ADC_ASIC_SPI
	)
```
If we dive into the "protoDUNE ASIC CTRL" entity we then see that the "WRITE SPI" register merely configures other signals "CHIP", "SPI_CTRL". We will trace what exactly these other signals are used for in the following steps.
```vhdl
     elsif (clk_sys'event AND clk_sys = '1') then
			CASE state IS
			when S_IDLE =>
				if (ADC_ASIC_RESET = '1')  then		
					SPI_CNTL		<= '1';			
					state 		<= S_ADC_ASIC_RESET;	
				elsif (SOFT_ADC_RESET = '1')  then		
					SPI_CNTL		<= '1';			
					state 		<= S_SOFT_ADC_RESET;						
				elsif (FE_ASIC_RESET = '1')  then
					state 		<= S_FE_ASIC_RESET;	
				elsif (WRITE_SPI = '1')  then
					CHIP			<= x"0";
					SPI_CNTL		<= '1';				
					DPM_ADDR_S 	<= ASIC_WR_ADDR(7 DOWNTO 0);	    	
					DPM_RB_ADDR	<= ASIC_RD_ADDR(7 DOWNTO 0);   			  	
					state 		<= S_WRITE_ADC_SPI_START;
```
Essentially the state is being changed to "S WRITE ADC SPI START".
##### III.b.4.7 Configure ADC ASIC


#### III.b.5 syncADC()


