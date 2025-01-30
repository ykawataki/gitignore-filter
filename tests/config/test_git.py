import os
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest

from gitignore_filter.config.git import GitConfig


@pytest.fixture
def temp_git_dir(tmp_path):
    """一時的な.gitディレクトリを作成する"""
    git_dir = tmp_path / '.git'
    git_dir.mkdir()
    return git_dir


@pytest.fixture
def git_config_content():
    """テスト用のGit設定内容"""
    return """
[core]
    ignorecase = true
    excludesfile = ~/.gitignore_global
[user]
    name = Test User
    email = test@example.com
"""


def test_find_git_dir(temp_git_dir):
    """_find_git_dirメソッドのテスト"""
    with patch('os.getcwd', return_value=str(temp_git_dir.parent)):
        config = GitConfig()
        assert config.git_dir == temp_git_dir


def test_find_git_dir_not_found():
    """Git directoryが見つからない場合のテスト"""
    with patch('os.getcwd', return_value='/tmp'), \
            patch('pathlib.Path.is_dir', return_value=False):
        with pytest.raises(FileNotFoundError):
            GitConfig()


def test_get_value(temp_git_dir, git_config_content):
    """get_valueメソッドのテスト"""
    mock_file = mock_open(read_data=git_config_content)
    with patch('builtins.open', mock_file):
        config = GitConfig(temp_git_dir)
        assert config.get_value('user', 'name') == 'Test User'
        assert config.get_value('user', 'email') == 'test@example.com'
        assert config.get_value('nonexistent', 'key') is None
        assert config.get_value('nonexistent', 'key', 'default') == 'default'


def test_get_bool_value(temp_git_dir):
    """get_bool_valueメソッドのテスト"""
    test_cases = {
        'true': True,
        'yes': True,
        'on': True,
        '1': True,
        'false': False,
        'no': False,
        'off': False,
        '0': False,
        'invalid': False,
    }

    for value, expected in test_cases.items():
        config_content = f'[core]\nignorecase = {value}\n'
        with patch('builtins.open', mock_open(read_data=config_content)):
            config = GitConfig(temp_git_dir)
            assert config.get_bool_value('core', 'ignorecase') == expected


def test_get_core_ignorecase(temp_git_dir):
    """get_core_ignorecaseメソッドのテスト"""
    # ignorecaseが明示的に設定されている場合
    config_content = '[core]\nignorecase = true\n'
    with patch('builtins.open', mock_open(read_data=config_content)):
        config = GitConfig(temp_git_dir)
        assert config.get_core_ignorecase() is True

    # ignorecaseが設定されていない場合（デフォルトはFalse）
    config_content = '[core]\n'
    with patch('builtins.open', mock_open(read_data=config_content)):
        config = GitConfig(temp_git_dir)
        assert config.get_core_ignorecase() is False


def test_get_excludes_file(temp_git_dir):
    """get_excludes_fileメソッドのテスト"""
    excludes_file = '~/.gitignore_global'
    config_content = f'[core]\nexcludesfile = {excludes_file}\n'

    with patch('builtins.open', mock_open(read_data=config_content)):
        config = GitConfig(temp_git_dir)
        result = config.get_excludes_file()
        assert result is not None
        # normalize_pathが適用されていることを確認
        assert '~' not in result
        assert str(Path.home()) in result

    # excludesfileが設定されていない場合
    config_content = '[core]\n'
    with patch('builtins.open', mock_open(read_data=config_content)):
        config = GitConfig(temp_git_dir)
        assert config.get_excludes_file() is None


def test_multiple_config_files(temp_git_dir):
    """複数の設定ファイルが存在する場合のテスト"""
    # システム設定
    system_config = '[core]\nignorecase = false\n'
    # ユーザー設定
    global_config = '[core]\nignorecase = true\n'
    # リポジトリ設定
    local_config = '[core]\nignorecase = false\n'

    def mock_open_multi(*args, **kwargs):
        """複数のファイルをモックする"""
        path = args[0] if args else kwargs.get('file')
        if '/etc/gitconfig' in str(path):
            return mock_open(read_data=system_config)()
        elif '.gitconfig' in str(path):
            return mock_open(read_data=global_config)()
        elif str(temp_git_dir) in str(path):
            return mock_open(read_data=local_config)()
        return mock_open()()

    with patch('builtins.open', side_effect=mock_open_multi), \
            patch('pathlib.Path.is_file', return_value=True):
        config = GitConfig(temp_git_dir)
        # 最後に読み込まれたローカル設定が優先される
        assert config.get_core_ignorecase() is False
