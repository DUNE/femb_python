# femb_python

Core functions for DUNE/SBND cold electronics UDP readout (python version)

Make sure python-setuptools, python-pip, python-virtualenv, python-numpy, and python-matplotlib are installed on your machine. You also need to setup some version of ROOT and pyROOT.

Then, for development, create a virtualenv with:

virtualenv -p /usr/bin/env/python3 --system-site-packages mypython3virtualenv

activate the virtualenv:

source mypython3virtualenv/bin/activate

then, from this directory run:

pip install -e .

Now the package should be setup in development mode. The developement directory is softlinked into your python path.

The FEMB_CONFIG env var is used to choose a configuration. Give it a file name. It first searches in the current directory, and if it is not found looks in the standard files. These include 35t.ini, sbne.ini, and adctest.ini.
