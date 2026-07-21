from __future__ import absolute_import

import os
import sys


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESOURCES = os.path.join(
    ROOT, "IconGrid.glyphsReporter", "Contents", "Resources"
)
if RESOURCES not in sys.path:
    sys.path.insert(0, RESOURCES)
