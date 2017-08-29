# femb_python

DUNE/SBND cold electronics UDP readout (python version)

## Developing on the BNL `hothdaq` systems

The operator will use a release.  Developing the test code can make
use of the installation of ROOT that the release uses.  Set up your
development environment like:

```
virtualenv --system-site-packages -p python3 venv
source venv/bin/activate
source /opt/sw/root-6.09.02/bin/thisroot.sh

git clone git@github.com:DUNE/femb_python.git
cd femb_python/
pip install -e .
./setup.sh
```

Note:
* Later, to reuse the area just repeat the two `source` commands.
* Need to use `pip install -e .` not `python setup.yp develop`.
* You run `./setup.sh` and do not source it.


## Installing on Scientific Linux 7 and Recent Ubuntu/Fedora

femb_python requires ROOT, git, and a set of python packages provided by
Anaconda.

To build ROOT, you must also have some other packages.

For Scientific Linux or Fedora:

First, run:

```
yum install -y epel-release
```

then

```
yum install -y git make cmake cmake3 gcc-c++ gcc gcc-gfortran binutils libX11-devel libXpm-devel libXft-devel libXext-devel ImageMagick
```

For Ubuntu:

```
sudo apt install git dpkg-dev cmake g++ gcc gfortran binutils libx11-dev libxpm-dev libxft-dev libxext-dev libpng libjpeg imagemagick
```

Download these two files:

https://repo.continuum.io/archive/Anaconda3-4.2.0-Linux-x86_64.sh

https://root.cern.ch/download/root_v6.08.02.source.tar.gz

and then run the script:

```
bash Anaconda3-4.2.0-Linux-x86_64.sh
```

Install anaconda to the default location and don't add the path to your .bashrc

Now we move on to installing ROOT:

```
tar xzf root_v6.08.02.source.tar.gz
cd root-6.08.02/
mkdir builddir
cd builddir
cmake3 -DCMAKE_INSTALL_PREFIX=~/root-6.08.02-pythonAnaconda3 -DPYTHON3=ON -DPYTHON_EXECUTABLE=~/anaconda3/bin/python3.5 -DPYTHON_INCLUDE_DIR=~/anaconda3/include/python3.5m -DPYTHON_LIBRARY=~/anaconda3/lib/libpython3.5m.so -Dssl=OFF -Dbuiltin_fftw3=ON .. >& logConfigure
cmake3 --build . >& logBuild
cmake3 --build . --target install >& logInstall
source ~/root-6.08.02-pythonAnaconda3/bin/thisroot.sh
```

You may have to replace cmake3 with cmake on Ubuntu and other OS's or run the
configure step twice.

Now setup anaconda by running:

```
export PATH=~/anaconda3/bin:$PATH
```

Now, on to the femb_python package. In whatever directory you want to work in, run:

```
conda create -n myenv
```

then activate the conda environment with:

```
source activate myenv
```

Now get the package:

```
git clone https://github.com/DUNE/femb_python.git
cd femb_python
```

and setup the package:

```
./setup.sh
pip install -e .
```

You are now all set up. All shell commands begin with femb, so try running
`femb_init_board`.

From a fresh terminal, whenever you want to work with the femb_python package, run:

```
export PATH=~/anaconda3/bin:$PATH
source activate myenv
source ~/root-6.08.02-pythonAnaconda3/bin/thisroot.sh
```

You also need to set the environment variable `FEMB_CONFIG` for most commands.
Running `femb_init_board` will present you with the available choices.

## Alternate Ubuntu Installation

This version uses the system python3 installation

```
sudo apt install git dpkg-dev cmake g++ gcc gfortran binutils libx11-dev libxpm-dev libxft-dev libxext-dev libpng libjpeg imagemagick python3-dev python3-matplotlib python3-numpy
```

Download this file:

https://root.cern.ch/download/root_v6.08.02.source.tar.gz

Now we install ROOT:

```
tar xzf root_v6.08.02.source.tar.gz
cd root-6.08.02/
mkdir builddir
cd builddir
cmake -DCMAKE_INSTALL_PREFIX=~/root-6.08.02-python3 -DPYTHON3=ON -DPYTHON_EXECUTABLE=/usr/bin/python3.5 -DPYTHON_INCLUDE_DIR=/usr/include/python3.5m -DPYTHON_LIBRARY=/usr/lib/python3.5/config-3.5m-x86_64-linux-gnu/libpython3.5.so NUMPY_INCLUDE_DIR=/usr/lib/python3/dist-packages/numpy/core/include -Dssl=OFF -Dbuiltin_fftw3=ON .. >& logConfigure
cmake --build . >& logBuild
cmake --build . --target install >& logInstall
source ~/root-6.08.02-python3/bin/thisroot.sh
```

