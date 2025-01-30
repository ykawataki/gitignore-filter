import os
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from gitignore_filter.scanner.fs import FileSystemScanner


@pytest.fixture
def temp_dir_structure(tmp_path):
    """テスト用のディレクトリ構造を作成する"""
    # ディレクトリ構造を作成
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "file1.txt").write_text("content")
    (tmp_path / "src" / "file2.py").write_text("content")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "index.md").write_text("content")
    (tmp_path / "build").mkdir()
    (tmp_path / "build" / "output.txt").write_text("content")
    return tmp_path


@pytest.fixture
def scanner(temp_dir_structure):
    """FileSystemScannerのインスタンスを作成する"""
    return FileSystemScanner(str(temp_dir_structure))


def test_basic_scan(temp_dir_structure, scanner):
    """基本的なディレクトリスキャンのテスト"""
    paths = scanner.scan()
    assert len(paths) > 0
    assert "src/file1.txt" in paths
    assert "src/file2.py" in paths
    assert "docs/index.md" in paths


def test_gitignore_root(temp_dir_structure):
    """ルートの.gitignoreファイルの処理テスト"""
    # .gitignoreファイルを作成
    gitignore = temp_dir_structure / ".gitignore"
    gitignore.write_text("*.txt\nbuild/")

    scanner = FileSystemScanner(str(temp_dir_structure))
    paths = scanner.scan()

    # .txtファイルとbuildディレクトリが除外されていることを確認
    assert "src/file2.py" in paths
    assert "docs/index.md" in paths
    assert "src/file1.txt" not in paths
    assert "build/output.txt" not in paths


def test_nested_gitignore(temp_dir_structure):
    """ネストされた.gitignoreファイルの処理テスト"""
    # ルートの.gitignoreファイル
    (temp_dir_structure / ".gitignore").write_text("*.txt")

    # srcディレクトリの.gitignoreファイル
    (temp_dir_structure / "src" / ".gitignore").write_text("!*.txt\n*.py")

    scanner = FileSystemScanner(str(temp_dir_structure))
    paths = scanner.scan()

    # srcディレクトリの.gitignoreが優先されることを確認
    assert "src/file1.txt" in paths  # !*.txtにより許可
    assert "src/file2.py" not in paths  # *.pyにより除外
    assert "build/output.txt" not in paths  # ルートの*.txtにより除外


def test_case_sensitivity(temp_dir_structure):
    """大文字小文字の区別のテスト"""
    # 大文字小文字混在のファイルを作成
    (temp_dir_structure / "TEST.txt").write_text("content")
    (temp_dir_structure / "test.TXT").write_text("content")

    # .gitignoreファイルを作成
    (temp_dir_structure / ".gitignore").write_text("*.TXT")

    # 大文字小文字を区別する場合
    scanner = FileSystemScanner(str(temp_dir_structure), case_sensitive=True)
    paths = scanner.scan()
    assert "TEST.txt" in paths
    assert "test.TXT" not in paths

    # 大文字小文字を区別しない場合
    scanner = FileSystemScanner(str(temp_dir_structure), case_sensitive=False)
    paths = scanner.scan()
    assert "TEST.txt" not in paths
    assert "test.TXT" not in paths


def test_symlink_handling(temp_dir_structure):
    """シンボリックリンクの処理テスト"""
    # シンボリックリンクを作成
    source = temp_dir_structure / "src" / "file1.txt"
    link = temp_dir_structure / "link.txt"
    try:
        os.symlink(source, link)
    except OSError:
        pytest.skip("Symlink creation not supported")

    scanner = FileSystemScanner(str(temp_dir_structure))
    paths = scanner.scan()

    # シンボリックリンクが除外されていることを確認
    assert "link.txt" not in paths
    assert "src/file1.txt" in paths


def test_permission_error_handling(temp_dir_structure):
    """権限エラーの処理テスト"""
    restricted_dir = temp_dir_structure / "restricted"
    restricted_dir.mkdir()

    # scandir関数がPermissionErrorを発生させるようにモック化
    with patch('os.scandir') as mock_scandir:
        mock_scandir.side_effect = PermissionError("Access denied")

        scanner = FileSystemScanner(str(temp_dir_structure))
        # エラーが発生してもスキャンが続行されることを確認
        paths = scanner.scan()
        assert isinstance(paths, list)


def test_ignore_dot_git_directory(temp_dir_structure):
    """.gitディレクトリの除外テスト"""
    # .gitディレクトリを作成
    git_dir = temp_dir_structure / ".git"
    git_dir.mkdir()
    (git_dir / "config").write_text("content")

    scanner = FileSystemScanner(str(temp_dir_structure))
    paths = scanner.scan()

    # .gitディレクトリ内のファイルが除外されていることを確認
    assert not any(path.startswith(".git/") for path in paths)


def test_empty_directory(tmp_path):
    """空のディレクトリのスキャンテスト"""
    scanner = FileSystemScanner(str(tmp_path))
    paths = scanner.scan()
    assert paths == []


def test_ignore_file_read_error(temp_dir_structure):
    """.gitignoreファイルの読み込みエラー処理テスト"""
    gitignore = temp_dir_structure / ".gitignore"
    gitignore.write_text("*.txt")

    with patch('builtins.open', side_effect=IOError("Read error")):
        scanner = FileSystemScanner(str(temp_dir_structure))
        # エラーが発生してもスキャンが続行されることを確認
        paths = scanner.scan()
        assert isinstance(paths, list)
