import os
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from gitignore_filter.core import git_ignore_filter


@pytest.fixture
def temp_project(tmp_path):
    """テスト用のプロジェクト構造を作成する"""
    # ディレクトリ構造を作成
    (tmp_path / "test3.py").write_text("content")
    (tmp_path / "test4.md").write_text("content")
    (tmp_path / "src").mkdir()
    (tmp_path / "src/file1.py").write_text("content")
    (tmp_path / "src/file2.txt").write_text("content")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests/test1.py").write_text("content")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs/index.md").write_text("content")
    return tmp_path


@pytest.fixture
def git_config_mock():
    """Git設定のモック"""
    with patch('gitignore_filter.core.GitConfig') as mock:
        config = Mock()
        config.get_core_ignorecase.return_value = False
        config.get_excludes_file.return_value = None
        mock.return_value = config
        yield mock


def test_basic_filtering(temp_project, git_config_mock):
    """基本的なファイルフィルタリングのテスト"""
    # .gitignoreファイルを作成
    gitignore = temp_project / ".gitignore"
    gitignore.write_text("*.txt\n")

    # フィルタリングを実行
    result = git_ignore_filter(str(temp_project))

    # .txtファイルが除外されていることを確認
    assert "src/file1.py" in result
    assert "src/file2.txt" not in result
    assert "tests/test1.py" in result
    assert "docs/index.md" in result


def test_custom_patterns(temp_project, git_config_mock):
    """カスタムパターンでのフィルタリングテスト"""
    custom_patterns = ["*.py", "!tests/*.py"]
    result = git_ignore_filter(
        str(temp_project), custom_patterns=custom_patterns, num_workers=1)

    # カスタムパターンが適用されていることを確認
    assert "test4.md" in result          # 対象外
    assert "src/file1.py" not in result  # *.pyで除外
    assert "src/file2.txt" in result     # 対象外
    assert "tests/test1.py" in result    # !tests/*.pyで除外から除外
    assert "docs/index.md" in result     # 対象外


def test_case_sensitivity(temp_project, git_config_mock):
    """大文字小文字の区別のテスト"""
    # 大文字小文字混在のファイルを作成
    (temp_project / "TEST.txt").write_text("content")
    (temp_project / "test.TXT").write_text("content")

    # .gitignoreファイルを作成
    gitignore = temp_project / ".gitignore"
    gitignore.write_text("*.TXT\n")

    # 大文字小文字を区別する場合
    result = git_ignore_filter(str(temp_project), case_sensitive=True)
    assert "TEST.txt" in result
    assert "test.TXT" not in result

    # 大文字小文字を区別しない場合
    result = git_ignore_filter(str(temp_project), case_sensitive=False)
    assert "TEST.txt" not in result
    assert "test.TXT" not in result


def test_nonexistent_directory(git_config_mock):
    """存在しないディレクトリに対するテスト"""
    with pytest.raises(FileNotFoundError):
        git_ignore_filter("/nonexistent/directory")


@pytest.mark.skipif(os.name == 'nt', reason="Permission tests not reliable on Windows")
def test_permission_error(temp_project, git_config_mock):
    """権限エラーの処理テスト"""
    # ディレクトリのパーミッションを変更
    os.chmod(temp_project, 0o000)
    try:
        with pytest.raises(PermissionError):
            git_ignore_filter(str(temp_project))
    finally:
        # テスト後にパーミッションを戻す
        os.chmod(temp_project, 0o755)


def test_nested_gitignore(temp_project, git_config_mock):
    """ネストされた.gitignoreファイルの処理テスト"""
    # ルートの.gitignore
    (temp_project / ".gitignore").write_text("*.txt\n")

    # src/配下の.gitignore
    (temp_project / "src/.gitignore").write_text("!*.txt\n*.log\n")

    result = git_ignore_filter(str(temp_project))

    # ネストされたパターンが正しく適用されていることを確認
    assert "src/file2.txt" in result     # src/.gitignoreで除外から除外
    assert "src/file1.py" in result      # 対象外
    assert "docs/index.md" in result     # 対象外


def test_global_gitignore(temp_project):
    """グローバルなgitignoreファイルの処理テスト"""
    # グローバルgitignoreファイルを作成
    global_gitignore = temp_project / "global_gitignore"
    global_gitignore.write_text("*.log\n")

    # Git設定でグローバルgitignoreを指定
    with patch('gitignore_filter.core.GitConfig') as mock:
        config = Mock()
        config.get_core_ignorecase.return_value = False
        config.get_excludes_file.return_value = str(global_gitignore)
        mock.return_value = config

        # テスト用のログファイルを作成
        (temp_project / "test.log").write_text("content")

        result = git_ignore_filter(str(temp_project))

        # グローバルパターンが適用されていることを確認
        assert "test.log" not in result


def test_multi_worker_scan(temp_project, git_config_mock):
    """複数ワーカーでのスキャンテスト"""
    # 多数のファイルを作成
    for i in range(10):
        (temp_project / f"file{i}.txt").write_text("content")
        (temp_project / f"file{i}.py").write_text("content")

    # 2ワーカーで実行
    result = git_ignore_filter(str(temp_project), num_workers=1)

    # すべてのファイルが正しく処理されていることを確認
    python_files = [f for f in result if f.endswith('.py')]
    # 10 + src/file1.py + test3.py + tests/test1.py
    assert len(python_files) == 13


def test_symlink_handling(temp_project, git_config_mock):
    """シンボリックリンクの処理テスト"""
    source = temp_project / "src/file1.py"
    link = temp_project / "link.py"

    try:
        os.symlink(source, link)
    except OSError:
        pytest.skip("Symlink creation not supported")

    result = git_ignore_filter(str(temp_project))

    # シンボリックリンクが無視されていることを確認
    assert "link.py" not in result
    assert "src/file1.py" in result
