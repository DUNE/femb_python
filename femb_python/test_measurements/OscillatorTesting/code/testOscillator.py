#!/usr/bin/env python2

import driverUSBTMC
import functions
import os
import sys
import time
import json
import numpy as np
import matplotlib.pyplot as plt


def turnPower(OnOrOff, iTest):
	if(iTest == 0): 
		functions.printSpecial("Checking/Setting Power Supply")

	#:INSTrument[:SELEct] CH- Select CH as the current channel
	#powerChannels = [" CH1", " CH2", " CH3"]
	powerChannels = [" CH1"]
	for iChannel in powerChannels:
		if(iTest == 0): 
			powerSupplyDevice.write(":INST"+iChannel)
			powerSupplyDevice.write(":INST?")
			print "Checking ",powerSupplyDevice.read().strip()

		#Enable and query the current output status
		powerSupplyDevice.write(":OUTP"+iChannel+", "+OnOrOff)
		time.sleep(3)
		if(iTest == 0):
			powerSupplyDevice.write(":OUTP?")
			print "The channel is ", powerSupplyDevice.read().strip()
		
		if(OnOrOff is "ON"):
			#Set and query the voltage setting value of the current channel
			powerSupplyDevice.write(":VOLT 3.5")
			if(iTest == 0):
				powerSupplyDevice.write(":VOLT?")
				print "Voltage is set to ", powerSupplyDevice.read().strip()

		#Query the voltage measured on the output terminal
		if(iTest == 0):
			powerSupplyDevice.write(":MEAS:VOLT?")
			print "Measured voltage is ", powerSupplyDevice.read().strip()

		#Query the current measured on the output terminal
		if(iTest == 0):
			powerSupplyDevice.write(":MEAS:CURR?")
	        	print "Measured current is ", powerSupplyDevice.read().lstrip()

###########################################################################
#Get devices that start with usbtmc in dev dir
functions.printSpecial("Accessing devices of interest from dev dir")
###########################################################################
#Devices of interest are:
#RIGOL DS1074B Digital Oscilloscope
#RIGOL DP832 Programmable DC Power Supply
###########################################################################

powerSupplyDevice = None
oscilloscopeDevice = None
dirList = os.listdir("/dev")
for fName in dirList:
	if(fName.startswith("usbtmc")):
		device = driverUSBTMC.DriverUSBTMC("/dev/" + fName)

		#Get the manufacturer name, the model, the serial number, and
		#the digital board version number in sequence
		deviceID = device.getID()

		if(deviceID.startswith("RIGOL TECHNOLOGIES,DP832")):
			print "DC Power Supply found with identification", deviceID
			powerSupplyDevice = device
	 	elif(deviceID.startswith("Rigol Technologies,DS1074B")):
			print "Oscilloscope found with identification", deviceID
			oscilloscopeDevice = device

if powerSupplyDevice is None or oscilloscopeDevice is None:
	print "All devices of our interest not found!\nExiting!\n"
	sys.exit(0)

###########################################################################
#Do it 100 times and take the measurement with oscilloscope
###########################################################################
oscillatorId = raw_input("Enter the oscillator id: ")
requiredFrequency = 125*(10**6)
totalTests = 100

