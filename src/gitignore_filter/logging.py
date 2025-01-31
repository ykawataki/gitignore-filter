"""ロギング機能を提供するモジュール。

このモジュールはgitignore_filterパッケージのロギング機能を設定・管理します。
ユーザーはログレベル、フォーマット、出力先を柔軟に設定できます。
"""

import logging
import sys
from logging import FileHandler, StreamHandler
from pathlib import Path
from typing import Optional, Union

# デフォルトのログフォーマット
DEFAULT_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'


class LogConfig:
    """ロギング設定を管理するクラス"""

    def __init__(self):
        """LogConfigを初期化"""
        self.logger = logging.getLogger('gitignore_filter')
        self.logger.setLevel(logging.WARNING)  # デフォルトはWARNING
        self._setup_default_handler()

    def _setup_default_handler(self):
        """デフォルトのハンドラを設定"""
        # 既存のハンドラをクリア
        self.logger.handlers.clear()

        # 標準エラー出力へのハンドラを追加
        handler = StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter(DEFAULT_FORMAT))
        self.logger.addHandler(handler)

    def set_level(self, level: Union[str, int]):
        """ログレベルを設定

        Args:
            level: ログレベル。文字列（'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'）
                  または数値（logging.DEBUG等）で指定可能
        """
        if isinstance(level, str):
            level = getattr(logging, level.upper())
        self.logger.setLevel(level)

    def set_format(self, format_str: str):
        """ログのフォーマットを設定

        Args:
            format_str: ログフォーマット文字列
        """
        formatter = logging.Formatter(format_str)
        for handler in self.logger.handlers:
            handler.setFormatter(formatter)

    def add_file_handler(self,
                         filepath: Union[str, Path],
                         mode: str = 'a',
                         encoding: str = 'utf-8',
                         format_str: Optional[str] = None):
        """ファイル出力ハンドラを追加

        Args:
            filepath: ログファイルのパス
            mode: ファイルオープンモード ('a' または 'w')
            encoding: ファイルエンコーディング
            format_str: このハンドラ専用のフォーマット文字列（省略時は現在の設定を使用）
        """
        handler = FileHandler(filepath, mode, encoding=encoding)
        if format_str:
            handler.setFormatter(logging.Formatter(format_str))
        else:
            # 現在のフォーマッタをコピー
            handler.setFormatter(self.logger.handlers[0].formatter)
        self.logger.addHandler(handler)

    def remove_all_handlers(self):
        """全てのログハンドラを削除"""
        self.logger.handlers.clear()

    def reset(self):
        """設定をデフォルトに戻す"""
        self.remove_all_handlers()
        self._setup_default_handler()
        self.logger.setLevel(logging.WARNING)


# グローバルなLogConfigインスタンス
_log_config = LogConfig()


def get_logger():
    """パッケージのロガーを取得"""
    return _log_config.logger


def configure_logging(level: Optional[Union[str, int]] = None,
                      format_str: Optional[str] = None,
                      log_file: Optional[Union[str, Path]] = None,
                      file_mode: str = 'a',
                      encoding: str = 'utf-8'):
    """ロギングを一括設定する

    Args:
        level: ログレベル
        format_str: ログフォーマット文字列
        log_file: ログファイルのパス
        file_mode: ログファイルのオープンモード
        encoding: ログファイルのエンコーディング
    """
    if level:
        _log_config.set_level(level)
    if format_str:
        _log_config.set_format(format_str)
    if log_file:
        _log_config.add_file_handler(log_file, file_mode, encoding)
