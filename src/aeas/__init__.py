"""Automated Euclidean Approximation System (AEAS)."""

__version__ = "0.2.0"

from .expr import ExprNode, Op
from .canonicalize import canonicalize
from .evaluate import evaluate, compute_target, clear_cache
from .search import beam_search, baseline_enumerate
from .chebyshev import chebyshev_T, chebyshev_T_float, chebyshev_residual
from .field_search import field_search
