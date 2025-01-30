from pathlib import Path

import pytest

from gitignore_filter.patterns.base import BasePattern


# ヘルパークラスとしてテストモジュールの外に定義
class _TestPatternImpl(BasePattern):
    """テスト用の具象クラス - ヘルパー実装"""

    def match(self, path):
        return True

    def match_file(self, path):
        return not self.is_directory_only

    def match_directory(self, path):
        return True


def test_base_pattern_initialization():
    """BasePatternの初期化テスト"""
    # 基本的な初期化
    pattern = _TestPatternImpl("*.txt")
    assert pattern.pattern == "*.txt"
    assert pattern.base_path is None
    assert not pattern.negated

    # 否定パターン
    pattern = _TestPatternImpl("*.txt", negated=True)
    assert pattern.negated

    # ベースパス付き
    pattern = _TestPatternImpl("*.txt", base_path="/base/path")
    assert pattern.base_path == "/base/path"


def test_pattern_string_representation():
    """パターンの文字列表現テスト"""
    # 通常のパターン
    pattern = _TestPatternImpl("*.txt")
    assert "_TestPatternImpl(*.txt)" in str(pattern)

    # 否定パターン
    pattern = _TestPatternImpl("*.txt", negated=True)
    assert "_TestPatternImpl(!*.txt)" in str(pattern)

    # ベースパス付き
    pattern = _TestPatternImpl("*.txt", base_path="/base/path")
    assert "_TestPatternImpl(*.txt (/base/path))" in str(pattern)


def test_is_directory_only_property():
    """is_directory_onlyプロパティのテスト"""
    # 通常のパターン
    pattern = _TestPatternImpl("*.txt")
    assert not pattern.is_directory_only

    # ディレクトリパターン
    pattern = _TestPatternImpl("temp/")
    assert pattern.is_directory_only

    # スラッシュで始まるが末尾がスラッシュでないパターン
    pattern = _TestPatternImpl("/path/to/file")
    assert not pattern.is_directory_only


def test_is_absolute_property():
    """is_absoluteプロパティのテスト"""
    # 相対パターン
    pattern = _TestPatternImpl("*.txt")
    assert not pattern.is_absolute

    # 絶対パターン
    pattern = _TestPatternImpl("/path/to/file")
    assert pattern.is_absolute

    # ディレクトリパターン（絶対パス）
    pattern = _TestPatternImpl("/path/to/dir/")
    assert pattern.is_absolute


def test_path_object_support():
    """Pathオブジェクトのサポートテスト"""
    pattern = _TestPatternImpl("*.txt")
    path = Path("test.txt")

    # 各メソッドがPathオブジェクトを受け付けることを確認
    assert pattern.match(path)
    assert pattern.match_file(path)
    assert pattern.match_directory(path)


def test_abstract_methods():
    """抽象メソッドの実装強制のテスト"""
    class IncompletePattern(BasePattern):
        pass

    # 抽象メソッドを実装していないクラスのインスタンス化を試みる
    with pytest.raises(TypeError):
        IncompletePattern("*.txt")
