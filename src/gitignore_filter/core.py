import logging
import os
from pathlib import Path
from typing import List, Optional, Union

from .config.git import GitConfig
from .scanner.worker import WorkerScanner

logger = logging.getLogger(__name__)


def git_ignore_filter(
    directory_path: str,
    custom_patterns: Optional[List[str]] = None,
    case_sensitive: Optional[bool] = None,
    num_workers: Optional[int] = None
) -> List[str]:
    """指定したディレクトリの.gitignoreを考慮したファイルパスのリストを取得する。

    Args:
        directory_path: 対象となるディレクトリパス
        custom_patterns: カスタムの.gitignoreパターン（rootの.gitignoreとして追加）
        case_sensitive: 大文字小文字を区別するか（Noneの場合はgit configに従う）
        num_workers: 並列処理のワーカー数（Noneの場合はCPU数）

    Returns:
        .gitignoreに除外されなかったファイルパスのリスト

    Raises:
        FileNotFoundError: 指定したディレクトリが存在しない場合
        PermissionError: ディレクトリにアクセス権がない場合
    """
    try:
        logger.debug("=== Starting git_ignore_filter ===")
        logger.debug(
            f"Parameters: directory_path={directory_path}, custom_patterns={custom_patterns}, case_sensitive={case_sensitive}, num_workers={num_workers}")
        directory_path = os.path.abspath(directory_path)

        if not os.path.isdir(directory_path):
            raise FileNotFoundError(f"Directory not found: {directory_path}")

        # Git設定を読み込む
        try:
            git_config = GitConfig()
            if case_sensitive is None:
                case_sensitive = not git_config.get_core_ignorecase()
        except FileNotFoundError:
            # .gitディレクトリが見つからない場合はデフォルト値を使用
            if case_sensitive is None:
                case_sensitive = True

        # スキャナーを初期化
        scanner = WorkerScanner(
            directory_path,
            case_sensitive=case_sensitive,
            num_workers=num_workers
        )

        # カスタムパターンがある場合は追加
        if custom_patterns:
            scanner.ignore_scanner.add_patterns(custom_patterns)

        # グローバルなgitignoreを読み込む
        if git_config and (excludes_file := git_config.get_excludes_file()):
            if os.path.isfile(excludes_file):
                global_patterns = scanner.read_ignore_file(Path(excludes_file))
                if global_patterns:
                    scanner.ignore_scanner.add_patterns(global_patterns)

        # スキャンを実行
        result = scanner.scan()
        logger.debug(f"Scan completed. Found {len(result)} files")
        logger.debug("=== git_ignore_filter completed ===")
        return sorted(result)

    except PermissionError as e:
        logger.error(f"Permission error accessing directory: {e}")
        raise
    except Exception as e:
        logger.error(f"Error during gitignore filtering: {e}", exc_info=True)
        raise
