from datetime import datetime
class user_editable_settings:
    def __init__(self):

        #GENERAL SETTINGS#################################################################################
        #The temp you're saying the run was at.  This affects how the analysis looks at the test pulses
        #Since both DACs give slightly different values at different temperatures
        self.temp       = "LN"
        self.chips_to_use = [0,1,2,3]
        self.chip_num = 4
        #Path everything will be saved at
        self.root_path = "/dsk/1/tmp/Quad_Data_FE/"
        self.spreadsheet = "FE_Quad_Data.xlsx"
        self.path = "/dsk/1/tmp/Quad_Data_FE/Quad_Data_" + (datetime.now().strftime('%Y_%m_%d'))  +"/" 
        #Which IP addresses you gave those 4 sockets
        self.PC_IP = '192.168.121.50'
        self.FPGA_IP = "192.168.121.1"
        self.FEMB_VER = "Quad FE Chip Tester with v0x201 Firmware"
        self.frame_size = 0x02cb
        
        #SYNC SETTINGS#####################################################################################
        self.default_DAC = 0x270
        self.default_TP_Period = 800
        self.default_TP_Shift = 0
        self.pre_buffer = 200
        
        self.Latch_Settings = [0x40400000, 0x0, 0x0, 0x0]
        self.Phase_Settings = [0x15145455, 0x5000000, 0x55555415, 0x0]
        self.test_ADC_Settings = 0x00000404
        
        self.sync_peak_min = 3500
        self.sync_peak_max = 7500
        self.sync_peak_height = 11
        self.sync_peaks_max = 90
        self.sync_baseline_min = 0
        self.sync_baseline_max = 3000
        
        #TEST SETTINGS#####################################################################################
        #Amount of data to collect per packet
        self.baseline_length = 5
        self.alive_length = 5
        self.pulse_length = 25
        self.monitor_length = 5
        self.DAC_length = 5
        
        #Settings for the pulse during the "alive" test
        self.test_DAC = 0x490
        self.test_TP_Period = 0x64
        self.test_TP_Shift = 0x0
        self.power_cycles = 3
        
        #The bounds to measure the DAC output and the timing of the pulse for during the DAC output test
        self.DAC_meas_min = 0
        self.DAC_meas_max = 0x3F
        self.DAC_freq = 0x600
        self.DAC_delay = 0x0
        
        #Pulse timing settings for the monitor test
        self.monitor_freq = 800
        self.monitor_delay = 0x0
        self.monitor_amplitude = 15
        
        #Pulse timing settings for the gain calibration test
        self.pulse_freq = 4000
        self.pulse_delay_amplitude = 15
        self.pulse_delay_min = 0
        self.pulse_delay_max = 25
        self.pulse_DAC_min = 0
        self.pulse_DAC_max = 0x3F
        
        #BASELINE ANALYSIS SETTINGS########################################################################
        #Upper and lower bounds for the mean value of the baseline in mV
        self.baseline_200_reject_max = 700
        self.baseline_200_acceptable_max = 700
        self.baseline_200_good_max = 700
        self.baseline_200_good_min = 100
        self.baseline_200_acceptable_min = 100
        self.baseline_200_reject_min = 100
        
        self.baseline_900_reject_max = 1100
        self.baseline_900_acceptable_max = 1100
        self.baseline_900_good_max = 1100
        self.baseline_900_good_min = 700
        self.baseline_900_acceptable_min = 700
        self.baseline_900_reject_min = 700
        
        #Upper and lower bounds for the standard deviation (noise) in electrons        
        self.noise_reject_max = 800
        self.noise_acceptable_max = 600
        self.noise_good_max = 400
        self.noise_good_min = 300
        self.noise_acceptable_min = 200
        self.noise_reject_min = 150
        
        #CHANNEL ALIVE ANALYSIS SETTINGS###################################################################
        self.test_peak_min = 300
        self.under_max = 200
        self.test_peaks_min = 2
        self.test_peaks_max = 25

        self.alive_plot_x_back = 100
        self.alive_plot_x_forward = 100
        
        #PULSE ANALYSIS SETTINGS##########################################################################
        self.pulse_47_min = 3
        self.pulse_47_max = 5
        self.pulse_78_min = 6
        self.pulse_78_max = 8
        self.pulse_14_min = 12
        self.pulse_14_max = 15
        self.pulse_25_min = 20
        self.pulse_25_max = 26  
        
        #DAC STEP ANALYSIS SETTINGS#######################################################################
        self.ideal_DAC_step = 18.75
        self.min_DAC_step = 0x02
        self.max_DAC_step = 0x3F
        self.DAC_peak_min = 45
        
        #MONITOR ANALYSIS SETTINGS########################################################################
        self.monitor_peak_min = 350
        self.monitor_peak_max = 1200
        self.monitor_peaks_min = 2
        self.monitor_peaks_max = 20

        self.monitor_plot_x_back = 100
        self.monitor_plot_x_forward = 100      
        
        #Acceptable range shading values for the plots
        self.red = 'FF0000'
        self.blue = '0000FF'
        self.white = 'FFFFFF'
        self.green = '006400'
        self.yellow = 'FFFF00'
        self.alpha = 0.1
        
        #FOLDER SETTINGS###################################################################################
        self.synchronization_folder = "Synchronization/"
        self.baseline_folder = "Baseline and RMS/"
        self.alive_folder = "Input Alive/"
        self.pulse_folder = "Pulse Calibration/"
        self.DAC_folder = "ASIC DAC Measurement/"
        self.monitor_folder = "Monitor Functionality/"
        self.data = "Data/"
        self.asic_settings = {"4.7mV" : 0,
                              "7.8mV" : 2,
                              "14mV" : 1,
                              "25mV" : 3,

                              "0.5us" : 2,
                              "1us" : 0,
                              "2us" : 3,
                              "3us" : 1,

                              "100pA" : [0,1],
                              "500pA" : [0,0],
                              "1nA" : [1,1],
                              "5nA" : [1,0],

                              "b_off" : 0,
                              "b_on" : 1,

                              "200mV" : 1,
                              "900mV" : 0,

                              "test_off" : [0,0],
                              "test_int" : [0,1],
                              "test_ext" : [1,0],
                              "test_meas" : [1,1],

                              "gains" : ["14mV"],
                              "peaks" : ["2us"],
                              "leaks" : ["500pA"],
                              "buffs" : ["b_on"],
                              "bases" : ["200mV", "900mV"],
                              "tests" : ["test_off","test_ext"],
                              "Baseline_Naming" : "Baseline_ch{}_{}_{}_{}_{}_{}.dat",
                              "Pulse_Naming" : "Pulse_ch{}_{}_{}_{}_{}_{}.dat",
                              "Pulse_Naming2" : "Pulse_{}_{}_{}_{}\\",
                              "Alive_Naming" : "Alive_ch{}_{}_{}.dat",
                              "Alive_Naming2" : "Alive_ch{}_{}_{}_{}.dat",
                              "DAC_Naming"  :   "DAC_step_{}.dat",
                              "Monitor_Naming"  :   "Monitor_ch_{}.dat"}
        
        

        self.bits_to_mv = (2048.0 / 16384)
        self.bits_to_V = (2.048 / 16384)
        
        self.channels = 16
