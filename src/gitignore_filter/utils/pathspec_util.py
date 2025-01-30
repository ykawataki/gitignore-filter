import logging
from pathlib import Path
from typing import List, Optional, Union

from pathspec import PathSpec
from pathspec.pattern import Pattern
from pathspec.patterns.gitwildmatch import GitWildMatchPattern
from pathspec.util import normalize_file

logger = logging.getLogger(__name__)


def create_pattern_spec(patterns: List[str], case_sensitive: bool = True) -> PathSpec:
    """与えられたパターンのリストからPathSpecオブジェクトを生成する

    Args:
        patterns: .gitignoreパターンのリスト
        case_sensitive: パターンを大文字小文字を区別するかどうか

    Returns:
        設定済みのPathSpecオブジェクト
    """
    normalized_patterns = []
    for pattern in patterns:
        if not pattern or pattern.startswith("#"):
            continue
        norm_pattern = _normalize_pattern(pattern, case_sensitive)
        if norm_pattern:
            normalized_patterns.append(norm_pattern)

    spec = PathSpec.from_lines(GitWildMatchPattern, normalized_patterns)
    return spec


def _normalize_pattern(pattern: str, case_sensitive: bool = True) -> str:
    """gitignoreパターンを正規化する

    Args:
        pattern: 正規化する.gitignoreパターン
        case_sensitive: 大文字小文字を区別するかどうか

    Returns:
        正規化されたパターン文字列
    """
    # 空白文字を除去
    pattern = pattern.strip()

    # コメント行や空行は無視
    if not pattern or pattern.startswith("#"):
        return ""

    # 最初にパス区切り文字を正規化
    normalized = pattern.replace("\\", "/")

    # エスケープシーケンスを処理
    result = []
    i = 0
    while i < len(normalized):
        if normalized[i] == "\\":
            if i + 1 < len(normalized):
                # エスケープ文字をそのまま追加
                result.append(normalized[i + 1])
                i += 2
            else:
                # パターン末尾のバックスラッシュ
                result.append("\\")
                i += 1
        else:
            result.append(normalized[i])
            i += 1

    normalized = "".join(result)

    # 連続するスラッシュを単一のスラッシュに
    while "//" in normalized:
        normalized = normalized.replace("//", "/")

    # 先頭のドットスラッシュを除去
    if normalized.startswith("./"):
        normalized = normalized[2:]

    # 大文字小文字を区別しない場合は小文字に変換
    if not case_sensitive:
        normalized = normalized.lower()

    return normalized


def match_path(spec: PathSpec, path: Union[str, Path], case_sensitive: Optional[bool] = None) -> bool:
    """パスがPathSpecのパターンにマッチするかチェックする

    Args:
        spec: チェックに使用するPathSpecオブジェクト
        path: チェックするパス
        case_sensitive: パターンを大文字小文字を区別するかどうか（デフォルトはspecの設定に従う）

    Returns:
        パターンにマッチする場合はTrue
    """
    # パスをPOSIX形式に正規化
    normalized = str(path).replace("\\", "/")

    # 大文字小文字を区別しない場合は入力パスも小文字化
    # specのパターンが小文字化されているかどうかをチェック
    if case_sensitive is False or (
        case_sensitive is None and
        any(p.pattern.lower() == p.pattern for p in spec.patterns)
    ):
        normalized = normalized.lower()

    result = spec.match_file(normalized)
    return result


def match_paths(spec: PathSpec, paths: List[Union[str, Path]]) -> List[str]:
    """パスのリストからPathSpecのパターンにマッチするものをフィルタリングする

    Args:
        spec: チェックに使用するPathSpecオブジェクト
        paths: チェックするパスのリスト

    Returns:
        パターンにマッチするパスのリスト
    """
    return [str(p) for p in paths if match_path(spec, p)]


def pattern_matches(pattern: str, path: Union[str, Path], case_sensitive: bool = True) -> bool:
    """単一のgitignoreパターンに対するパスのマッチをチェックする

    Args:
        pattern: チェックする.gitignoreパターン
        path: チェックするパス
        case_sensitive: パターンを大文字小文字を区別するかどうか

    Returns:
        パターンにマッチする場合はTrue
    """
    spec = create_pattern_spec([pattern], case_sensitive)
    return match_path(spec, path, case_sensitive)