now go to whatever directory you want femb code to live in and run:

```
git clone https://github.com/DUNE/femb_python.git
virtualenv -p python3 --system-site-packages venv
source venv/bin/activate
cd femb_python
./setup.sh
pip install -e .
```

You are now all set up. All shell commands begin with femb, so try running
`femb_init_board`.

From a fresh terminal, whenever you want to work with the femb_python package,
go to your femb code directory and run:

```
source ~/root-6.08.02-python3/bin/thisroot.sh
source venv/bin/activate
```

You also need to set the environment variable `FEMB_CONFIG` for most commands.
Running `femb_init_board` will present you with the available choices.


## Installing on Scientific Linux 5 or 6

In SL 5 or 6, an older c++ compiler must be used. This means we have to use an
older version of ROOT as well as Python 2. Some functionality may not work,
such as the C++ scripts and possibly other modules that haven't been tested
with Python 2. SL5 also doesn't have git, so you must download a tagged release
from Github.

To build ROOT, you must also have some other packages.

First, run:

```
yum install -y epel-release
```

then

```
yum install -y git make cmake cmake3 gcc-c++ gcc gcc-gfortran binutils libX11-devel libXpm-devel libXft-devel libXext-devel ImageMagick
```

Download these two files:

https://repo.continuum.io/archive/Anaconda2-4.3.0-Linux-x86_64.sh

https://root.cern.ch/download/root_v5.34.36.source.tar.gz

and then run the script:

```
bash Anaconda2-4.3.0-Linux-x86_64.sh
```

Install anaconda to the default location and don't add the path to your .bashrc

Now setup anaconda by running:

```
export PATH=~/anaconda3/bin:$PATH
```

Now we move on to installing ROOT:

```
tar xzf root_v5.34.36.source.tar.gz
cd root/
./configure --prefix=$HOME/root-5.34.36-pythonAnaconda2 --with-python-incdir=$HOME/anaconda2/include/python2.7 --with-python-libdir=$HOME/anaconda2/lib --enable-builtin-freetype --enable-builtin-pcre >& logConfigure
make >& logBuild
make install >& logBuild
source ~/root-5.34.36-pythonAnaconda2/bin/thisroot.sh
```

Now, on to the femb_python package. In whatever directory you want to work in, run:

```
conda create -n myenv
```

then activate the conda environment with:

```
source activate myenv
```

Now get the package. On SL6, run:

```
git clone https://github.com/DUNE/femb_python.git
cd femb_python
```

on SL5, go to https://github.com/DUNE/femb_python then click on the releases
tab. Download one of those and untar it. Go into the resulting directory.

Setup the package:

```
./setup.sh
pip install -e .
```

You are now all set up. All shell commands begin with femb, so try running
`femb_init_board`.

From a fresh terminal, whenever you want to work with the femb_python package, run:

```
export PATH=~/anaconda2/bin:$PATH
source activate myenv
source ~/root-5.34.36-pythonAnaconda2/bin/thisroot.sh
```

You also need to set the environment variable `FEMB_CONFIG` for most commands.
Running `femb_init_board` will present you with the available choices.


## Rebuilding

You shouldn't need to redo anything unless you change setup.py or the C++
files. In that case, from this directory, just run:

```
./setup.sh
pip install -e .
```

## Adding new commands

To add your new script, e.g. `femb_python/test_measurements/rocket/ship.py`,
with main function `main` as a command line command `femb_rocket_ship`, add a
line to `setup.py` in the list `console_scripts` that looks like this:

```
"femb_rocket_ship=femb_python.test_measurements.rocket.ship:main",
```

## Calling compiled C++ executables from python

Use the class in femb_python/configuration/cppfilerunner.py

```
from .configuration.cppfilerunner import CPP_FILE_RUNNER

cppfr = CPP_FILE_RUNNER()

cppfr.call('test_measurements/example_femb_test/parseBinaryFile',["outfilename"])

```

The first argument to call is the path to the binary file from the femb_python
directory, the second argument is a list of arguments to the called executable
command.

There is an example in:

```
femb_python/test_measurements/example_femb_test/doFembTest_simpleMeasurement.py
```
