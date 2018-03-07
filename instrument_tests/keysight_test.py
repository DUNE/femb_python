import time
import visa
from visa import VisaIOError

class main:
	def life(self):
		rm = visa.ResourceManager('@py')
		#rm.list_resources()
		time.sleep(0.1)
		AFG = rm.open_resource(u'USB0::2391::22279::MY53802422::0::INSTR')	
		AFG.write("*rst")
		AFG.write("*cls")
		
		AFG.write("Source1:Function:Shape ramp")
		AFG.write("Source1:Frequency 1Hz")
		AFG.write("Source1:Voltage:Amplitude 1.8")
		AFG.write("Source1:Voltage:Offset 0.7")

		AFG.write("Source1:Burst:Mode Trigger")
		AFG.write("Source1:Burst:Ncycles 1")
		AFG.write("Source1:Phase:Adjust 180DEG")
		AFG.write("Source1:Burst:State On")
		AFG.write("Initiate1:Continuous OFF")
		
		time.sleep(1000)		
		AFG.write("*TRG")

		return AFG

if __name__ == "__main__":
	main().life()
