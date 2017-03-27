###########################################################################
#USBTMC (USB Test & Measurement Class)
###########################################################################

import os

class DriverUSBTMC:
    """For USBTMC device driver"""

    def __init__(self, deviceName):
        self.deviceName = deviceName
        self.FILE = os.open(deviceName, os.O_RDWR) 
               
    def write(self, writeCommand):
        os.write(self.FILE, writeCommand);

    def read(self, readLength = 4000):
        return os.read(self.FILE, readLength)

    def getID(self):
        self.write("*IDN?")
        return self.read(300)

    def sendReset(self):
        self.write("*RST")
