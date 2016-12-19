#!/bin/bash
g++ -std=c++11 -o parseBinaryFile parseBinaryFile.cxx `root-config --cflags --glibs`
g++ -std=c++11 -o processNtuple_simpleMeasurement processNtuple_simpleMeasurement.cxx `root-config --cflags --glibs`
g++ -std=c++11 -o processNtuple_noiseMeasurement processNtuple_noiseMeasurement.cxx `root-config --cflags --glibs`
g++ -std=c++11 -o processNtuple_gainMeasurement processNtuple_gainMeasurement.cxx `root-config --cflags --glibs`
mkdir data
