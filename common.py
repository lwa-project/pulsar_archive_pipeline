"""
Module for storing common configuration values.
"""

import os

__version__ = "0.2"
__all__ = ["DATA_PATH", "DATABASE_PATH", "TZPAR_PATH", "TEMPLATE_PATH", "SCRIPT_PATH", "RDQ_PATH"]


_BASE_PATH = os.path.dirname(os.path.abspath(__file__))

DATA_PATH = "/data/network/recent_data/pulsar/LK018"

DATABASE_PATH = os.path.join(_BASE_PATH, "database")
TZPAR_PATH = os.path.join(_BASE_PATH, "tzpar")
TEMPLATE_PATH = os.path.join(_BASE_PATH, "templates")
SCRIPT_PATH = _BASE_PATH

RDQ_PATH = "/home/jdowell/ClusterManagement/recentDataQueue"
