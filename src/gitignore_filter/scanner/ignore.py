import logging
from pathlib import Path
from typing import List, Optional

from ..patterns.pathspec import PathSpecPattern
from ..utils.cache import get_global_cache
from ..utils.path import normalize_path

logger = logging.getLogger(__name__)


class GitIgnoreScanner:
    """gitignoreファイルを読み込んでパターンを管理するクラス"""

    def __init__(self, case_sensitive: bool = True):
        """
        Args:
            case_sensitive: パターンの大文字小文字を区別するかどうか
        """
        self.case_sensitive = case_sensitive
        self._patterns: List[PathSpecPattern] = []
        self._cache = get_global_cache()

    def read_file(self, path: Path) -> List[str]:
        """gitignoreファイルを読み込む"""
        if not path.is_file():
            return []

        try:
            with open(path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except UnicodeDecodeError:
            try:
                with open(path, 'r', encoding='latin-1') as f:
                    lines = f.readlines()
            except Exception as e:
                return []

        patterns = []
        for line in lines:
            pattern = line.strip()
            if pattern and not pattern.startswith('#'):
                patterns.append(pattern)

        return patterns

    def add_patterns(self, patterns: List[str], base_path: Optional[str] = None) -> None:
        """パターンをスキャナーに追加する"""
        for pattern in patterns:
            negated = pattern.startswith('!')
            if negated:
                pattern = pattern[1:].strip()

            if pattern:
                if base_path:
                    # ベースパスはパターン追加時の相対パスを保持
                    normalized_base = str(Path(base_path))
                else:
                    normalized_base = None

                pattern_obj = PathSpecPattern(
                    pattern,
                    base_path=normalized_base,
                    negated=negated,
                    case_sensitive=self.case_sensitive
                )
                self._patterns.append(pattern_obj)

    def is_ignored(self, path: str, base_path: Path = Path('.')) -> bool:
        """パスがgitignoreパターンによって無視されるべきかを判定する"""
        full_path = Path(base_path.joinpath(path))
        is_dir = full_path.is_dir() if full_path.exists() else str(full_path).endswith('/')

        matched = False
        for pattern in self._patterns:
            # キャッシュをチェック
            cached_result = self._cache.get(pattern, path, is_dir)
            # パターンとのマッチをチェック
            if is_dir:
                matches = pattern.match_directory(path)
            else:
                matches = pattern.match(path)

            # 結果をキャッシュに保存
            self._cache.set(pattern, path, is_dir, matches)

            if pattern.negated and matches:
                matched = False
                break
            elif matches:
                matched = True
        return matched

    def get_patterns(self) -> List[PathSpecPattern]:
        """登録されているパターンのリストを取得する"""
        return self._patterns.copy()
