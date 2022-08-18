try:
    from ._version import version as __version__
except ImportError:
    __version__ = "unknown"

# must import before hg since we extend higlass_schema behavior
from higlass_schema import * # isort: skip

import hg.tilesets
from hg.api import *
from hg.fuse import fuse
from hg.server import server
from hg.tilesets import remote
from hg.utils import Scale 

bigwig = server.register(hg.tilesets.bigwig)
multivec = server.register(hg.tilesets.multivec)
cooler = server.register(hg.tilesets.cooler)
