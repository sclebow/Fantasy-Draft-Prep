import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from espn_api import football

# Place shared constants and functions here
SCORING_MULTIPLIER_DICT = {
    "PY": 0.04,
    "PTD": 4,
    "INT": -2,
    "2PC": 2,
    "RY": 0.01,
    "RTD": 6,
    "2PR": 2,
    "REY": 0.1,
    "REC": 0.5,
    "2PRE": 2,
    "PAT": 1,
    "FGM": -1,
    "FG0": 3,
    "FG40": 4,
    "FG50": 5,
    "FG60": 5
}

ROSTER_SPOTS_PER_POSITION_DICT = {
    "QB": {"starters": 1, "max": 4, "likely_benched": 2},
    "RB": {"starters": 2, "max": 8, "likely_benched": 2},
    "WR": {"starters": 2, "max": 8, "likely_benched": 2},
    "TE": {"starters": 1, "max": 3, "likely_benched": 1},
    "K": {"starters": 1, "max": 3, "likely_benched": 0},
    "DST": {"starters": 1, "max": 3, "likely_benched": 0}
}

NUMBER_OF_TEAMS = 10
HEAD_COUNT = 5

# You can add more shared functions here for import in other tab files
