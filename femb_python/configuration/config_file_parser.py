import configparser

class CONFIG_FILE(object):
    """
    This class reads the .ini configuration files and makes configuration data available.
    The configuration file can have three sections, BOARD, FE_ASIC, and ADC_ASIC.
    The FE_ASIC and FE_ASIC sections are only present if those chips are present on
    the board
    """
    def __init__(self,filename):
      """
      Constructor. Uses filename string to read configuration
      """
      self.filename = filename
      self.parser = configparser.ConfigParser()
      self.parser.read(filename)

    def hasADC(self):
      if "ADC_CONFIGURATION" in self.parser:
        return True
      else:
        return False

    def hasFE(self):
      if "FE_CONFIGURATION" in self.parser:
        return True
      else:
        return False

    def get(self,section,key,isBool=False):
      """
      Read a configuration variable with name 'key' in section 'section'
      The return type is always a string, unless isBool is True, then it is bool.
      """
      if section in self.parser:
        if key in self.parser[section]:
          if isBool:
            return self.parser[section].getboolean(key)
          else:
            return self.typeConvert(self.parser[section][key])
        else:
          raise Exception("Configuration file '{0}', section '{1}' doesn't have key '{2}'".format(self.filename,section,key))
      else:
        raise Exception("Configuration file '{0}' doesn't have a '{1}' section".format(self.filename,section))

    def typeConvert(self,instring):
      """
      Automatically converts instring to the appropriate type. 
      Lists identified with [] as the first and last characters, and commas seperate entries (white space is erased)
      Floats must have '.' to be floats
      Hex, Octal, and Binary literals must follow the python convention and start with: 0x, 0o, 0b
      """
      if instring[0] == "[" and instring[-1] == "]": # it's a list
        instring = instring[1:-1]
        instring = instring.replace(' ','')
        instring = instring.replace('\n','')
        instring = instring.replace('\r','')
        instring = instring.replace('\t','')
        listOfStrings = instring.split(',')
        result = [self.typeConvert(x) for x in listOfStrings]
        return result
      if instring[:2] == "0x":
        try:
          result = int(instring,16) # it's a hex int
          return result
        except:
          pass
      if instring[:2] == "0o":
        try:
          result = int(instring,8) # it's an octal int
          return result
        except:
          pass
      if instring[:2] == "0b":
        try:
          result = int(instring,2) # it's a binary int
          return result
        except:
          pass
      try:
        result = int(instring) # it's a decimal int
        return result
      except:
        pass
      try:
        result = float(instring) # it's a float
        return result
      except:
        pass
      result = instring # it's a string
      return result

    def listKeys(self,section):
      """
      List the keys in section
      """
      if section in self.parser:
        return list(self.parser[section])
      else:
        raise Exception("Configuration file '{0}' doesn't have a '{1}' section".format(self.filename,section))

if __name__ == "__main__":
    cf = CONFIG_FILE("35t.ini")
    print(cf.boardParam("REG_RESET"))
    print(cf.adcParam("REG_ASIC_RESET"))
    print(cf.adcParam("ADC_TESTPATTERN"))
    for i in cf.adcParam("ADC_TESTPATTERN"):
        print(hex(i))
    print(cf.hasFE())
    print(cf.hasADC())
