"""Automated Euclidean Approximation System (AEAS)."""

__version__ = "0.1.0"

from .expr import ExprNode, Op
from .canonicalize import canonicalize
from .evaluate import evaluate, compute_target, clear_cache
from .search import beam_search, baseline_enumerate
