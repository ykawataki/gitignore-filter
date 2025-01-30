"""テストの共通設定とフィクスチャ"""

import os
import shutil
from pathlib import Path
from typing import Dict, Generator, List

import pytest


@pytest.fixture
def temp_workspace(tmp_path) -> Generator[Path, None, None]:
    """一時的なワークスペースを提供するフィクスチャ"""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    yield workspace
    shutil.rmtree(workspace)


@pytest.fixture
def sample_files(temp_workspace) -> Generator[Dict[str, Path], None, None]:
    """サンプルファイル構造を作成するフィクスチャ

    Returns:
        作成したファイルパスの辞書
    """
    files = {
        "python": [
            "src/main.py",
            "src/utils.py",
            "tests/test_main.py",
            "tests/test_utils.py",
        ],
        "documents": [
            "docs/index.md",
            "docs/api.md",
            "README.md",
        ],
        "data": [
            "data/input.csv",
            "data/output.json",
        ],
        "temp": [
            "temp/cache.tmp",
            "temp/log.txt",
        ],
    }

    created_files = {}
    for category, paths in files.items():
        for path in paths:
            full_path = temp_workspace / path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(f"Content of {path}")
            created_files[path] = full_path

    yield created_files

    # 後片付け
    for path in created_files.values():
        if path.exists():
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                shutil.rmtree(path)


@pytest.fixture
def sample_gitignore(temp_workspace) -> Generator[Path, None, None]:
    """サンプルの.gitignoreファイルを作成するフィクスチャ"""
    gitignore_content = """
# Python
__pycache__/
*.py[cod]
*$py.class

# Temporary files
*.tmp
temp/
*.log

# Documentation
docs/_build/

# Data
*.csv
!data/*.csv

# IDE
.vscode/
.idea/
"""

    gitignore_path = temp_workspace / ".gitignore"
    gitignore_path.write_text(gitignore_content.strip())
    yield gitignore_path


@pytest.fixture
def nested_gitignore(temp_workspace) -> Generator[List[Path], None, None]:
    """ネストされた.gitignoreファイルを作成するフィクスチャ"""
    gitignores = {
        ".gitignore": """
*.txt
*.tmp
!important.txt
""",
        "src/.gitignore": """
!*.txt
*.log
""",
        "docs/.gitignore": """
*.html
!index.html
""",
    }

    created_files = []
    for path, content in gitignores.items():
        full_path = temp_workspace / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content.strip())
        created_files.append(full_path)

    yield created_files


@pytest.fixture
def mock_git_config(temp_workspace) -> Generator[Path, None, None]:
    """モックのGit設定ファイルを作成するフィクスチャ"""
    git_dir = temp_workspace / ".git"
    git_dir.mkdir()

    config_content = """
[core]
    ignorecase = false
    excludesfile = ~/.gitignore_global
[user]
    name = Test User
    email = test@example.com
"""

    config_path = git_dir / "config"
    config_path.write_text(config_content.strip())
    yield config_path

    # 後片付け
    shutil.rmtree(git_dir)


@pytest.fixture
def mock_global_gitignore(tmp_path) -> Generator[Path, None, None]:
    """モックのグローバルgitignoreファイルを作成するフィクスチャ"""
    global_gitignore_content = """
# Global ignore patterns
.DS_Store
Thumbs.db
*.swp
*~
"""

    global_gitignore = tmp_path / ".gitignore_global"
    global_gitignore.write_text(global_gitignore_content.strip())
    yield global_gitignore
