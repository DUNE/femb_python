from ..femb_udp import FEMB_UDP
from ..configuration.argument_parser import ArgumentParser


def main():
  parser = ArgumentParser(description="Dumps data to stdout")
  parser.addNPacketsArgs(False,1)
  args = parser.parse_args()

  femb = FEMB_UDP()
  data = femb.get_data(args.nPackets)
  for samp in data:
      chNum = ((samp >> 12 ) & 0xF)
      sampVal = (samp & 0xFFF)
      print( str(chNum) + "\t" + str(sampVal) + "\t" + str( hex(sampVal) ) )
