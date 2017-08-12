import sys
import string
from subprocess import check_call as call
import os
import ntpath
import glob
import struct
import json
import time

#constants
reprocessDirName = str("reprocess")

def main():
  #provide FEMB test directory to reprocess
  if len(sys.argv) != 2 :
    print( "Usage: python reprocessGainMeasurements <results directory>")
    return
  testDir = sys.argv[1]
  print( str("Results directory : ") + str(testDir) )

  #check for executable
  if os.path.isfile( "processNtuple_gainMeasurement" ) == False:
    print( "Must run in same directory as processNtuple_gainMeasurement")
    return

  #get subdirectories
  subdirs = get_immediate_subdirectories(str(testDir))
  if subdirs == None :
    return

  #check if "reprocess" dir is open, create otherwise
  if os.path.isdir( reprocessDirName ) == False:
    os.makedirs( reprocessDirName )

  #create reprocessed results directory
  if os.path.isdir( reprocessDirName + str("/") + str(testDir) ) == False:
    os.makedirs( reprocessDirName + str("/") + str(testDir) )

  #process individual measurements
  for subdir in subdirs:
    rundir = str(testDir) + str(subdir)
    processRunDir( rundir )

#get subdirectory structure
def get_immediate_subdirectories(a_dir):
  if os.path.isdir( str(a_dir) ) == False :
    return None
  return [name for name in os.listdir(a_dir) if os.path.isdir(os.path.join(a_dir, name))]

#copy/process files for an individual measurement
def processRunDir( rundir ):
  #check that original measurement data directory exists
  if os.path.isdir( str(rundir) ) == False:
    return None

  #define new measurement directory name
  newdirName = reprocessDirName + str("/") + str(rundir)

  #create reprocessed results directory
  if os.path.isdir( newdirName ) == False:
    os.makedirs( newdirName )  

  #copy over json + png files, reprocess gain measurements
  for root, dirs, files in os.walk( str(rundir) ):
    gainMeasurementFiles = []
    resultsFiles = []
    for file in files:
      if file.endswith('params.json'):
        call(["cp",str(root)+"/"+str(file),newdirName + str("/.")])
      if file.endswith('results.json'):
        call(["cp",str(root)+"/"+str(file),newdirName+str("/.")])
        resultsFiles.append(str(file))
      if file.startswith('gain') and file.endswith('parseBinaryFile.root'):
        #print( root,"\t",file)
        gainMeasurementFiles.append([root,file,newdirName])
    
    #reprocess gain measurement, require 1 set of parsed data and original results json file
    if (len(gainMeasurementFiles) != 1) or (len(resultsFiles) != 1):
        continue
    processGainMeasurement( gainMeasurementFiles[0][0],gainMeasurementFiles[0][1],gainMeasurementFiles[0][2],resultsFiles[0])

def processGainMeasurement( rootdirName, fileName, newdirName, originalResultsFileName ):
    #check that results json file exists in new directory
    if os.path.isfile( newdirName + "/" + originalResultsFileName ) == False:
      print("ERROR")
      return None
    
    #get base of gain measurement name
    nameBase = fileName[:-20]
    if len(nameBase) == 0:
      return None

    #have gain measurement, reprocess
    call(["./processNtuple_gainMeasurement", rootdirName + str("/") + fileName ])

    #parse output results list into a dictionary, messy
    lines = []
    with open( "output_processNtuple_gainMeasurement.list" ) as infile:
      for line in infile:
        line = line.strip('\n')
        line = line.split(',') #measurements separated by commas
        #parseline is a dictionary for a single channel measurement
        parseline = {}
        for n in range(0,len(line),1):
          word = line[n].split(' ')
          if( len(word) != 2 ):
            continue
          parseline[ str(word[0]) ] = str(word[1])
        lines.append(parseline)

    #add results list to dictionary object
    jsondict = {}
    jsondict['results_reprocessed'] = lines

    #append reporcessed results into original json file
    with open(newdirName + "/" + originalResultsFileName) as f:
       data = json.load(f)

    #data.update(jsondict) #append
    data['results'] = lines

    with open(newdirName + "/" + originalResultsFileName, 'w') as f:
       json.dump(data, f, indent=4)

    #copy image file
    call(["cp","summaryPlot_gainMeasurement.png",newdirName + str("/") + str(nameBase) + str("summaryPlot.png")])

if __name__ == '__main__':
    main()