totalFails = 0
totalCounts = 0
totalFrequency = 0
testResults = {}
for iTest in range(1,totalTests+1,1):
	###########################################################################
	if(iTest == 0): 
		functions.printSpecial("Starting test")
	###########################################################################
	turnPower("OFF", iTest)
	turnPower("ON", iTest)

	###########################################################################
	if(iTest == 0):
		functions.printSpecial("Checking Oscilloscope")
	###########################################################################

	#Return data points currently displayed on the screen (600 points)
	oscilloscopeDevice.write(":WAV:POIN:MODE NOR")

	#Set the format of the waveform data to BYTE (int8: -128 to 127)
	oscilloscopeDevice.write(":WAV:FORM BYTE")
	oscilloscopeDevice.write(":WAV:FORM?")
	if(iTest == 0):
		print "Format of the waveform data is ", oscilloscopeDevice.read().strip()

	#:MEASure:SOURce <source>- Select the measurement channel
	#oscilloscopeChannels = [" CHAN1", " CHAN2", " CHAN3"]
	oscilloscopeChannels = [" CHAN1"]

	waveFormData = []
	timeInterval = []
	oscilloscopeFrequency = []
	for iChannel in oscilloscopeChannels:
		if(iTest == 0):
			oscilloscopeDevice.write(":MEAS:SOUR"+iChannel)
			oscilloscopeDevice.write(":MEAS:SOUR?")
			print "Checking ",oscilloscopeDevice.read().strip()

		#Measure the frequency of signal
		oscilloscopeDevice.write(":MEAS:FREQ?"+iChannel)
		oscilloscopeFrequency.append(oscilloscopeDevice.read())
		if(iTest == 0):        	
			print "Oscilloscope measured frequency is ",oscilloscopeFrequency[-1]

		#Measure the time interval of the signal
		oscilloscopeDevice.write(":WAV:XINC?"+iChannel)
		timeInterval.append(oscilloscopeDevice.read())
		if(iTest == 0):
			print "Time interval is ", timeInterval[-1]

		#Read in waveform data for the channel
		oscilloscopeDevice.write(":WAV:DATA?"+iChannel)

		#Create numpy array for each channel
		waveFormData.append(np.frombuffer(oscilloscopeDevice.read(), "B"))

	###########################################################################
	if(iTest == 0):
		print
		functions.printSpecial("Data Analysis")
	###########################################################################
	iName = 0
	for iChannelData in waveFormData:
		if(iTest == 0):
			print "Analyzing oscillator id: ", oscillatorId
		print "Test no. ", iTest
		xPoints = []
		yPoints = []
		iCount = 0
		for iData in iChannelData:
			yData = (iData & 0xFFF)
			yPoints.append(yData)
			xPoints.append(iCount)
			iCount = iCount + 1
	
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
		timeScale = float(timeInterval[iName])
		signal = np.array(yPoints, dtype=float)
		yFftPoints= np.fft.fft(signal)
		nLengthData = signal.size
		xFftPoints = np.fft.fftfreq(nLengthData, d=timeScale)

		#One side frequency
		#The zeo frequency is in the first postion of the array, 
		#followed by the positve frequencies in acscending order, and then
		#the negative frequencies in descending order 
		xFftPoints = xFftPoints[range(nLengthData/2)]
		yFftPoints = yFftPoints[range(nLengthData/2)]

		axis2 = chFigure.add_subplot(2,1,2)
		axis2.plot(xFftPoints, 20*np.log10(abs(yFftPoints)), color='g', alpha=0.5)
		functions.setTitle(axis2, '', 'Frequency (Hz)', '')
		functions.setTicks(axis2)	
		axis2.set_xlim([0.0,0.75e9])
		axis2.set_ylim([0.0,100.0])

		chFigure.show()
		time.sleep(1)
		chFigure.savefig("../plots/Id_"+oscillatorId+"_test_"+str(iTest)+".png")
		plt.close(chFigure)

		#Need to store the frequency
		#The zeroth coefficient is the average value of the signal over the interval	
		yFftPoints = yFftPoints[1:]
		xFftPoints = xFftPoints[1:]
		maxY = np.argmax(abs(yFftPoints))
		maxX = xFftPoints[maxY]
		print 'Oscilloscope measured frequency: ', oscilloscopeFrequency[iName].strip()
		print 'FFT calculated frequency: %.3e' %(maxX)
		print
		
		if maxX != requiredFrequency:
			totalFails = totalFails +1

		if totalFails >= 2:
			print 'Two fails!!! Exiting'
			sys.exit(0)

		testResults[iTest] = maxX
		
		totalCounts = totalCounts + 1
		totalFrequency = totalFrequency + maxX

		iName = iName + 1

turnPower("OFF", 1)

###########################################################################
#Summary of results
###########################################################################
with open("../jsonFiles/"+oscillatorId+".json", 'wb') as outFile:
	json.dump(testResults, outFile)

functions.printSpecial("Printing results")
averageFrequency = totalFrequency/totalCounts
print
if averageFrequency == requiredFrequency:
	print "Oscillator Passed!!!!"
else:
	print "Oscillator Failed!!!!"
print
print "Printing results of each test:"
print testResults
print






























