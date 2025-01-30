import os
from pathlib import Path

import pytest

from gitignore_filter.utils.pathspec_util import (
    create_pattern_spec,
    match_path,
    match_paths,
    pattern_matches,
)


def test_create_pattern_spec_basic():
    patterns = ["*.txt", "!important.txt", "temp/"]
    spec = create_pattern_spec(patterns)
    assert spec is not None
    assert len(spec.patterns) == 3


def test_create_pattern_spec_empty_and_comments():
    patterns = ["", "  ", "#comment", "*.txt"]
    spec = create_pattern_spec(patterns)
    assert len(spec.patterns) == 1  # 空行とコメントは除外される


def test_create_pattern_spec_case_sensitivity():
    patterns = ["*.TXT"]
    # 大文字小文字を区別する場合
    spec_sensitive = create_pattern_spec(patterns, case_sensitive=True)
    assert not match_path(spec_sensitive, "test.txt")
    assert match_path(spec_sensitive, "test.TXT")

    # 大文字小文字を区別しない場合
    spec_insensitive = create_pattern_spec(patterns, case_sensitive=False)
    assert match_path(spec_insensitive, "test.txt")
    assert match_path(spec_insensitive, "test.TXT")


@pytest.mark.parametrize("pattern,path,expected", [
    ("*.txt", "test.txt", True),
    ("*.txt", "test.doc", False),
    ("!important.txt", "important.txt", False),  # 否定パターン
    ("dir/*.txt", "dir/test.txt", True),
    ("dir/*.txt", "other/test.txt", False),
    ("**/temp", "a/b/temp", True),  # 再帰マッチ
    ("temp/", "temp/file.txt", True),  # ディレクトリ指定
    ("temp/", "temp", False),  # ディレクトリ指定は末尾スラッシュ必須
])
def test_match_path(pattern, path, expected):
    spec = create_pattern_spec([pattern])
    assert match_path(spec, path) == expected


def test_match_path_with_path_object():
    spec = create_pattern_spec(["*.txt"])
    path = Path("test.txt")
    assert match_path(spec, path)


def test_match_paths():
    paths = ["test.txt", "test.doc", "important.txt", "temp/test.txt"]
    patterns = ["*.txt", "!important.txt"]
    spec = create_pattern_spec(patterns)

    matches = match_paths(spec, paths)
    assert "test.txt" in matches
    assert "temp/test.txt" in matches
    assert "important.txt" not in matches
    assert "test.doc" not in matches


def test_pattern_matches():
    # 基本的なマッチング
    assert pattern_matches("*.txt", "test.txt")
    assert not pattern_matches("*.txt", "test.doc")

    # 大文字小文字の区別
    assert pattern_matches("*.TXT", "test.TXT", case_sensitive=True)
    assert not pattern_matches("*.TXT", "test.txt", case_sensitive=True)
    assert pattern_matches("*.TXT", "test.txt", case_sensitive=False)

    # パスオブジェクトでのテスト
    assert pattern_matches("*.txt", Path("test.txt"))


def test_windows_paths():
    # Windowsパスの正規化
    spec = create_pattern_spec(["temp\\*.txt"])
    assert match_path(spec, "temp/test.txt")
    assert match_path(spec, "temp\\test.txt")

    # バックスラッシュを含むパターン
    assert pattern_matches("temp\\*.txt", "temp/test.txt")
    assert pattern_matches("temp/*.txt", "temp\\test.txt")
