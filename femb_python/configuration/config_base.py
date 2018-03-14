""" 
Base class for configuration files. These should be considered the 'public'
methods of the config classes, non-configuration code should only use this set
of functions.  
"""

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import
from builtins import int
from builtins import range
from builtins import hex
from builtins import str
from future import standard_library
standard_library.install_aliases()
from builtins import object

class FEMBConfigError(Exception):
    """Base class exception for femb_python configuration errors"""
    pass

class ConfigADCError(FEMBConfigError):
    """Exception when you can't configure the ADC"""
    pass

class SyncADCError(FEMBConfigError):
    """Exception when you can't sync the ADC"""
    pass

class InitBoardError(FEMBConfigError):
    """Exception when you can't initialize a board"""
    pass

class ReadRegError(FEMBConfigError):
    """Exception when you can't read a register"""
    pass

class FEMB_CONFIG_BASE(object):
    """
    Base class for configuration files. These should be considered the 'public'
    methods of the config classes, non-configuration code should only use this set
    of functions.  
    """

    def __init__(self,exitOnError=True):
        """
        Initialize this class (no board communication here. Should setup self.femb as a femb_udp instance.)
        if exitOnError is false, methods should raise error that subclass FEMBConfigError
        """
        self.femb = None
        self.NASICS = 1
        self.NBOARDS = 1
        self.COLD = False
        self.exitOnError=exitOnError

    def resetBoard(self):
        """
        Send reset to board/asics
        """
        pass

    def initBoard(self):
        """
        Initialize board/asics with default configuration
        """
        pass

    def configAdcAsic(self,Adcasic_regs):
        """
        Configure ADCs with given list of registers
        """
        pass

    def configFeAsic_regs(self,feasic_regs):
        """
        Configure FEs with given list of registers
        """
        pass

    def configFeAsic(self,gain,shape,base,slk=None,slkh=None,monitorBandgap=None,monitorTemp=None):
        """
        Configure FEs with given gain/shape/base values.
        Also, configure leakage current slk = 0 for 500 pA, 1 for 100 pA
            and slkh = 0 for 1x leakage current, 1 for 10x leakage current
        if monitorBandgap is True: monitor bandgap instead of signal
        if monitorTemp is True: monitor temperature instead of signal
        """
        pass

    def configAdcAsic(self,enableOffsetCurrent=None,offsetCurrent=None,testInput=None,
                            freqInternal=None,sleep=None,pdsr=None,pcsr=None,
                            clockMonostable=None,clockExternal=None,clockFromFIFO=None,
                            sLSB=None,f0=None,f1=None,f2=None,f3=None,f4=None,f5=None):
        """
        Configure ADCs
          enableOffsetCurrent: 0 disable offset current, 1 enable offset current
          offsetCurrent: 0-15, amount of current to draw from sample and hold
          testInput: 0 digitize normal input, 1 digitize test input
          freqInternal: internal clock frequency: 0 1MHz, 1 2MHz
          sleep: 0 disable sleep mode, 1 enable sleep mode
          pdsr: if pcsr=0: 0 PD is low, 1 PD is high
          pcsr: 0 power down controlled by pdsr, 1 power down controlled externally
          Only one of these can be enabled:
            clockMonostable: True ADC uses monostable clock
            clockExternal: True ADC uses external clock
            clockFromFIFO: True ADC uses digital generator FIFO clock
          sLSB: LSB current steering mode. 0 for full, 1 for partial (ADC7 P1)
          f0, f1, f2, f3, f4, f5: version specific
        """
        if clockMonostable and clockExternal:
            raise Exception("Only clockMonostable, clockExternal, OR, clockFromFIFO can be true, clockMonostable and clockExternal were set true")
        if clockMonostable and clockFromFIFO:
            raise Exception("Only clockMonostable, clockExternal, OR, clockFromFIFO can be true, clockMonostable and clockFromFIFO were set true")
        if clockExternal and clockFromFIFO:
            raise Exception("Only clockMonostable, clockExternal, OR, clockFromFIFO can be true, clockExternal and clockFromFIFO were set true")

    def selectChannel(self,asic,chan, hsmode= 1 ):
        """
        asic is chip number 0 to 7
        chan is channel within asic from 0 to 15
        hsmode: if 0 then streams all channels of a chip, 
                if 1 only te selected channel
                defaults to 1. Not enabled for all firmware versions
        """
        pass

    def setInternalPulser(self,pulserEnable,pulseHeight):
        """
        pulserEnable = 0 for disable, 1 for enable
        pulseHeight = 0 to 31
        """
        pass

    def syncADC(self):
        """
        Syncronize the ADCs
        Should return isAlreadySynced, latchloc1, latchloc2, phase
        """
        pass
