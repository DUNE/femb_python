# femb_python

DUNE/SBND cold electronics UDP readout (python version)

## Installing the femb_python package

You must have the `git` package installed to do anything.

To build ROOT, you must also have some other packages.

For Scientific Linux:

First, run:

```
yum install -y epel-release
```

then

```
yum install -y git make cmake cmake3 gcc-c++ gcc binutils libX11-devel libXpm-devel libXft-devel libXext-devel
```

For Ubuntu:

```
sudo apt install git dpkg-dev cmake g++ gcc binutils libx11-dev libxpm-dev libxft-dev libxext-dev libpng libjpeg
```

Download these two files:

https://repo.continuum.io/archive/Anaconda3-4.2.0-Linux-x86_64.sh

https://root.cern.ch/download/root_v6.08.02.source.tar.gz

and then run the script:

```
bash Anaconda3-4.2.0-Linux-x86_64.sh
```

Install anaconda to the default location and don't add the path to your .bashrc

Now run:

```
export PATH=~/anaconda3/bin:$PATH
```

Now we move on to installing ROOT:

```
tar xzf root_v6.08.02.source.tar.gz
cd root-6.08.02/
./configure --prefix=~/root-6.08.02-pythonAnaconda3 --with-python=~/anaconda3/bin/python3.5 --with-python-incdir=~/anaconda3/include/python3.5m  --with-python-libdir=~/anaconda3/lib/libpython3.5m.so >& logConfigure
make >& logBuild
make install >& logInstall
```

You may have to replace cmake3 with cmake on Ubuntu and other OS's or run the
configure step twice.

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
git clone https://github.com/jhugon/femb_python.git
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
