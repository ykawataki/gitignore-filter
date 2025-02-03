import logging
import multiprocessing as mp
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import List, Optional, Set, Tuple

from .fs import FileSystemScanner

logger = logging.getLogger(__name__)


class WorkerScanner:
    """並列処理でファイルシステムをスキャンするスキャナー"""

    def __init__(
        self,
        root_dir: str,
        case_sensitive: bool = True,
        num_workers: Optional[int] = None
    ):
        """
        Args:
            root_dir: 走査を開始するルートディレクトリ
            case_sensitive: ファイル名の大文字小文字を区別するかどうか
            num_workers: ワーカープロセス数。Noneの場合はCPUコア数
        """
        self.root_dir = Path(root_dir).resolve()
        self.case_sensitive = case_sensitive
        self.num_workers = num_workers or mp.cpu_count()
        # FileSystemScannerをメンバーとして保持
        self.fs_scanner = FileSystemScanner(str(self.root_dir), case_sensitive)
        # GitIgnoreScannerへの参照を追加
        self.ignore_scanner = self.fs_scanner.ignore_scanner

    def read_ignore_file(self, path: Path) -> List[str]:
        """FileSystemScannerのread_ignore_fileメソッドを委譲"""
        return self.fs_scanner.read_ignore_file(path)

    def scan(self) -> List[str]:
        """並列処理でディレクトリを走査する

        Returns:
            gitignoreルールでフィルタリングされたファイルパスのリスト
        """
        try:
            # ルートの.gitignoreを読み込む
            root_patterns = self._read_root_gitignore()

            if root_patterns:
                self.fs_scanner.ignore_scanner.add_patterns(root_patterns)

            # 最上位のディレクトリとファイルを列挙
            dirs, files = self._get_top_level_entries()

            # ルートレベルのファイルをフィルタリング
            filtered_files = set()
            for file in files:
                file_path = self.root_dir / file
                rel_path = file_path.relative_to(self.root_dir)
                if not self.fs_scanner.is_ignored(rel_path):
                    filtered_files.add(str(rel_path))

            # カスタムパターンを取得しstrの配列に変換
            merged_patterns = root_patterns.copy()
            custom_patterns = self.ignore_scanner.get_patterns()
            for pattern in custom_patterns:
                if pattern.negated:
                    merged_patterns.append(f"!{pattern.pattern}")
                else:
                    merged_patterns.append(pattern.pattern)

            # カスタムパターンとroot_patternsをマージしユニークにする
            merged_patterns = list(set(merged_patterns))

            # 並列処理でスキャン
            with ProcessPoolExecutor(max_workers=self.num_workers) as executor:
                # 各ディレクトリに対してワーカーを起動
                future_to_dir = {
                    executor.submit(self._worker_scan,
                                    str(d),
                                    str(self.root_dir),
                                    merged_patterns,
                                    self.case_sensitive): d
                    for d in dirs
                }

                # 結果を収集
                for future in as_completed(future_to_dir):
                    directory = future_to_dir[future]
                    try:
                        paths = future.result()
                        filtered_files.update(paths)
                    except Exception as e:
                        logger.error(f"Worker error scanning {directory}: {e}")
                        continue

            return sorted(filtered_files)

        except Exception as e:
            logger.error(f"Error during parallel scan: {e}")
            raise

    def _read_root_gitignore(self) -> List[str]:
        """ルートの.gitignoreファイルを読み込む"""
        root_gitignore = self.root_dir / '.gitignore'
        if root_gitignore.is_file():
            try:
                patterns = self.read_ignore_file(root_gitignore)
                return patterns
            except PermissionError as e:
                return []

        return []

    def _get_top_level_entries(self) -> Tuple[List[Path], List[str]]:
        """スキャン対象のトップレベルのディレクトリとファイルを取得する"""
        dirs = []
        files = []

        try:
            for entry in os.scandir(self.root_dir):
                logger.debug(
                    f"Processing entry: {entry.path}, is_dir: {entry.is_dir()}, is_file: {entry.is_file()}")

                path = Path(entry.path)
                logger.debug(
                    f"Converting path: {path} relative to {self.root_dir}")
                rel_path = path.relative_to(self.root_dir)

                if entry.is_dir() and not entry.is_symlink():
                    dirs.append(path)
                elif entry.is_file() and not entry.is_symlink():
                    files.append(str(rel_path))

            return dirs, files
        except PermissionError as e:
            logger.error(f"Permission error reading directory entries: {e}")
            return dirs, files
        except Exception as e:
            logger.error(f"Error listing root directory: {e}")
            raise

    @staticmethod
    def _worker_scan(directory: str, root_dir: str, root_patterns: List[str], case_sensitive: bool) -> Set[str]:
        """ワーカープロセスでディレクトリをスキャンする"""
        worker_id = os.getpid()  # ワーカープロセスのID取得
        logger.debug(
            f"Worker {worker_id}: Starting scan for directory: {directory}")
        directory_path = Path(directory)
        root_path = Path(root_dir)
        result_paths = set()

        try:
            # FileSystemScannerを初期化
            scanner = FileSystemScanner(root_dir, case_sensitive)

            # ルートパターンを適用
            if root_patterns:
                scanner.ignore_scanner.add_patterns(root_patterns)
                logger.debug(
                    f"Worker {worker_id}: Applied {len(root_patterns)} root patterns")

            def scan_recursive(current_dir: Path) -> None:
                # 現在のディレクトリの.gitignoreを読み込む
                ignore_path = current_dir / '.gitignore'
                if ignore_path.is_file():
                    with open(ignore_path, 'r', encoding='utf-8') as f:
                        patterns = [line.strip() for line in f if line.strip()
                                    and not line.startswith('#')]
                        if patterns:
                            rel_dir = str(current_dir.relative_to(root_path))
                            scanner.ignore_scanner.add_patterns(
                                patterns, rel_dir)
                            logger.debug(
                                f"Worker {worker_id}: Found and applied {len(patterns)} patterns from {ignore_path}")

                try:
                    # ディレクトリ内のエントリーを走査
                    for entry in os.scandir(current_dir):
                        if entry.is_symlink():
                            continue

                        entry_path = Path(entry.path)
                        rel_path = entry_path.relative_to(root_path)

                        if entry.is_file():
                            if not scanner.is_ignored(rel_path):
                                result_paths.add(str(rel_path))
                        elif entry.is_dir():
                            # ディレクトリの場合は再帰的に処理
                            if not scanner.is_ignored(rel_path):
                                scan_recursive(entry_path)
                except PermissionError as e:
                    logger.warning(
                        f"Worker {worker_id}: Permission denied accessing {current_dir}: {e}")
                except Exception as e:
                    logger.error(
                        f"Worker {worker_id}: Error scanning directory {current_dir}: {e}")

            # 再帰的なスキャンを開始
            scan_recursive(directory_path)
            return result_paths

        except Exception as e:
            logger.error(f"Error scanning directory {directory}: {e}")
            return set()
