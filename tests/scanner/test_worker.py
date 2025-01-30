import os
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import List, Set
from unittest.mock import Mock, patch

import pytest

from gitignore_filter.scanner.worker import WorkerScanner


@pytest.fixture
def temp_dir_structure(tmp_path):
    """テスト用のディレクトリ構造を作成する"""
    # 複数のディレクトリを作成
    dirs = ["src", "docs", "tests", "build"]
    for dir_name in dirs:
        dir_path = tmp_path / dir_name
        dir_path.mkdir()
        # 各ディレクトリにテストファイルを作成
        (dir_path / "file1.txt").write_text("content")
        (dir_path / "file2.py").write_text("content")

    # 隠しディレクトリ
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config").write_text("content")

    return tmp_path


@pytest.fixture
def worker_scanner(temp_dir_structure):
    """WorkerScannerのインスタンスを作成する"""
    return WorkerScanner(str(temp_dir_structure))


def test_basic_parallel_scan(worker_scanner, temp_dir_structure):
    """基本的な並列スキャンのテスト"""
    paths = worker_scanner.scan()

    # 各ディレクトリのファイルが含まれていることを確認
    assert "src/file1.txt" in paths
    assert "src/file2.py" in paths
    assert "docs/file1.txt" in paths
    assert "docs/file2.py" in paths
    assert "tests/file1.txt" in paths
    assert "tests/file2.py" in paths


def test_worker_count_initialization():
    """ワーカー数の初期化テスト"""
    # CPU数が4の場合をシミュレート
    with patch('multiprocessing.cpu_count', return_value=4):
        scanner = WorkerScanner("dummy/path")
        assert scanner.num_workers == 4

        # 明示的にワーカー数を指定
        scanner = WorkerScanner("dummy/path", num_workers=2)
        assert scanner.num_workers == 2


def test_empty_directory_scan(tmp_path):
    """空のディレクトリのスキャンテスト"""
    scanner = WorkerScanner(str(tmp_path))
    paths = scanner.scan()
    assert paths == []


def test_hidden_directory_exclusion(temp_dir_structure):
    """隠しディレクトリの除外テスト"""
    scanner = WorkerScanner(str(temp_dir_structure))
    paths = scanner.scan()

    # .gitディレクトリが除外されていることを確認
    assert not any(path.startswith(".git") for path in paths)


def test_permission_error_handling(temp_dir_structure):
    """権限エラーの処理テスト"""
    with patch('os.scandir') as mock_scandir:
        mock_scandir.side_effect = PermissionError("Access denied")

        scanner = WorkerScanner(str(temp_dir_structure))
        paths = scanner.scan()

        # エラーが発生しても空のリストが返されることを確認
        assert isinstance(paths, list)
        assert len(paths) == 0


def test_worker_process_error_handling(worker_scanner, temp_dir_structure):
    """ワーカープロセスのエラー処理テスト"""
    def mock_worker_scan(*args):
        raise Exception("Worker error")

    with patch.object(worker_scanner, '_worker_scan', side_effect=mock_worker_scan):
        paths = worker_scanner.scan()
        # エラーが発生しても処理が継続することを確認
        assert isinstance(paths, list)


def test_gitignore_in_parallel_scan(temp_dir_structure):
    """並列スキャン時の.gitignoreの処理テスト"""
    # ルートの.gitignoreを作成
    (temp_dir_structure / ".gitignore").write_text("*.txt")

    # サブディレクトリの.gitignoreを作成
    (temp_dir_structure / "src" / ".gitignore").write_text("!file1.txt")

    scanner = WorkerScanner(str(temp_dir_structure))
    paths = scanner.scan()

    # .gitignoreルールが適用されていることを確認
    assert "src/file1.txt" in paths  # 除外から除外される
    assert "src/file2.py" in paths   # 元々除外対象ではない
    assert "docs/file1.txt" not in paths  # 除外される
    assert "tests/file1.txt" not in paths  # 除外される


def test_case_sensitivity_in_parallel_scan(temp_dir_structure):
    """並列スキャン時の大文字小文字の区別テスト"""
    # 大文字小文字混在のファイルを作成
    (temp_dir_structure / "src" / "TEST.txt").write_text("content")
    (temp_dir_structure / "src" / "test.TXT").write_text("content")

    # .gitignoreファイルを作成
    (temp_dir_structure / ".gitignore").write_text("*.TXT")

    # 大文字小文字を区別する場合
    scanner = WorkerScanner(str(temp_dir_structure), case_sensitive=True)
    paths = scanner.scan()
    normalized_paths = {p.lower() for p in paths}
    assert "src/test.txt" in normalized_paths
    assert "src/test.txt" in normalized_paths

    # 大文字小文字を区別しない場合
    scanner = WorkerScanner(str(temp_dir_structure), case_sensitive=False)
    paths = scanner.scan()
    normalized_paths = {p.lower() for p in paths}
    assert "src/test.txt" not in normalized_paths
    assert "src/test.txt" not in normalized_paths


def test_symlink_handling(temp_dir_structure):
    """シンボリックリンクの処理テスト"""
    source = temp_dir_structure / "src" / "file1.txt"
    link = temp_dir_structure / "src" / "link.txt"

    try:
        os.symlink(source, link)
    except OSError:
        pytest.skip("Symlink creation not supported")

    scanner = WorkerScanner(str(temp_dir_structure))
    paths = scanner.scan()

    # シンボリックリンクが除外されていることを確認
    assert "src/link.txt" not in paths
    assert "src/file1.txt" in paths
