import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Set

from ..utils.path import make_relative, normalize_path
from .base import BaseScanner
from .ignore import GitIgnoreScanner

logger = logging.getLogger(__name__)


class FileSystemScanner(BaseScanner):
    """ファイルシステムを走査してgitignoreルールに基づいてファイルをフィルタリングするクラス"""

    def __init__(self, root_dir: str, case_sensitive: bool = True):
        """
        Args:
            root_dir: 走査を開始するルートディレクトリ
            case_sensitive: ファイル名の大文字小文字を区別するかどうか
        """
        super().__init__(root_dir, case_sensitive)
        self.ignore_scanner = GitIgnoreScanner(case_sensitive=case_sensitive)
        self._patterns_by_dir: Dict[Path, List[str]] = {}

    def scan(self) -> List[str]:
        """ディレクトリを走査してgitignoreルールでフィルタリングされたパスのリストを返す"""
        try:
            # ルートの.gitignoreを読み込む
            root_ignore = self.root_dir / '.gitignore'
            if root_ignore.is_file():
                patterns = self.read_ignore_file(root_ignore)
                self.ignore_scanner.add_patterns(patterns)
                self._patterns_by_dir[self.root_dir] = patterns

            # ファイルシステムを走査
            return list(self._scan_directory(self.root_dir))
        except PermissionError as e:
            logger.warning(f"Permission error while scanning directory: {e}")
            return []
        except Exception as e:
            logger.error(f"Error during directory scan: {e}")
            return []

    def _scan_directory(self, directory: Path) -> Set[str]:
        """再帰的にディレクトリを走査する

        Args:
            directory: 走査するディレクトリ

        Returns:
            gitignoreルールでフィルタリングされたパスのセット
        """
        result: Set[str] = set()

        try:
            # ディレクトリ内の.gitignoreを読み込む
            ignore_file = directory / '.gitignore'
            if ignore_file.is_file() and ignore_file not in self._scanned_paths:
                self._scanned_paths.add(ignore_file)
                patterns = self.read_ignore_file(ignore_file)
                self.ignore_scanner.add_patterns(patterns, str(directory))
                self._patterns_by_dir[directory] = patterns

            # ディレクトリ内のファイルとサブディレクトリを処理
            for entry in os.scandir(directory):
                entry_path = Path(entry.path)
                relative_path = make_relative(entry_path, self.root_dir)

                # シンボリックリンクは無視
                if entry_path.is_symlink():
                    continue

                # gitignoreルールをチェック
                if self.is_ignored(entry_path):
                    continue

                if entry.is_file():
                    # ファイルの場合は結果に追加
                    result.add(relative_path)
                elif entry.is_dir():
                    # ディレクトリの場合は再帰的に処理
                    result.update(self._scan_directory(entry_path))

        except PermissionError as e:
            logger.warning(f"Permission denied accessing {directory}: {e}")
        except Exception as e:
            logger.error(f"Error scanning directory {directory}: {e}")

        return result

    def read_ignore_file(self, path: Path) -> List[str]:
        """gitignoreファイルを読み込む

        Args:
            path: .gitignoreファイルのパス

        Returns:
            gitignoreパターンのリスト
        """
        try:
            return self.ignore_scanner.read_file(path)
        except Exception as e:
            logger.error(f"Error reading ignore file {path}: {e}")
            return []

    def _check_ignore_patterns(self, path: Path) -> bool:
        """パスがgitignoreパターンによって無視されるべきかをチェックする

        Args:
            path: チェックするパス

        Returns:
            パスが無視されるべき場合はTrue
        """
        # relative_path = make_relative(path, self.root_dir)

        return self.ignore_scanner.is_ignored(path, self.root_dir)
