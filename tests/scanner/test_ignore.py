import logging
import os
from pathlib import Path

import pytest

from gitignore_filter.scanner.ignore import GitIgnoreScanner

# デバッグ用のロガーを設定
logger = logging.getLogger(__name__)


@pytest.fixture
def scanner():
    return GitIgnoreScanner()


@pytest.fixture
def temp_gitignore(tmp_path):
    """一時的な.gitignoreファイルを作成する"""
    gitignore = tmp_path / '.gitignore'
    return gitignore


def test_read_empty_file(scanner, temp_gitignore):
    """空のgitignoreファイルを読み込むテスト"""
    temp_gitignore.write_text('')
    patterns = scanner.read_file(temp_gitignore)
    assert patterns == []


def test_read_basic_patterns(scanner, temp_gitignore):
    """基本的なパターンの読み込みテスト"""
    content = """
# コメント
*.txt
!important.txt
temp/
""".strip()
    temp_gitignore.write_text(content)
    patterns = scanner.read_file(temp_gitignore)
    assert patterns == ['*.txt', '!important.txt', 'temp/']


def test_read_nonexistent_file(scanner, temp_gitignore):
    """存在しないファイルの読み込みテスト"""
    patterns = scanner.read_file(Path('nonexistent'))
    assert patterns == []


def test_read_with_different_encoding(scanner, temp_gitignore):
    """異なるエンコーディングのファイル読み込みテスト"""
    content = "*.txt\n# comment\ntemp/".encode('latin-1')
    temp_gitignore.write_bytes(content)
    patterns = scanner.read_file(temp_gitignore)
    assert patterns == ['*.txt', 'temp/']


def test_add_basic_patterns(scanner):
    """基本的なパターンの追加テスト"""
    patterns = ['*.txt', '!important.txt', 'temp/']
    scanner.add_patterns(patterns)
    added_patterns = scanner.get_patterns()
    assert len(added_patterns) == 3
    assert not added_patterns[0].negated
    assert added_patterns[1].negated
    assert added_patterns[2].is_directory_only


def test_add_patterns_with_base_path(scanner):
    """ベースパス付きでパターンを追加するテスト"""
    patterns = ['*.txt']
    base_path = '/base/path'
    scanner.add_patterns(patterns, base_path)
    added_patterns = scanner.get_patterns()
    assert len(added_patterns) == 1
    assert added_patterns[0].base_path == base_path


def test_is_ignored_basic(scanner, tmp_path):
    """基本的な無視判定のテスト"""
    scanner.add_patterns(['*.txt', '!important.txt'])

    # 通常のテキストファイルは無視される
    test_file = tmp_path / 'test.txt'
    result = scanner.is_ignored(test_file)
    assert result


def test_is_ignored_directory(scanner, tmp_path):
    """ディレクトリの無視判定テスト"""
    scanner.add_patterns(['temp/'])

    # ディレクトリは無視される
    temp_dir = tmp_path / 'temp'
    temp_dir.mkdir()
    assert scanner.is_ignored(temp_dir)

    # ファイルは無視されない
    temp_file = tmp_path / 'temp.txt'
    assert not scanner.is_ignored(temp_file)


def test_is_ignored_nested_patterns(scanner, tmp_path):
    """ネストされたパターンの無視判定テスト"""
    scanner.add_patterns(['*.txt'])
    scanner.add_patterns(['!src/*.txt'], 'src')

    # ルートのテキストファイルは無視される
    result = scanner.is_ignored('test.txt')
    assert result

    # srcディレクトリ内のテキストファイルは無視されない
    result = scanner.is_ignored('src/test.txt')
    assert not result


def test_is_ignored_case_sensitivity(tmp_path):
    """大文字小文字の区別の無視判定テスト"""
    # 大文字小文字を区別する場合
    sensitive_scanner = GitIgnoreScanner(case_sensitive=True)
    sensitive_scanner.add_patterns(['*.TXT'])

    assert sensitive_scanner.is_ignored('test.TXT', tmp_path)
    assert not sensitive_scanner.is_ignored('test.txt', tmp_path)

    # 大文字小文字を区別しない場合
    insensitive_scanner = GitIgnoreScanner(case_sensitive=False)
    insensitive_scanner.add_patterns(['*.TXT'])

    assert insensitive_scanner.is_ignored('test.TXT', tmp_path)
    assert insensitive_scanner.is_ignored('test.txt', tmp_path)
