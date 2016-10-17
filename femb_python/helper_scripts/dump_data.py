from ..femb_udp import FEMB_UDP

def main():
  femb = FEMB_UDP()
  data = femb.get_data(1)
  for samp in data:
      chNum = ((samp >> 12 ) & 0xF)
      sampVal = (samp & 0xFFF)
      print( str(chNum) + "\t" + str(sampVal) + "\t" + str( hex(sampVal) ) )
