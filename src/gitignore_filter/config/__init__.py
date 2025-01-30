"""Git設定の読み取りと管理を行うモジュール。

このモジュールは.gitconfigファイルの読み取りと、
Git関連の設定値へのアクセスを提供します。
"""

from .git import GitConfig

__all__ = ['GitConfig']
