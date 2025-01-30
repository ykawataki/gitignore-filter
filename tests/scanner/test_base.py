from pathlib import Path
from typing import List

import pytest

from gitignore_filter.scanner.base import BaseScanner


@pytest.fixture
def mock_scanner_class():
    """テスト用のBaseScannerの実装クラスを提供するフィクスチャ"""
    class _MockScanner(BaseScanner):
        """BaseScanner実装のモッククラス"""

        def __init__(self, root_dir: str, patterns: List[str] = None, case_sensitive: bool = True):
            super().__init__(root_dir, case_sensitive)
            self.test_patterns = patterns or []

        def scan(self) -> List[str]:
            return []

        def read_ignore_file(self, path: Path) -> List[str]:
            return self.test_patterns

        def _check_ignore_patterns(self, path: Path) -> bool:
            return str(path).endswith('.ignore')

    return _MockScanner


@pytest.fixture
def temp_dir(tmp_path):
    """一時ディレクトリを作成するフィクスチャ"""
    return tmp_path


@pytest.fixture
def scanner(temp_dir, mock_scanner_class):
    """テスト用のスキャナーインスタンスを作成するフィクスチャ"""
    return mock_scanner_class(str(temp_dir))


def test_base_scanner_initialization(temp_dir, mock_scanner_class):
    """BaseScanner初期化のテスト"""
    scanner = mock_scanner_class(str(temp_dir))
    assert scanner.root_dir == temp_dir.resolve()
    assert scanner.case_sensitive is True
    assert isinstance(scanner._scanned_paths, set)
    assert isinstance(scanner._ignore_patterns, dict)


def test_case_sensitive_initialization(temp_dir, mock_scanner_class):
    """大文字小文字の区別の設定テスト"""
    # デフォルトは大文字小文字を区別する
    scanner = mock_scanner_class(str(temp_dir))
    assert scanner.case_sensitive is True

    # 大文字小文字を区別しない設定
    scanner = mock_scanner_class(str(temp_dir), case_sensitive=False)
    assert scanner.case_sensitive is False


def test_is_ignored_git_directory(scanner):
    """is_ignoredメソッドの.gitディレクトリチェックテスト"""
    git_path = Path('.git/config')
    assert scanner.is_ignored(git_path) is True

    git_subdir = Path('subdir/.git/config')
    assert scanner.is_ignored(git_subdir) is True

    non_git = Path('something/else')
    assert scanner.is_ignored(non_git) is False


def test_normalize_path(temp_dir, mock_scanner_class):
    """_normalize_pathメソッドのテスト"""
    scanner = mock_scanner_class(str(temp_dir))

    # 基本的なパス正規化
    test_path = temp_dir / 'test' / 'path.txt'
    normalized = scanner._normalize_path(test_path)
    assert '\\' not in normalized
    assert normalized == 'test/path.txt'

    # 大文字小文字を区別しない場合
    scanner_insensitive = mock_scanner_class(
        str(temp_dir), case_sensitive=False)
    test_path = temp_dir / 'TEST' / 'Path.TXT'
    normalized = scanner_insensitive._normalize_path(test_path)
    assert normalized == 'test/path.txt'


def test_get_ignored_patterns(scanner):
    """get_ignored_patternsメソッドのテスト"""
    # パターンを追加
    test_dir = Path('test/dir')
    scanner._ignore_patterns[test_dir] = ['*.txt', '*.log']
    other_dir = Path('other/dir')
    scanner._ignore_patterns[other_dir] = ['*.tmp']

    # 特定のディレクトリのパターンを取得
    patterns = scanner.get_ignored_patterns(test_dir)
    assert patterns == ['*.txt', '*.log']

    # 存在しないディレクトリは空リストを返す
    patterns = scanner.get_ignored_patterns(Path('nonexistent'))
    assert patterns == []

    # ディレクトリを指定しない場合は全パターンを返す
    all_patterns = scanner.get_ignored_patterns()
    assert len(all_patterns) == 3
    assert set(all_patterns) == {'*.txt', '*.log', '*.tmp'}


def test_abstract_methods():
    """抽象メソッドの実装強制のテスト"""
    class IncompleteScanner(BaseScanner):
        pass

    with pytest.raises(TypeError):
        IncompleteScanner('dummy/path')
