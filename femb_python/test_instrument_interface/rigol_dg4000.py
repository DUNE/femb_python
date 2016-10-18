"""
Interface to Rigol DG4000 Function Generator
"""

import time

VMIN=0.
VMAX=1.8

class RigolDG4000(object):
    """
    Interface to Rigol DG4000 Function Generator
    """

    def __init__(self,filename,sourceNumber=1):
        """
        filename is the file descriptor for the usbtmc object like /dev/usbtmc0
        sourceNumber is either 1 or 2
        """
        self.filename = filename
        self.sourceNumber = sourceNumber
        self.sourceString = ":SOURce{}".format(sourceNumber)
        self.outputString = ":OUTPut{}".format(sourceNumber)

    def writeCommand(self,command):
        """
        Writes a command string to the function generator
        """
        #print("Writing command '{}'".format(command))
        with open(self.filename,'w') as wfile:
            wfile.write(command)
            time.sleep(0.1)

    def stop(self):
        """
        Stops output
        """
        command = self.outputString+":STATe OFF"
        self.writeCommand(command)

    def startSin(self,freq,amp,offset):
        """
        Starts a sin wave with
        freq freqeuncy in Hz
        amp amplitude in V
        offset offset in V
        """
        self.stop()
        if offset - amp < VMIN or offset + amp > VMAX:
            raise Exception("Voltage swings outside of {} to {} V, may damage things".format(VMIN,VMAX))
        commands = [
            self.sourceString+":FUNCtion SINusoid",
            self.sourceString+":FREQuency {:f}".format(freq),
            self.sourceString+":VOLTage:AMPLitude {:f}".format(amp),
            self.sourceString+":VOLTage:OFFSet {:f}".format(offset),
        ]
        for command in commands:
            self.writeCommand(command)
        time.sleep(0.5)
        self.writeCommand(self.outputString+":STATe ON")

    def startDC(self,voltage):
        """
        Starts a DC signal
        voltage in V
        """
        self.stop()
        if voltage < VMIN or voltage > VMAX:
            raise Exception("Voltage swings outside of {} to {} V, may damage things".format(VMIN,VMAX))
        commands = [
            self.sourceString+":FUNCtion DC",
            self.sourceString+":VOLTage:OFFSet {:f}".format(voltage),
        ]
        for command in commands:
            self.writeCommand(command)
        time.sleep(0.5)
        self.writeCommand(self.outputString+":STATe ON")

if __name__ == "__main__":

    fungen = RigolDG4000("/dev/usbtmc0")
    fungen.stop()
    print()
    fungen.startSin(300,0.1,0.2)
    time.sleep(3)
    print()
    fungen.startDC(0.15)
    time.sleep(3)
    print()
    fungen.stop()

#  with open("/dev/usbtmc0",'w') as wfile:
#
#    #wfile.write("*IDN?")
#    #wfile.write(":SOURce1:FUNCtion DC")
#    #wfile.write(":SOURce1:FUNCtion SINusoid")
#    #wfile.write(":SOURce1:FREQuency 1500")
#    #wfile.write(":SOURce1:VOLTage:AMPLitude 0.1")
#    #wfile.write(":SOURce1:VOLTage:OFFSet 0.25")
#    #wfile.write(":OUTPut1:STATe OFF")
  
