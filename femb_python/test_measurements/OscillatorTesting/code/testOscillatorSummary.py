#!/usr/bin/env python33

import os
import sys
import re
import json
from glob import glob

class OSCILLATOR_TESTING_SUMMARY(object):

        def __init__(self, datadir=None, outlabel=None):
                self.datadir = datadir
                self.outlabel = outlabel
                self.outpathlabel = os.path.join(datadir, outlabel)
                                                	
        def doSummary(self):
                #Testing 100 MHz oscillators
                requiredFrequency = 100*(10**6)
                                
                jsonFiles = glob(self.datadir+"/../OscillatorTestingThermalCycle?/*-?.json")
                jsonFiles.sort()

                resultArray = [["N/A" for iThermalCycle in range(0, 4)] for iChannelNumber in range(0,5)]
                resultArray[0][0] = ""

                resultArray[1][0] = "Channel 1"
                resultArray[2][0] = "Channel 2"
                resultArray[3][0] = "Channel 3"
                resultArray[4][0] = "Channel 4"

                resultArray[0][1] = "Cycle 1"
                resultArray[0][2] = "Cycle 2"
                resultArray[0][3] = "Cycle 3"
                 
                for iFile in jsonFiles:
                        thermalCycle = int(iFile[iFile.rfind("/OscillatorTestingThermalCycle") +30 : iFile.rfind("/")])
                        channelNumber = int(iFile[iFile.rfind("-") +1 : iFile.rfind(".")])

                        result = "Error!"
                        with open(iFile) as jsonData:
                                data = json.load(jsonData)
                                totalCount = 0
                                totalFrequency = 0
                                for test, frequency in data.items():
                                        totalCount = totalCount + 1
                                        totalFrequency = totalFrequency + frequency
                        averageFrequency = totalFrequency/totalCount
                        if averageFrequency  == requiredFrequency:
                                result = "Passed"
                        else:
                                result = "Failed"
                        resultArray[channelNumber][thermalCycle] = result

                print()
                print("*********************************************************************************")
                print("Summary of results:")
                print("*********************************************************************************")
                for iChannelNumber in range(0, 5):
                        print("%s%s%s%s"
                              %(resultArray[iChannelNumber][0].center(20), resultArray[iChannelNumber][1].center(20),
                                resultArray[iChannelNumber][2].center(20), resultArray[iChannelNumber][3].center(20)))
                print("*********************************************************************************")
                print()
                
                #Save the result
                with open(self.outpathlabel+".txt", 'w') as outFile:
                        json.dump(resultArray, outFile)
def main():
        #Standard parameters for the codes: output dir and outlabel
        datadir = sys.argv[1] 
        outlabel = sys.argv[2]
        
        oscTestSummary = OSCILLATOR_TESTING_SUMMARY(datadir, outlabel)

        #Begin Summary
        oscTestSummary.doSummary()
        
if __name__ == '__main__':
        main()
