"""Script generating the Impresso Corpus and Enrichment Release Card.

This card is a JSON file which documents and describes the data within a given release all in one place.
"""

import os
import json
import copy
import fire
from harvesters.utils import transform_value, BITMAP_KEYS
