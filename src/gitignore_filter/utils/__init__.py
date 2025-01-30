"""ユーティリティ関数と共通機能を提供するモジュール。

このモジュールはパス操作、キャッシュ機能、
pathspec関連のユーティリティなど、共通で使用される機能を提供します。
"""

from .cache import PatternCache, get_global_cache
from .path import make_relative, normalize_path, split_path
from .pathspec_util import create_pattern_spec, match_path, match_paths, pattern_matches

__all__ = [
    'PatternCache',
    'get_global_cache',
    'make_relative',
    'normalize_path',
    'split_path',
    'create_pattern_spec',
    'match_path',
    'match_paths',
    'pattern_matches'
]
