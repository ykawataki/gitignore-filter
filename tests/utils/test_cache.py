from pathlib import Path
from typing import Dict, Set
from unittest.mock import Mock

import pytest

from gitignore_filter.utils.cache import PatternCache, get_global_cache


@pytest.fixture
def cache():
    """テスト用のキャッシュインスタンスを作成する"""
    return PatternCache(max_size=100)


def test_cache_basic_operation(cache):
    """基本的なキャッシュ操作のテスト"""
    # テスト用のパターンオブジェクト
    pattern = Mock()

    # キャッシュミスの確認
    assert cache.get(pattern, "test.txt") is None

    # 値のセットと取得
    cache.set(pattern, "test.txt", False, True)
    assert cache.get(pattern, "test.txt", False) is True

    # 異なるパスでの取得
    assert cache.get(pattern, "other.txt", False) is None


def test_cache_with_path_objects(cache):
    """Pathオブジェクトを使用したキャッシュ操作のテスト"""
    pattern = Mock()
    path = Path("test.txt")

    cache.set(pattern, path, False, True)
    assert cache.get(pattern, path, False) is True
    assert cache.get(pattern, "test.txt", False) is True
    assert cache.get(pattern, Path("test.txt"), False) is True


def test_cache_directory_flag(cache):
    """ディレクトリフラグの処理テスト"""
    pattern = Mock()
    path = "test"

    # ファイルとしてキャッシュ
    cache.set(pattern, path, False, True)
    assert cache.get(pattern, path, False) is True
    assert cache.get(pattern, path, True) is None  # ディレクトリとして取得

    # ディレクトリとしてキャッシュ
    cache.set(pattern, path, True, False)
    assert cache.get(pattern, path, True) is False
    assert cache.get(pattern, path, False) is True  # 元のファイルのキャッシュは維持


def test_cache_max_size(cache):
    """キャッシュサイズの制限テスト"""
    pattern = Mock()
    max_entries = 100

    # キャッシュを最大サイズまで埋める
    for i in range(max_entries):
        cache.set(pattern, f"file{i}.txt", False, True)

    # すべてのエントリが取得できることを確認
    for i in range(max_entries):
        assert cache.get(pattern, f"file{i}.txt", False) is True

    # さらにエントリを追加
    cache.set(pattern, "overflow.txt", False, True)

    # キャッシュがクリアされていることを確認
    assert cache.get(pattern, "file0.txt", False) is None
    assert cache.get(pattern, "overflow.txt", False) is True


def test_cache_unhashable_pattern():
    """ハッシュ不可能なパターンの処理テスト"""
    cache = PatternCache()
    unhashable_pattern = [1, 2, 3]  # リストはハッシュ不可能

    # エラーを発生させずに処理されることを確認
    assert cache.get(unhashable_pattern, "test.txt") is None
    cache.set(unhashable_pattern, "test.txt", False, True)  # 何も起こらない
    assert cache.get(unhashable_pattern, "test.txt") is None


def test_cache_hit_ratio(cache):
    """キャッシュヒット率の計算テスト"""
    pattern = Mock()

    # 初期状態
    assert cache.hit_ratio == 0.0

    # キャッシュミス
    cache.get(pattern, "test.txt")
    assert cache.hit_ratio == 0.0

    # キャッシュヒット
    cache.set(pattern, "test.txt", False, True)
    cache.get(pattern, "test.txt", False)
    assert cache.hit_ratio == 0.5  # 1 hit, 1 miss

    # さらにヒット
    cache.get(pattern, "test.txt", False)
    assert cache.hit_ratio == 2/3  # 2 hits, 1 miss


def test_cache_clear(cache):
    """キャッシュクリア機能のテスト"""
    pattern = Mock()
    cache.set(pattern, "test.txt", False, True)
    assert cache.get(pattern, "test.txt", False) is True

    cache.clear()
    assert cache.get(pattern, "test.txt", False) is None
    assert cache.hit_ratio == 0.0
    assert cache.get_stats()['hits'] == 0
    assert cache.get_stats()['misses'] == 1


def test_global_cache():
    """グローバルキャッシュの取得テスト"""
    cache1 = get_global_cache()
    cache2 = get_global_cache()
    assert cache1 is cache2  # 同じインスタンスを返すことを確認


def test_cache_stats(cache):
    """キャッシュ統計情報のテスト"""
    pattern = Mock()

    # 初期状態
    stats = cache.get_stats()
    assert stats['hits'] == 0
    assert stats['misses'] == 0
    assert stats['hit_ratio'] == 0.0
    assert stats['patterns'] == 0

    # パターンを追加してアクセス
    cache.set(pattern, "test.txt", False, True)
    cache.get(pattern, "test.txt", False)  # ヒット
    cache.get(pattern, "other.txt", False)  # ミス

    stats = cache.get_stats()
    assert stats['hits'] == 1
    assert stats['misses'] == 1
    assert stats['hit_ratio'] == 0.5
    assert stats['patterns'] == 1
