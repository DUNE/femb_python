from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()

from .config_module_loader import CONFIGURATION_MODULE_LOADER
loader = CONFIGURATION_MODULE_LOADER()
CONFIG = loader.load()
