import logging
from pathlib import Path
from typing import Dict, Optional, Set, Tuple, Union
from weakref import WeakKeyDictionary

logger = logging.getLogger(__name__)


class PatternCache:
    """gitignoreパターンのマッチング結果をキャッシュするクラス。

    WeakKeyDictionaryを使用してメモリリークを防ぎつつ、
    パターンとパスの組み合わせに対するマッチング結果をキャッシュします。
    """

    def __init__(self, max_size: int = 10000):
        """
        Args:
            max_size: キャッシュの最大エントリ数
        """
        self._cache: WeakKeyDictionary = WeakKeyDictionary()
        self._max_size = max_size
        self._hits = 0
        self._misses = 0

    def _is_cacheable(self, pattern: object) -> bool:
        """パターンがキャッシュ可能かどうかをチェックする"""
        try:
            # 弱参照が作成可能かテスト
            from weakref import ref
            ref(pattern)
            return True
        except TypeError:
            return False

    def get(self, pattern: object, path: Union[str, Path], is_dir: bool = False) -> Optional[bool]:
        """キャッシュからマッチング結果を取得する

        Args:
            pattern: パターンオブジェクト
            path: チェックするパス
            is_dir: パスがディレクトリかどうか

        Returns:
            キャッシュされた結果。キャッシュミスの場合はNone
        """
        if not self._is_cacheable(pattern):
            self._misses += 1
            return None

        try:
            cache_dict = self._cache.get(pattern)
            if cache_dict is None:
                self._misses += 1
                return None

            key = (str(path), is_dir)
            result = cache_dict.get(key)
            if result is not None:
                self._hits += 1
            else:
                self._misses += 1
            return result
        except Exception as e:
            logger.debug(f"Cache get error: {e}")
            self._misses += 1
            return None

    def set(self, pattern: object, path: Union[str, Path], is_dir: bool, result: bool) -> None:
        """マッチング結果をキャッシュに保存する

        Args:
            pattern: パターンオブジェクト
            path: チェックしたパス
            is_dir: パスがディレクトリかどうか
            result: マッチング結果
        """
        if not self._is_cacheable(pattern):
            return

        try:
            # パターンごとのキャッシュ辞書を取得または作成
            cache_dict = self._cache.get(pattern)
            if cache_dict is None:
                cache_dict = {}
                self._cache[pattern] = cache_dict

            # キャッシュサイズをチェック
            if len(cache_dict) >= self._max_size:
                logger.debug(
                    f"Cache for pattern {pattern} is full. Clearing...")
                cache_dict.clear()

            key = (str(path), is_dir)
            cache_dict[key] = result
        except Exception as e:
            logger.debug(f"Cache set error: {e}")

    def clear(self) -> None:
        """キャッシュをクリアする"""
        self._cache.clear()
        self._hits = 0
        self._misses = 0

    @property
    def hit_ratio(self) -> float:
        """キャッシュのヒット率を計算する

        Returns:
            ヒット率（0.0 - 1.0）
        """
        total = self._hits + self._misses
        return self._hits / total if total > 0 else 0.0

    def get_stats(self) -> Dict[str, Union[int, float]]:
        """キャッシュの統計情報を取得する

        Returns:
            統計情報を含む辞書
        """
        return {
            'hits': self._hits,
            'misses': self._misses,
            'hit_ratio': self.hit_ratio,
            'patterns': len(self._cache),
        }


# グローバルなキャッシュインスタンス
_global_cache = PatternCache()


def get_global_cache() -> PatternCache:
    """グローバルなパターンキャッシュを取得する"""
    return _global_cache
