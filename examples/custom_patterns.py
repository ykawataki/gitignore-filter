#!/usr/bin/env python3
"""Advanced usage examples with custom patterns for gitignore_filter package."""

import os
from pathlib import Path
from typing import List

from gitignore_filter import git_ignore_filter


def advanced_patterns() -> None:
    """Examples of advanced pattern usage."""
    # 高度なパターンの例
    patterns = [
        # 基本的なワイルドカード
        "*.{jpg,jpeg,png,gif}",  # 画像ファイル

        # ディレクトリ指定
        "build/",                # buildディレクトリ
        "dist/",                # distディレクトリ

        # 否定パターン
        "!build/release/",      # buildディレクトリ内のreleaseは除外しない
        "!*.min.js",           # 圧縮済みJavaScriptは除外しない

        # パスパターン
        "docs/*/*.pdf",        # docsの直下のサブディレクトリ内のPDFファイル
        "**/test/temp/",       # どの階層のtest/tempディレクトリも除外

        # 文字セット
        "[0-9]*.txt",         # 数字で始まるテキストファイル
        "data-[a-z].json",    # data-の後に小文字が続くJSONファイル
    ]

    files = git_ignore_filter("./tmp/my_project", custom_patterns=patterns)
    print("Files after applying advanced patterns:", files)


def nested_ignore_example() -> None:
    """Example of handling nested .gitignore files."""
    # プロジェクトのルートに.gitignoreを作成
    root_patterns = [
        "*.log",
        "*.tmp"
    ]

    # サブディレクトリに別の.gitignoreを作成
    sub_patterns = [
        "!important.log",
        "*.cache"
    ]

    project_dir = Path("tmp/my_project")
    src_dir = project_dir / "src"

    # .gitignoreファイルを作成
    with open(project_dir / ".gitignore", "w") as f:
        f.write("\n".join(root_patterns))

    src_dir.mkdir(exist_ok=True)
    with open(src_dir / ".gitignore", "w") as f:
        f.write("\n".join(sub_patterns))

    # フィルタリングを実行
    files = git_ignore_filter(str(project_dir))
    print("Files after applying nested .gitignore rules:", files)


def windows_patterns() -> None:
    """Example of Windows-style path patterns."""
    # Windowsスタイルのパスパターン
    patterns = [
        "temp\\*",
        "build\\output\\*.exe",
        "!build\\output\\release\\*.exe"
    ]

    files = git_ignore_filter("./tmp/my_project", custom_patterns=patterns)
    print("Files after applying Windows-style patterns:", files)


if __name__ == "__main__":
    # サンプルのディレクトリ構造を作成
    project_dir = Path("tmp/my_project")
    project_dir.mkdir(exist_ok=True, parents=True)

    # 様々な種類のファイルを作成
    files_to_create = [
        "main.py",
        "test.jpg",
        "doc.pdf",
        "data-a.json",
        "1test.txt",
        "important.log",
        "temp.tmp",
    ]

    for file in files_to_create:
        (project_dir / file).touch()

    # buildディレクトリとファイル
    build_dir = project_dir / "build"
    build_dir.mkdir(exist_ok=True)
    (build_dir / "output.exe").touch()

    # ネストされたディレクトリとファイル
    src_dir = project_dir / "src"
    src_dir.mkdir(exist_ok=True)
    (src_dir / "module.py").touch()
    (src_dir / "module.cache").touch()

    print("\n=== Advanced Pattern Examples ===")
    advanced_patterns()

    print("\n=== Nested .gitignore Example ===")
    nested_ignore_example()

    print("\n=== Windows-style Pattern Example ===")
    windows_patterns()
