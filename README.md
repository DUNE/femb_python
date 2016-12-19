# femb_python

Core functions for DUNE/SBND cold electronics UDP readout (python version)

## Do this first!

You must manually compile the root C++ files into executables before setting up
the python packages. Just run:

./setup.sh

## Python 2

It's a pain to compile ROOT with support for python3, so by default we use
python 2.

Make sure python-setuptools, python-pip, python-virtualenv, python-numpy,
python-matplotlib, and python-gi-cairo are installed on your machine. You also
need to setup some version of ROOT and pyROOT.

Then, for development, create a virtualenv with:

virtualenv --system-site-packages myvirtualenv

activate the virtualenv:

source myvirtualenv/bin/activate

Make sure you have compiled the C++ files with `./setup.sh`, then, from this
directory run:

pip install -e .

Now the package should be setup in development mode. The developement directory
is softlinked into your python path.

The FEMB_CONFIG env var is used to choose a configuration. Give it a file name.
It first searches in the current directory, and if it is not found looks in the
standard files. These include 35t.ini, sbne.ini, and adctest.ini.

## Python 3

If you can get ROOT working with python3, then the package might work with
that. Make sure all of the dependency packages are installed in their python3
version.

Create the virtualenv like:

virtualenv -p /usr/bin/env/python3 --system-site-packages mypython3virtualenv

## Rebuilding

You shouldn't need to redo anything unless you change setup.py or the C++
files. In that case, from this directory, just run:

./setup.sh
pip install -e .

