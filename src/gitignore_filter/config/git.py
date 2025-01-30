import configparser
import logging
import os
from pathlib import Path
from typing import Optional, Tuple

from ..utils.path import normalize_path

logger = logging.getLogger(__name__)


class GitConfig:
    """Gitの設定を読み込んで提供するクラス"""

    def __init__(self, git_dir: Optional[str] = None):
        """
        Args:
            git_dir: .gitディレクトリのパス。Noneの場合は現在のディレクトリから探索
        """
        self.git_dir = self._find_git_dir(
            git_dir) if git_dir is None else Path(git_dir)
        self.config_parser = configparser.ConfigParser()
        self._load_config()

    def _find_git_dir(self, start_path: Optional[str] = None) -> Path:
        """現在のディレクトリから.gitディレクトリを探索する

        Args:
            start_path: 探索を開始するディレクトリ

        Returns:
            見つかった.gitディレクトリのパス

        Raises:
            FileNotFoundError: .gitディレクトリが見つからない場合
        """
        current = Path(start_path or os.getcwd()).resolve()

        while True:
            git_dir = current / '.git'
            if git_dir.is_dir():
                return git_dir

            # ルートディレクトリに到達した場合
            if current.parent == current:
                raise FileNotFoundError(
                    "No .git directory found in the current path or any parent directories")

            current = current.parent

    def _load_config(self) -> None:
        """Gitの設定ファイルを読み込む"""
        config_files = [
            # システム全体の設定
            Path('/etc/gitconfig'),
            # グローバル設定
            Path.home() / '.gitconfig',
            # リポジトリ固有の設定
            self.git_dir / 'config'
        ]

        # configparserの初期化
        self.config_parser = configparser.ConfigParser(strict=False)

        for config_file in config_files:
            if config_file.is_file():
                try:
                    # Gitの設定ファイルはセクション名が[section "subsection"]の形式をとることがある
                    # 一度内容を読み込んでから、セクション名を正規化する
                    with open(config_file, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # セクションの正規化（[section "subsection"] -> [section.subsection]）
                    normalized_content = ''
                    for line in content.splitlines():
                        if line.strip().startswith('[') and '"' in line:
                            # [section "subsection"] -> [section.subsection]
                            line = line.replace(' "', '.').replace('"]', ']')
                        normalized_content += line + '\n'

                    self.config_parser.read_string(normalized_content)
                    logger.debug(f"Loaded git config from {config_file}")
                except (IOError, configparser.Error) as e:
                    logger.warning(
                        f"Failed to load git config from {config_file}: {e}")

    def get_value(self, section: str, key: str, default: Optional[str] = None) -> Optional[str]:
        """設定値を取得する

        Args:
            section: セクション名（例: "core"）
            key: キー名
            default: デフォルト値

        Returns:
            設定値。存在しない場合はデフォルト値
        """
        try:
            if not self.config_parser.has_section(section):
                return default
            return self.config_parser.get(section, key, fallback=default)
        except (configparser.Error, ValueError):
            return default

    def get_bool_value(self, section: str, key: str, default: bool = False) -> bool:
        """真偽値の設定を取得する

        Args:
            section: セクション名
            key: キー名
            default: デフォルト値

        Returns:
            設定値。存在しない場合はデフォルト値
        """
        value = self.get_value(section, key)
        if value is None:
            return default

        # Gitの真偽値形式をPythonの真偽値に変換
        return value.lower() in ('true', 'yes', 'on', '1')

    def get_core_ignorecase(self) -> bool:
        """core.ignorecaseの設定値を取得する

        Returns:
            core.ignorecaseの値。デフォルトはFalse
        """
        return self.get_bool_value('core', 'ignorecase', False)

    def get_excludes_file(self) -> Optional[str]:
        """core.excludesFileの設定値を取得する

        Returns:
            excludesFileのパス。設定されていない場合はNone
        """
        excludes_file = self.get_value('core', 'excludesFile')
        if excludes_file:
            # チルダ展開を行う
            expanded_path = os.path.expanduser(excludes_file)
            # パスを正規化して返す
            return normalize_path(expanded_path)
        return None
