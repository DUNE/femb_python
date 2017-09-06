import os
import sys
import time
import random
import json

from femb_python.configuration import CONFIG

class TEST_QUAD_EPCS(object):

    def __init__(self, datadir="data", outlabel="OscillatorTesting"):
        self.outpathlabel = os.path.join(datadir, outlabel)
        self.femb_config = CONFIG()

        self.nFlashes = 4
        self.nPages = 20
        self.nWriteTries = 3
        self.printData = False
        
    def doTesting(self):
        print("*" * 75)
        #Initialize board
        self.femb_config.initBoard()
        print("*" * 75)
                
        #Loop through flashes and erase
        for iFlash in range(self.nFlashes):
            self.femb_config.eraseFlash(iFlash)

        #Writing to flash is skipped if there was a problem erasing it
        flashToSkip = [True]*self.nFlashes
        timeToErase = [9999]*self.nFlashes        

        print("*" * 75)
        #Erase bulk cycle time for EPCS64 is 160s max, trying 3 mins (180s)
        print("\n\nWaiting 3 mins for flashes to be erased\n")
        startTime = time.time()
        for t in range(180):
            for iFlash in range(self.nFlashes):
                if flashToSkip[iFlash] == False: continue 
                status = self.femb_config.readStatus(iFlash)
                if(status == 0):
                    flashToSkip[iFlash] = False
                    timeToErase[iFlash] = time.time() - startTime
        time.sleep(1)

        #Check a page (page 5 here) to make sure if things make sense; memory should be erased to 0xFFFFFFFF
        for iFlash in range(self.nFlashes):
            if flashToSkip[iFlash]:
                print("Couldn't erase flash %s, skipping it\n" %(iFlash))
            else:
                print("Successfully erased flash %s\n" %(iFlash))

                if self.printData:
                    outputData = self.femb_config.readFlash(iFlash, 5)
                    print("\nPrinting page 5 of flash %s, expecting all 0xffffffff\n" %(iFlash))
                    outputDataHex = [hex(x) for x in outputData]
                    print(outputDataHex)
        print("*" * 75)

        print("*" * 75)
        print("\nDone erasing flashes! Begining the tests.\n")
         
        #Loop over flashes, pages, and tries
        writeSuccess = [[[9999 for iT in range (0, self.nWriteTries)] for iP in range(0, self.nPages)] for iF in range(0, self.nFlashes)]
        # 9999: flash skipped; 0: write fail; 1: write successful; -1: write previously successful (no attempt made to write again)
        for iFlash in range(self.nFlashes):
            if flashToSkip[iFlash]: continue
            for iPage in range(self.nPages):
                isMatch = False
                for iTry in range(self.nWriteTries):
                    if isMatch:
                        writeSuccess[iFlash][iPage][iTry] = -1
                        continue
                    print("\nWriting/Reading flash %s, page %s, try %s" %(iFlash, iPage, iTry))
                    inputData = []
                    for iNum in range(0, 64):
                        num = random.randint(1, 10000000)
                        inputData.append(num)

                    self.femb_config.programFlash(iFlash, iPage, inputData)

                    #Write byte cycle time for EPCS64 is 5s max
                    for t in range(5):
                        status = self.femb_config.readStatus(iFlash)
                        time.sleep(1)
                        if(status == 0):
                            break
                                                                                
                    outputData = self.femb_config.readFlash(iFlash, iPage)
                    if self.printData:
                        inputDataHex = [hex(x) for x in inputData]
                        outputDataHex = [hex(x) for x in outputData]
                        print("\nInput data is:")
                        print(inputDataHex)
                        print()
                        print("\nOutput data is:")
                        print(outputDataHex)

                    isMatch = (set(inputData) == set(outputData))
                    if isMatch:
                        writeSuccess[iFlash][iPage][iTry]  = 1
                        print("Success!!")
                    else:
                        writeSuccess[iFlash][iPage][iTry]  = 0
                        print("Failed!!")
                                    
        #Print the results
        flashSuccess = [False]*self.nFlashes
        failedPages = [0]*self.nFlashes
        for iFlash in range(self.nFlashes):
            for iPage in range(self.nPages):
                failedPage = True
                for iTry in range(self.nWriteTries):
                    if writeSuccess[iFlash][iPage][iTry] == 1:
                        flashSuccess[iFlash] = True
                        filedPage = False
                if failedPage:
                    failedPages[iFlash] +=1
        print("*" * 75)

        print("*" * 75)
        print("Printing results:")
        print("\nTested %s flashes over %s pages (with %s write tries)." %(self.nFlashes, self.nPages, self.nWriteTries))
        for iFlash in range(self.nFlashes):
            if flashSuccess[iFlash]:
                print("\nFlash %s passed!!" %(iFlash))
                print("\tErase time: %.4s seconds" %(timeToErase[iFlash]))
            else:
                print("\nFlash %s failed!!" %(iFlash))
                if flashToSkip[iFlash]:
                    print("\tIt failed during erase")
                else:
                    print("\tIt failed on %s pages" %(failedPages[iFlash]))
                    print("\tErase time: %.4s seconds" %(timeToErase[iFlash]))
        print("*" * 75)

        #Save the results
        with open(self.outpathlabel+".json", 'w') as outFile:
            json.dump({'Passed? : ':flashSuccess}, outFile, indent=4)
            json.dump({'Failed pages: ':failedPages}, outFile, indent=4)
            json.dump({'Erase time : ':timeToErase}, outFile, indent=4)
            json.dump(writeSuccess, outFile, indent=4)
            
def main():
    datadir = sys.argv[1]
    outlabel = sys.argv[2]

    epcsTest = TEST_QUAD_EPCS(datadir, outlabel)

    #Begin testing
    epcsTest.doTesting()


if __name__ == '__main__':
    main()
