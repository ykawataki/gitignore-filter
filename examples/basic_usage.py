#!/usr/bin/env python3
"""Basic usage examples for gitignore_filter package."""

from pathlib import Path
from typing import List

from gitignore_filter import git_ignore_filter


def basic_filtering() -> None:
    """Basic file filtering example."""
    # ディレクトリ内のファイルをフィルタリング
    files = git_ignore_filter("./tmp/my_project")
    print("Filtered files:", files)


def custom_ignore_patterns() -> None:
    """Using custom ignore patterns example."""
    # カスタムの除外パターンを指定
    custom_patterns = [
        "*.log",
        "temp/",
        "!important.log"
    ]
    files = git_ignore_filter(
        "./tmp/my_project", custom_patterns=custom_patterns)
    print("Files with custom patterns:", files)


def case_sensitive_filtering() -> None:
    """Case-sensitive filtering example."""
    # 大文字小文字を区別する
    files_sensitive = git_ignore_filter(
        "./tmp/my_project", case_sensitive=True)
    print("Case-sensitive results:", files_sensitive)

    # 大文字小文字を区別しない
    files_insensitive = git_ignore_filter(
        "./tmp/my_project", case_sensitive=False)
    print("Case-insensitive results:", files_insensitive)


def parallel_processing() -> None:
    """Parallel processing example."""
    # 並列処理を制御
    files_parallel = git_ignore_filter("./tmp/my_project", num_workers=4)
    print("Files processed in parallel:", files_parallel)


if __name__ == "__main__":
    # サンプルディレクトリ構造を作成
    project_dir = Path("tmp/my_project")
    project_dir.mkdir(exist_ok=True, parents=True)

    # サンプルファイルを作成
    (project_dir / "main.py").touch()
    (project_dir / "debug.log").touch()
    (project_dir / "important.log").touch()
    temp_dir = project_dir / "temp"
    temp_dir.mkdir(exist_ok=True)
    (temp_dir / "cache.tmp").touch()

    # 基本的な使用例
    print("\n=== Basic Filtering ===")
    basic_filtering()

    # カスタムパターンの使用例
    print("\n=== Custom Patterns ===")
    custom_ignore_patterns()

    # 大文字小文字の区別
    print("\n=== Case Sensitivity ===")
    case_sensitive_filtering()

    # 並列処理
    print("\n=== Parallel Processing ===")
    parallel_processing()
