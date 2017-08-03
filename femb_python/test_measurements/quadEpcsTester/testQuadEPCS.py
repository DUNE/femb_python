import os
import sys
import time
import random

from femb_python.configuration import CONFIG

class TEST_QUAD_EPCS(object):

    def __init__(self, datadir="data", outlabel="OscillatorTesting"):
        self.outpathlabel = os.path.join(datadir, outlabel)
        self.femb_config = CONFIG()

        self.nFlashes = 4
        self.nPages = 10
        
    def doTesting(self):
        #Initialize board
        self.femb_config.initBoard()

        #Loop through flashes first and check status + erase
        for iFlash in range(self.nFlashes):
            #Check the status
            print("\nChecking status of flash %s" %(iFlash))
            boardStatus = self.femb_config.readStatus(iFlash)
            if(boardStatus != 0):
                 print("Error!! Status before erasing is bad.\n")
                 return
             
            #Erase Flash 
            self.femb_config.eraseFlash(iFlash)
            boardStatus = self.femb_config.readStatus(iFlash)
            iTries = 0
            while(boardStatus != 0 and tries <= 5):
                iTries +=1
                print("Error!! Status after erasing is bad. Trying again. Try no. %s" %(iTries))
                self.femb_config.eraseFlash(iFlash)
                boardStatus = self.femb_config.readStatus(iFlash)

            if(iTries > 5):
                print("Flash %s has a problem. Please check and retry again!\nExiting!\n" %(iFlash))
                return

            #Check a page (page 5 here) to make sure if things make sense; memory should be erased to 0xFFFFFFFF
            outputData = self.femb_config.readFlash(iFlash, 5)
            print("\nPrinting page 5 of flash %s, expecting all 0xffffffff\n" %(iFlash))
            outputDataHex = [hex(x) for x in outputData]
            print(outputDataHex)
            
        print("\nDone erasing flashes! Begining the tests.\n")

        #Loop over flashes and pages
        flashSuccess = [True]*self.nFlashes
        for iFlash in range(self.nFlashes):
            for iPage in range(self.nPages):
                inputData = []
                for iNum in range(0, 64):
                    num = random.randint(1, 10000000)
                    inputData.append(num)
                
                self.femb_config.programFlash(iFlash, iPage, inputData)
                outputData = self.femb_config.readFlash(iFlash, iPage)

                inputDataHex = [hex(x) for x in inputData]
                outputDataHex = [hex(x) for x in outputData]
                print("\nInput data is:")
                print(inputDataHex)
                print()
                print("\nOutput data is:")
                print(outputDataHex)
                
                isMatch = set(inputData) == set(outputData)
                iTries = 0
                while (not isMatch and iTries <=5):
                    iTries += 1
                    print("*" * 75)
                    print("Input and output data don't match, trying again!\nTry no. %s" %(iTries))
                    print("*" * 75)
                    self.femb_config.programFlash(iFlash, iPage, inputData)
                    outputData = self.femb_config.readFlash(iFlash, iPage)
                    isMatch = set(inputData) == set(outputData)

                    outputDataHex = [hex(x) for x in outputData]
                    print("\nOutput data is:")
                    print(outputDataHex)
                    
                if(iTries > 5):
                    print("*" * 75)
                    print("Writing to flash %s, page %s failed!" %(iFlash, iPage))
                    print("*" * 75)                    
                    flashSuccess[iFlash]= False
                else:
                    print("*" * 75)
                    print("Input and output data match for flash %s, page %s!" %(iFlash, iPage))
                    print("*" * 75)
                    
        #Print results
        print("*" * 75)
        print("\nPrinting results:")
        for iFlash in range(self.nFlashes):
            if(flashSuccess[iFlash]):
               print("Flash %s passed!!" %(iFlash))
            else:
               print("Flash %s failed!!" %(iFlash))
        print("*" * 75)


def main():
    datadir = sys.argv[1]
    outlabel = sys.argv[2]

    epcsTest = TEST_QUAD_EPCS(datadir, outlabel)

    #Begin testing
    epcsTest.doTesting()


if __name__ == '__main__':
    main()
