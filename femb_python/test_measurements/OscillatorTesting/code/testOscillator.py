#!/usr/bin/env python33

from . import driverUSBTMC
from . import functions
import os
import sys
import time
import json
import numpy as np
import matplotlib.pyplot as plt

class OSCILLATOR_TESTING(object):

        def __init__(self, datadir="data", outlabel="OscillatorTesting"):
                self.outpathlabel = os.path.join(datadir, outlabel)

                self.powerSupplyDevice = None
                self.oscilloscopeDevice = None
                                
        def turnPower(self, OnOrOff, iPowerCycle):
	        if(iPowerCycle == 1): 
		        functions.printSpecial("Checking/Setting Power Supply")
	
	        #:INSTrument[:SELEct] CH- Select CH as the current channel
	        powerChannels = [" CH3"]
	        for iChannel in powerChannels:
	                if(iPowerCycle == 1): 
	                        self.powerSupplyDevice.write(":INST"+iChannel)
	                        self.powerSupplyDevice.write(":INST?")
	                        print("Checking %s" %(self.powerSupplyDevice.read().strip().decode()))
	
	                #Enable and query the current output status
	                self.powerSupplyDevice.write(":OUTP"+iChannel+", "+OnOrOff)
	                time.sleep(1)
	                if(iPowerCycle == 1):
	                        self.powerSupplyDevice.write(":OUTP?")
	                        print("The channel is %s" %(self.powerSupplyDevice.read().strip().decode()))
			
	                if(OnOrOff is "ON"):
	                        #Set and query the voltage setting value of the current channel
	                        self.powerSupplyDevice.write(":VOLT 3.3")
	                        if(iPowerCycle == 1):
	                                self.powerSupplyDevice.write(":VOLT?")
	                                print("Voltage is set to %f" %(float(self.powerSupplyDevice.read().strip().decode())))
	
			#Query the voltage measured on the output terminal
	                if(iPowerCycle == 1):
	                        self.powerSupplyDevice.write(":MEAS:VOLT?")
	                        print("Measured voltage is %f" %(float(self.powerSupplyDevice.read().strip().decode())))
	
			#Query the current measured on the output terminal
	                if(iPowerCycle == 1):
	                        self.powerSupplyDevice.write(":MEAS:CURR?")
	                        print("Measured current is %f" %(float(self.powerSupplyDevice.read().lstrip().decode())))
	

        def doTesting(self):                        
                
                timeStamp= time.strftime("%m_%d-%H_%M")
                
                ###########################################################################
		#Get devices that start with usbtmc in dev dir
                functions.printSpecial("Accessing devices of interest from dev dir")
		###########################################################################
		#Devices of interest are:
		#RIGOL DS1074B Digital Oscilloscope
		#RIGOL DP832 Programmable DC Power Supply
		###########################################################################
                #powerSupplyDevice = None
                #oscilloscopeDevice = None
                dirList = os.listdir("/dev")
                for fName in dirList:
                        if(fName.startswith("usbtmc")):
                                device = driverUSBTMC.DriverUSBTMC("/dev/" + fName)
		
				#Get the manufacturer name, the model, the serial number, and
				#the digital board version number in sequence
                                deviceID = device.getID()
		
                                if(deviceID.startswith(b"RIGOL TECHNOLOGIES,DP832")):
                                        print("DC Power Supply found with identification %s" %(deviceID.decode()))
                                        self.powerSupplyDevice = device
                                elif(deviceID.startswith(b"Rigol Technologies,DS1074B")):
                                        print("Oscilloscope found with identification %s" %(deviceID.decode()))
                                        self.oscilloscopeDevice = device

                if self.powerSupplyDevice is None or self.oscilloscopeDevice is None:
                        print("All devices of our interest not found!\nExiting!\n")
                        sys.exit(1)
		
		###########################################################################
		#Power cycle and take the measurements with oscilloscope
		###########################################################################
		#Power cycle 100 times in LN2
                totalPowerCycle = 100
		
		#Testing 100 MHz oscillators
                requiredFrequency = 100*(10**6)
		
		#Final result
                testResults = [{}, {}, {}, {}]
		
		#Let the oscillator settle in LN2
                time.sleep(5)
                for iPowerCycle in range(1,totalPowerCycle+1,1):
			###########################################################################
                        if(iPowerCycle == 1):
                                functions.printSpecial("Starting test")
			###########################################################################
                        self.turnPower("OFF", iPowerCycle)	
                        self.turnPower("ON", iPowerCycle)
			
			###########################################################################
                        if(iPowerCycle == 1):
                                functions.printSpecial("Checking Oscilloscope")
			###########################################################################
                        
			#Return data points currently displayed on the screen (600 points)
                        self.oscilloscopeDevice.write(":WAV:POIN:MODE NOR")
		
			#Set the format of the waveform data to BYTE (int8: -128 to 127)
                        self.oscilloscopeDevice.write(":WAV:FORM BYTE")
                        if(iPowerCycle == 1):
                                self.oscilloscopeDevice.write(":WAV:FORM?")
                                print("Format of the waveform data is %s" %(self.oscilloscopeDevice.read().strip().decode()))

                        #Set the timebase scale as 5 ns
                        self.oscilloscopeDevice.write(":TIM:SCAL 0.0000000005")
                        if(iPowerCycle == 1):
                                self.oscilloscopeDevice.write(":TIM:SCAL?")
                                print("Timebase scale is %s" %(self.oscilloscopeDevice.read().strip().decode()))
                                
			#:MEASure:SOURce <source>- Select the measurement channel
                        oscilloscopeChannels = [" CHAN1", " CHAN2", " CHAN3" , " CHAN4"]

                        #Turn off the display if any is on
                        for iChannel in oscilloscopeChannels:
                                self.oscilloscopeDevice.write(iChannel+":DISP OFF")
                        
                        waveFormData = []
                        timeInterval = []
                        oscilloscopeFrequency = []
                        for iChannel in oscilloscopeChannels:
                                #Turn on the display
                                self.oscilloscopeDevice.write(iChannel+":DISP ON")
                                #Set the vertical scale to 100 mV
                                self.oscilloscopeDevice.write(iChannel+":SCAL 0.1")
                                #Set the edge trigger source to the same channel
                                self.oscilloscopeDevice.write(":TRIG:EDGE:SOUR"+iChannel)
                                self.oscilloscopeDevice.write(":MEAS:SOUR"+iChannel)

                                if(iPowerCycle == 1):
                                        self.oscilloscopeDevice.write(iChannel+":SCAL?")
                                        print("Vertical scale is %s" %(self.oscilloscopeDevice.read().strip().decode()))
                                        
                                if(iPowerCycle == 1):
                                        self.oscilloscopeDevice.write(":MEAS:SOUR?"+iChannel)
                                        print("Checking %s" %(self.oscilloscopeDevice.read().strip().decode()))

                                if(iPowerCycle == 1):
                                        self.oscilloscopeDevice.write("TRIG:EDGE:SOUR?"+iChannel)
                                        print("Triggering on %s" %(self.oscilloscopeDevice.read().strip().decode()))
                                        
				#Measure the frequency of signal
                                self.oscilloscopeDevice.write(":MEAS:FREQ?"+iChannel)
                                oscilloscopeFrequency.append(self.oscilloscopeDevice.read())
                                if(iPowerCycle == 1):        	
                                        print("Oscilloscope measured frequency is %.3e" %(float(oscilloscopeFrequency[-1])))
		
				#Measure the time interval of the signal
                                self.oscilloscopeDevice.write(":WAV:XINC?"+iChannel)
                                timeInterval.append(self.oscilloscopeDevice.read())
                                if(iPowerCycle == 1):
                                        print("Time interval is %.3e" %(float(timeInterval[-1])))
		
				#Read in waveform data for the channel
                                self.oscilloscopeDevice.write(":WAV:DATA?"+iChannel)
                                
				#Create numpy array for each channel
                                #Will exit if nothing to read due to a problem; like oscillator not in the socket, etc
                                tries = 0
                                success = 0
                                while (tries < 5 and not success):
                                        try:
                                                waveFormData.append(np.frombuffer(self.oscilloscopeDevice.read(), "B"))
                                                success = 1
                                        except:
                                                print("Trying again...")
                                                time.sleep(5)
                                                tries += 1
                                if (not success):
                                        print("%s has a problem. Please check and retry again!\nExiting!\n" %(iChannel.strip()))
                                        sys.exit(1)
                                        

                                #Sleep 1 second and turn off the display for that channel        
                                time.sleep(1)
                                self.oscilloscopeDevice.write(iChannel+":DISP OFF")
                                
			###########################################################################
                        if(iPowerCycle == 1):
                                print()
                                functions.printSpecial("Data Analysis")
			###########################################################################
                        print("Test no. %s" %(iPowerCycle))
                        print()
                        
                        iChannelNumber = 0
                        oscillatorId = []
                        for iChannelData in waveFormData:
                                oscillatorId.append(timeStamp + "-" + str(iChannelNumber + 1))
                                print("Analyzing oscillator in Channel %s" %(iChannelNumber + 1))
                                
                                xPoints = []
                                yPoints = []
                                tempCount = [0, 0, 0, 0]
                                for iData in iChannelData:
                                        yData = (iData & 0xFFF)
                                        yPoints.append(yData)
                                        xPoints.append(tempCount[iChannelNumber])
                                        tempCount[iChannelNumber] = tempCount[iChannelNumber] + 1
			
                                chFigure = plt.figure(figsize=(15, 15), dpi=50, facecolor='w', edgecolor='k') 
		
				#The DFT assume that the signal is periodic on the interval 0 to N,
				#where N is the total numbe fo data points in the signal 
                                yPoints = yPoints[28:428]
                                xPoints = xPoints[28:428]
		
				#Plot Waveform data
                                axis1 = chFigure.add_subplot(2,1,1)
                                axis1.plot(xPoints, yPoints, 'ro', color='g', alpha=0.5)
                                functions.setTitle(axis1, 'Voltage (V)', '', '')
                                functions.setTicks(axis1)
		
				#Peform FFT
                                timeScale = float(timeInterval[iChannelNumber])
                                signal = np.array(yPoints, dtype=float)
                                yFftPoints= np.fft.fft(signal)
                                nLengthData = signal.size
                                xFftPoints = np.fft.fftfreq(nLengthData, d=timeScale)
		
				#One side frequency
				#The zeo frequency is in the first postion of the array, 
				#followed by the positve frequencies in acscending order, and then
				#the negative frequencies in descending order 
                                xFftPoints = xFftPoints[range(nLengthData//2)]
                                yFftPoints = yFftPoints[range(nLengthData//2)]
		
                                axis2 = chFigure.add_subplot(2,1,2)
                                axis2.plot(xFftPoints, 20*np.log10(abs(yFftPoints)), color='g', alpha=0.5)
                                functions.setTitle(axis2, '', 'Frequency (Hz)', '')
                                functions.setTicks(axis2)	
                                axis2.set_xlim([0.0,0.75e9])
                                axis2.set_ylim([0.0,100.0])
		
                                chFigure.show()
                                time.sleep(1)
                                chFigure.savefig(self.outpathlabel+"_OscillatorId_"+oscillatorId[iChannelNumber]+"_PowerCycle_"+ str(iPowerCycle) +".png")
                                plt.close(chFigure)
                                 
				#Need to store the frequency
				#The zeroth coefficient is the average value of the signal over the interval	
                                yFftPoints = yFftPoints[1:]
                                xFftPoints = xFftPoints[1:]
                                maxY = np.argmax(abs(yFftPoints))
                                maxX = xFftPoints[maxY]
                                print('Oscilloscope measured frequency: %.3e' %(float(oscilloscopeFrequency[iChannelNumber].strip())))
                                print('FFT calculated frequency: %.3e' %(maxX))
				
                                testResults[iChannelNumber][iPowerCycle] = maxX
				
                                iChannelNumber = iChannelNumber + 1
                                print()
                self.turnPower("OFF", 1)
                print()
                
		###########################################################################
		#Write summary of results in JSON file
		###########################################################################
                for iC in range(0, 4):                                                 
                        with open(self.outpathlabel+"_OscillatorId_"+oscillatorId[iC]+".json", 'w') as outFile:
                                json.dump(testResults[iC], outFile)
	                
		#Noitfy with a beep: as PC doesn't have speakers, using RIGOl devices
                self.powerSupplyDevice.write("SYST:BEEP:IMM")
                self.oscilloscopeDevice.write("BEEP:ACT")


def main():
        #Standard parameters for the codes: output dir, outlabel (contains thermal cycle)
        datadir = sys.argv[1] 
        outlabel = sys.argv[2]
        
        oscTest = OSCILLATOR_TESTING(datadir, outlabel)

        #Begin testing
        oscTest.doTesting()
        
if __name__ == '__main__':
        main()
