"""ロギング機能のテスト"""

import logging
import os
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest

from gitignore_filter import git_ignore_filter
from gitignore_filter.logging import LogConfig


@pytest.fixture
def log_file(tmp_path):
    """一時的なログファイルを提供するフィクスチャ"""
    return tmp_path / "test.log"


@pytest.fixture
def string_buffer():
    """StringIOバッファを提供するフィクスチャ"""
    return StringIO()


@pytest.fixture
def sample_dir(tmp_path):
    """サンプルディレクトリ構造を作成するフィクスチャ"""
    # テスト用のファイルを作成
    (tmp_path / "test.txt").write_text("test")
    (tmp_path / "test.py").write_text("test")
    return tmp_path


def test_log_level_setting(sample_dir, string_buffer):
    """ログレベルの設定テスト"""
    with patch('sys.stderr', string_buffer):
        # DEBUGレベルでログ出力
        git_ignore_filter(str(sample_dir), log_level='DEBUG')
        output = string_buffer.getvalue()
        assert "Starting git_ignore_filter" in output
        assert "Scan completed" in output

        # リセット
        string_buffer.truncate(0)
        string_buffer.seek(0)

        # WARNINGレベルではDEBUGメッセージは出力されない
        git_ignore_filter(str(sample_dir), log_level='WARNING')
        output = string_buffer.getvalue()
        assert "Starting git_ignore_filter" not in output


def test_log_format(sample_dir, string_buffer):
    """ログフォーマットの設定テスト"""
    test_format = '%(levelname)s - TEST - %(message)s'
    with patch('sys.stderr', string_buffer):
        git_ignore_filter(
            str(sample_dir),
            log_level='DEBUG',  # DEBUGレベルに変更
            log_format=test_format
        )
        output = string_buffer.getvalue()
        # カスタムフォーマットが適用されていることを確認
        assert any(line.startswith(('DEBUG - TEST -'))
                   for line in output.splitlines())


def test_file_logging(sample_dir, log_file):
    """ファイルへのログ出力テスト"""
    git_ignore_filter(
        str(sample_dir),
        log_level='DEBUG',
        log_file=log_file
    )

    # ログファイルが作成されていることを確認
    assert log_file.exists()
    content = log_file.read_text()
    assert "Starting git_ignore_filter" in content
    assert "Scan completed" in content


def test_file_mode(sample_dir, log_file):
    """ログファイルのモードテスト"""
    # 最初のログ出力
    git_ignore_filter(
        str(sample_dir),
        log_level='DEBUG',
        log_file=log_file,
        log_file_mode='w'
    )
    content1 = log_file.read_text()

    # 追記モードでの出力
    git_ignore_filter(
        str(sample_dir),
        log_level='DEBUG',
        log_file=log_file,
        log_file_mode='a'
    )
    content2 = log_file.read_text()
    assert len(content2) > len(content1)  # 追記されていることを確認

    # 上書きモードでの出力
    git_ignore_filter(
        str(sample_dir),
        log_level='DEBUG',
        log_file=log_file,
        log_file_mode='w'
    )
    content3 = log_file.read_text()
    assert len(content3) < len(content2)  # 上書きされていることを確認


def test_multiple_handlers(sample_dir, log_file, string_buffer):
    """複数のハンドラでのログ出力テスト"""
    with patch('sys.stderr', string_buffer):
        git_ignore_filter(
            str(sample_dir),
            log_level='DEBUG',
            log_file=log_file
        )

        # 両方のハンドラにログが出力されていることを確認
        assert log_file.exists()
        file_content = log_file.read_text()
        stderr_content = string_buffer.getvalue()

        assert "Starting git_ignore_filter" in file_content
        assert "Starting git_ignore_filter" in stderr_content


def test_log_encoding(sample_dir, log_file):
    """ログファイルのエンコーディングテスト"""
    # 日本語を含むメッセージを出力
    test_file = sample_dir / "テスト.txt"
    test_file.write_text("test")

    git_ignore_filter(
        str(sample_dir),
        log_level='DEBUG',
        log_file=log_file,
        log_encoding='utf-8'
    )

    # UTF-8でログファイルを読み込めることを確認
    content = log_file.read_text(encoding='utf-8')
    assert "テスト.txt" in content


def test_log_config_reset():
    """LogConfigのリセット機能テスト"""
    config = LogConfig()
    original_level = config.logger.level

    # レベルを変更
    config.set_level('DEBUG')
    assert config.logger.level == logging.DEBUG

    # リセット
    config.reset()
    assert config.logger.level == original_level
    assert len(config.logger.handlers) == 1  # デフォルトハンドラのみ


def test_invalid_log_level(sample_dir):
    """無効なログレベル指定のテスト"""
    with pytest.raises(AttributeError):
        git_ignore_filter(str(sample_dir), log_level='INVALID_LEVEL')


def test_non_existent_log_directory(sample_dir):
    """存在しないログディレクトリのテスト"""
    non_existent_file = Path("/non/existent/dir/test.log")
    with pytest.raises(OSError):
        git_ignore_filter(str(sample_dir), log_file=non_existent_file)


def test_log_level_numeric_value(sample_dir, string_buffer):
    """数値でのログレベル指定テスト"""
    with patch('sys.stderr', string_buffer):
        git_ignore_filter(str(sample_dir), log_level=logging.DEBUG)
        output = string_buffer.getvalue()
        assert "Starting git_ignore_filter" in output


def test_concurrent_calls_isolation(sample_dir, tmp_path):
    """並行呼び出し時のログ設定の分離テスト"""
    log_file1 = tmp_path / "test1.log"
    log_file2 = tmp_path / "test2.log"

    # 異なるログ設定で呼び出し
    # デバッグメッセージ付きの呼び出し
    git_ignore_filter(
        str(sample_dir),
        log_level='DEBUG',
        log_file=log_file1,
        log_format='DEBUG - %(message)s'
    )

    # エラー時のみメッセージを出力する設定で、存在しないディレクトリを指定
    with pytest.raises(FileNotFoundError):
        git_ignore_filter(
            str(sample_dir / "non_existent"),
            log_level='ERROR',
            log_file=log_file2,
            log_format='ERROR - %(message)s'
        )

    # それぞれのログファイルが独立して設定どおりに出力されていることを確認
    content1 = log_file1.read_text()
    content2 = log_file2.read_text()
    assert "DEBUG -" in content1
    assert "ERROR -" in content2  # FileNotFoundErrorのエラーメッセージが出力されているはず
