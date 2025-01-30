from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, Union


class BasePattern(ABC):
    """gitignoreパターンの基底クラス。

    このクラスは.gitignoreパターンの基本的なインターフェースを定義します。
    すべてのパターン実装クラスはこのクラスを継承する必要があります。
    """

    def __init__(self, pattern: str, base_path: Optional[str] = None, negated: bool = False):
        """
        Args:
            pattern: gitignoreパターン文字列
            base_path: パターンの基準となるディレクトリパス
            negated: 否定パターン（!で始まるパターン）かどうか
        """
        self.pattern = pattern
        self.base_path = base_path
        self.negated = negated

    @abstractmethod
    def match(self, path: Union[str, Path]) -> bool:
        """パスがパターンにマッチするかチェックする

        Args:
            path: チェックするパス

        Returns:
            パターンにマッチする場合はTrue
        """
        pass

    @abstractmethod
    def match_file(self, path: Union[str, Path]) -> bool:
        """ファイルパスがパターンにマッチするかチェックする

        ディレクトリパターン（末尾が/のパターン）の場合は常にFalseを返す

        Args:
            path: チェックするファイルパス

        Returns:
            パターンにマッチする場合はTrue
        """
        pass

    @abstractmethod
    def match_directory(self, path: Union[str, Path]) -> bool:
        """ディレクトリパスがパターンにマッチするかチェックする

        Args:
            path: チェックするディレクトリパス

        Returns:
            パターンにマッチする場合はTrue
        """
        pass

    def __repr__(self) -> str:
        """パターンの文字列表現を返す"""
        prefix = "!" if self.negated else ""
        base = f" ({self.base_path})" if self.base_path else ""
        return f"{self.__class__.__name__}({prefix}{self.pattern}{base})"

    @property
    def is_directory_only(self) -> bool:
        """ディレクトリのみにマッチするパターンかどうか

        Returns:
            ディレクトリのみにマッチするパターンの場合はTrue
        """
        return self.pattern.endswith('/')

    @property
    def is_absolute(self) -> bool:
        """絶対パスパターンかどうか（先頭が/で始まる）

        Returns:
            絶対パスパターンの場合はTrue
        """
        return self.pattern.startswith('/')
