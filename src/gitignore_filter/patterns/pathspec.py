from pathlib import Path
from typing import Optional, Union

from pathspec import PathSpec

from ..utils import pathspec_util
from .base import BasePattern


class PathSpecPattern(BasePattern):
    def __init__(
        self,
        pattern: str,
        base_path: Optional[str] = None,
        negated: bool = False,
        case_sensitive: bool = True
    ):
        super().__init__(pattern, base_path, negated)
        self.case_sensitive = case_sensitive

        # 中括弧展開パターンの処理
        if '{' in pattern and '}' in pattern:
            start = pattern.index('{')
            end = pattern.index('}')
            prefix = pattern[:start]
            suffix = pattern[end + 1:]
            alternatives = pattern[start + 1:end].split(',')
            patterns = [f"{prefix}{alt}{suffix}" for alt in alternatives]
        else:
            patterns = [pattern]

        # ベースパスがある場合、パターンに相対パスとして追加
        if base_path:
            normalized_base = base_path.strip('/')
            patterns = [
                f"**/{p}" if not p.startswith('/') else p[1:]
                for p in patterns
            ]

        self._spec = pathspec_util.create_pattern_spec(
            patterns, case_sensitive=case_sensitive
        )

    def match(self, path: Union[str, Path]) -> bool:
        """パスがパターンにマッチするかチェックする"""
        if self.base_path:
            # ベースパスがある場合、相対パスとして扱う
            path_str = str(path)
            if not path_str.startswith('/'):
                path_str = f"**/{path_str}"
        else:
            path_str = str(path)

        return pathspec_util.match_path(
            self._spec, path_str, case_sensitive=self.case_sensitive)

    def match_file(self, path: Union[str, Path]) -> bool:
        """ファイルパスがパターンにマッチするかチェックする"""
        if self.is_directory_only:
            return False
        return self.match(path)

    def match_directory(self, path: Union[str, Path]) -> bool:
        """ディレクトリパスがパターンにマッチするかチェックする"""
        path_obj = Path(path)
        if path_obj.is_file() or (not path_obj.exists() and path_obj.suffix):
            return False

        path_str = str(path)
        if not path_str.endswith('/'):
            path_str += '/'
        return self.match(path_str)
