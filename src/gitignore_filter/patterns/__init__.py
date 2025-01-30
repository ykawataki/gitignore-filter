"""gitignoreパターンの解析と照合を行うモジュール。

このモジュールはgitignoreパターンの解析、保持、
およびファイルパスとのマッチング機能を提供します。
"""

from .base import BasePattern
from .pathspec import PathSpecPattern

__all__ = ['BasePattern', 'PathSpecPattern']
