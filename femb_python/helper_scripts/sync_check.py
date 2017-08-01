from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from builtins import str
from builtins import hex
from future import standard_library
standard_library.install_aliases()
from ..configuration import CONFIG

def main():
    femb_config = CONFIG()
    #for iASIC in range(femb_config.NASICS):
    for iASIC in range(1):
        femb_config.testUnsync(iASIC)
