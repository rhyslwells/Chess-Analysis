# ============================================================================
# FILE 2: src/components/__init__.py
# ============================================================================
"""
Component package initialization.
Exports all component modules for easy importing.
"""

from . import (
    sidebar,
    landing,
    overview,
    rating,
    results,
    openings,
    opponent,
    probability,
    game_length,
    competitor,
)

__all__ = [
    "sidebar",
    "landing",
    "overview",
    "rating",
    "results",
    "openings",
    "opponent",
    "probability",
    "game_length",
    "competitor",
]
