from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional, Set


class BaseScanner(ABC):
    """スキャナーの基底クラス。

    このクラスはファイルシステムの走査とgitignoreファイルの
    読み込みに関する基本的なインターフェースを定義します。
    """

    def __init__(self, root_dir: str, case_sensitive: bool = True):
        """
        Args:
            root_dir: 走査を開始するルートディレクトリ
            case_sensitive: ファイル名の大文字小文字を区別するかどうか
        """
        self.root_dir = Path(root_dir).resolve()
        self.case_sensitive = case_sensitive
        self._scanned_paths: Set[Path] = set()
        self._ignore_patterns: Dict[Path, List[str]] = {}

    @abstractmethod
    def scan(self) -> List[str]:
        """ディレクトリを走査してファイルパスのリストを返す。

        Returns:
            gitignoreルールに基づいてフィルタリングされたファイルパスのリスト
        """
        pass

    @abstractmethod
    def read_ignore_file(self, path: Path) -> List[str]:
        """指定されたパスのgitignoreファイルを読み込む。

        Args:
            path: .gitignoreファイルのパス

        Returns:
            読み込んだgitignoreパターンのリスト
        """
        pass

    def is_ignored(self, path: Path) -> bool:
        """パスがgitignoreルールによって無視されるべきかを判定する。

        Args:
            path: チェックするパス

        Returns:
            パスが無視されるべき場合はTrue
        """
        # .gitディレクトリは常に無視
        if '.git' in path.parts:
            return True
        return self._check_ignore_patterns(path)

    @abstractmethod
    def _check_ignore_patterns(self, path: Path) -> bool:
        """gitignoreパターンに対してパスをチェックする。

        Args:
            path: チェックするパス

        Returns:
            パスが無視されるべき場合はTrue
        """
        pass

    def _normalize_path(self, path: Path) -> str:
        """パスを正規化する。

        Args:
            path: 正規化するパス

        Returns:
            正規化されたパス文字列
        """
        normalized = str(path.resolve().relative_to(self.root_dir))
        if not self.case_sensitive:
            normalized = normalized.lower()
        return normalized.replace('\\', '/')

    def get_ignored_patterns(self, dir_path: Optional[Path] = None) -> List[str]:
        """指定されたディレクトリに適用されるgitignoreパターンを取得する。

        Args:
            dir_path: パターンを取得するディレクトリ。Noneの場合は全パターンを返す。

        Returns:
            gitignoreパターンのリスト
        """
        if dir_path is None:
            # 全パターンをフラットなリストにして返す
            return [
                pattern
                for patterns in self._ignore_patterns.values()
                for pattern in patterns
            ]

        # 指定されたディレクトリに適用されるパターンを返す
        return self._ignore_patterns.get(dir_path, [])
