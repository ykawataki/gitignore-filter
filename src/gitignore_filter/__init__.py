"""GitIgnoreFilter - Git互換の.gitignoreパターンフィルタリングを提供するPythonライブラリ。

このパッケージはGitの.gitignoreパターン構文との完全な互換性を持ち、
大規模ディレクトリの効率的な並列処理、カスタムパターンのサポート、
パターンのキャッシング機構による高速化などの機能を提供します。

Example:
    基本的な使用方法:

    >>> from gitignore_filter import git_ignore_filter
    >>> files = git_ignore_filter("./my_project")

    カスタムパターンを指定:

    >>> custom_patterns = [
    ...     "*.log",
    ...     "temp/",
    ...     "!important.log"
    ... ]
    >>> files = git_ignore_filter("./my_project", custom_patterns=custom_patterns)

    大文字小文字を区別:

    >>> files = git_ignore_filter("./my_project", case_sensitive=True)

    並列処理を制御:

    >>> files = git_ignore_filter("./my_project", num_workers=4)
"""

from .core import git_ignore_filter

__version__ = "0.1.2"
__author__ = "Yoshikazu Kawataki"
__email__ = "y.kawataki@gmail.com"
__license__ = "MIT"
__copyright__ = "Copyright 2025 Yoshikazu Kawataki"

__all__ = ["git_ignore_filter"]
