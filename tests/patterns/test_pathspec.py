from pathlib import Path

import pytest

from gitignore_filter.patterns.pathspec import PathSpecPattern


@pytest.fixture
def pattern():
    return PathSpecPattern("*.txt")


def test_basic_pattern_matching(pattern):
    """基本的なパターンマッチングのテスト"""
    assert pattern.match("test.txt")
    assert pattern.match("path/to/test.txt")
    assert not pattern.match("test.doc")


def test_directory_only_pattern():
    """ディレクトリのみにマッチするパターンのテスト"""
    pattern = PathSpecPattern("temp/")

    # ディレクトリにマッチ
    assert pattern.match_directory("temp")
    assert pattern.match_directory("path/to/temp")

    # ファイルにはマッチしない
    assert not pattern.match_file("temp/file.txt")
    assert not pattern.match_file("temp")


def test_negated_pattern():
    """否定パターンのテスト"""
    pattern = PathSpecPattern("*.txt", negated=True)

    # 通常のマッチ結果も反転せずnegated属性で判定する。
    assert pattern.match("test.txt")
    assert not pattern.match("test.doc")
    assert pattern.negated


def test_case_sensitive_matching():
    """大文字小文字の区別のテスト"""
    # 大文字小文字を区別する場合
    pattern = PathSpecPattern("*.TXT", case_sensitive=True)
    assert pattern.match("test.TXT")
    assert not pattern.match("test.txt")

    # 大文字小文字を区別しない場合
    pattern = PathSpecPattern("*.TXT", case_sensitive=False)
    assert pattern.match("test.TXT")
    assert pattern.match("test.txt")


def test_path_object_support(pattern):
    """Pathオブジェクトのサポートテスト"""
    path = Path("test.txt")
    assert pattern.match(path)
    assert pattern.match_file(path)
    assert not pattern.match_directory(path)


def test_absolute_pattern():
    """絶対パスパターンのテスト"""
    pattern = PathSpecPattern("/root/*.txt")
    assert pattern.is_absolute
    assert pattern.match("root/test.txt")
    assert not pattern.match("other/root/test.txt")


@pytest.mark.parametrize("test_pattern,test_path,expected", [
    ("*.txt", "test.txt", True),
    ("doc/*/*.pdf", "doc/2023/test.pdf", True),
    ("doc/*/*.pdf", "doc/test.pdf", False),
    ("**/temp", "a/b/temp", True),
    ("temp/", "temp/file.txt", True),
    ("!temp/", "temp/file.txt", False),
    ("[0-9]*.txt", "1test.txt", True),
    ("[0-9]*.txt", "test.txt", False),
    ("*.{jpg,jpeg,png}", "test.jpg", True),
    ("*.{jpg,jpeg,png}", "test.gif", False),
])
def test_pattern_variations(test_pattern, test_path, expected):
    """様々なパターンのテスト"""
    pattern = PathSpecPattern(test_pattern)
    assert pattern.match(test_path) == expected


def test_base_path_support():
    """ベースパスのサポートテスト"""
    pattern = PathSpecPattern("*.txt", base_path="/base/path")
    assert pattern.base_path == "/base/path"
    assert pattern.match("test.txt")  # どこにあるtxtファイルでもマッチするように
    assert pattern.match("dir/test.txt")  # サブディレクトリ内のファイルにもマッチ


def test_string_representation():
    """文字列表現のテスト"""
    pattern = PathSpecPattern("*.txt", base_path="/base", negated=True)
    repr_str = str(pattern)
    assert "PathSpecPattern" in repr_str
    assert "*.txt" in repr_str
    assert "/base" in repr_str
    assert "!" in repr_str
