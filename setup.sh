#!/bin/bash

for cxxfile in $(find . -name '*.cxx' -or -name '*.cc'); do
  exefile=${cxxfile%.*}
  cflagslibs=$(root-config --cflags --glibs)
  command="g++ -std=c++11 -o $exefile $cxxfile $cflagslibs"
  echo $command
  $command
done
