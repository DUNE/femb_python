import os
import sys
import time

from femb_python.configuration import CONFIG

class TEST_QUAD_EPCS(object):

    def __init__(self, datadir="data", outlabel="OscillatorTesting"):
        self.outpathlabel = os.path.join(datadir, outlabel)
        self.femb_config = CONFIG()

        self.nFlashes = 4
        self.nPages = 1
        
    def doTesting(self):
        #Initialize board
        self.femb_config.initBoard()

        #Loop through flashes
        for iFlash in range(4):
            #Check the status
            print("Checking status of flash %s" %(iFlash))
            boardStatus = self.femb_config.readStatus(iFlash)
            if(boardStatus != 0):
                 print("Error!! Status before erasing is bad.")
                 return
             
            #Erase Flash 
            self.femb_config.eraseFlash(iFlash)
            boardStatus = self.femb_config.readStatus(iFlash)
            tries = 0
            while(boardStatus != 0 and tries <= 5):
                print("Error!! Status after erasing is bad. Trying again.")
                self.femb_config.eraseFlash(iFlash)
                boardStatus = self.femb_config.readStatus(iFlash)
                tries +=1

            if(tries > 5):
                print("Flash %s has a problem. Please check and retry again!\nExiting!\n" %(iFlash))
                return

            #Check a page (page 5 here) to make sure if things make sense; memory should be erased to 0xFFFFFFFF
            outputData = self.femb_config.readFlash(iFlash, 5)
            print("Printing page 5 of flash %s" %(iFlash))
            
        print("Done erasing flashes! Begining the tests.")
        
        #Loop over flashes and pages
        for iFlash in range(self.nFlashes):
            for iPage in range(self.nPages):
                inputData = [987]*64 #thing to work on

                print("Input data is:")
                print(inputData)
                
                self.femb_config.programFlash(iFlash, iPage, inputData)
                outputData = self.femb_config.readFlash(iFlash, iPage)
                print(outputData)

def main():
    datadir = sys.argv[1]
    outlabel = sys.argv[2]

    epcsTest = TEST_QUAD_EPCS(datadir, outlabel)

    #Begin testing
    epcsTest.doTesting()


    
if __name__ == '__main__':
    main()
