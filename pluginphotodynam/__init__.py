# set this to be any version of PHOEBE supported and tested to work with
# this plugin
_supported_phoebe_versions = ['2.0']


# the rest of this file should remain as is - it checks the version requirements,
# handles setting up the namespace correctly, and registers the plugin with
# phoebe.

import sys

if 'phoebe' not in sys.modules.keys():
    raise ImportError("must import phoebe before importing plugin")

import phoebe

from . import compute
from . import backends

if phoebe.__version__ not in _supported_phoebe_versions+['devel']:
    raise ImportError("this plugin requires one of the following phoebe versions: {}".format(_supported_phoebe_versions))

phoebe.register_plugin(__name__)