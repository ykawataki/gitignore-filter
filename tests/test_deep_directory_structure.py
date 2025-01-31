import os
from pathlib import Path

import pytest

from gitignore_filter.core import git_ignore_filter


@pytest.fixture
def deep_directory_structure(tmp_path):
    """深い階層のディレクトリ構造を作成するフィクスチャ"""
    # 深い階層のディレクトリを作成
    directories = [
        "src/components/ui/buttons",
        "src/components/ui/forms",
        "src/components/layout",
        "src/utils/helpers/string",
        "src/utils/helpers/date",
        "src/case-test",  # case sensitivityテスト用のディレクトリを追加
        "tests/unit/components/ui",
        "tests/integration/api",
        "docs/api/v1/endpoints",
        "docs/api/v2/endpoints",
    ]

    # 各ディレクトリにファイルを作成
    files = {
        "src/components/ui/buttons/primary.tsx": "content",
        "src/components/ui/buttons/secondary.tsx": "content",
        "src/components/ui/forms/input.tsx": "content",
        "src/components/ui/forms/select.tsx": "content",
        "src/components/layout/header.tsx": "content",
        "src/utils/helpers/string/format.ts": "content",
        "src/utils/helpers/string/validate.ts": "content",
        "src/utils/helpers/date/format.ts": "content",
        "tests/unit/components/ui/test_buttons.py": "content",
        "tests/integration/api/test_endpoints.py": "content",
        "docs/api/v1/endpoints/users.md": "content",
        "docs/api/v2/endpoints/auth.md": "content",
    }

    # ネストされた.gitignoreファイル
    gitignores = {
        ".gitignore": """
# Global patterns
*.log
node_modules/
dist/
.DS_Store

# Source files
*.map
*.d.ts

# Test files
__pycache__/
.pytest_cache/
coverage/
""",
        "src/.gitignore": """
# Allow TypeScript declaration files in src
!*.d.ts

# Ignore local development files
*.local.*
.env.local
""",
        "docs/.gitignore": """
# Ignore generated files
_site/
.jekyll-cache/
*.html
!index.html
""",
    }

    # ディレクトリとファイルを作成
    for directory in directories:
        (tmp_path / directory).mkdir(parents=True, exist_ok=True)

    for file_path, content in files.items():
        file = tmp_path / file_path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(content)

    # .gitignoreファイルを作成
    for gitignore_path, content in gitignores.items():
        ignore_file = tmp_path / gitignore_path
        ignore_file.parent.mkdir(parents=True, exist_ok=True)
        ignore_file.write_text(content.strip())

    return tmp_path


def test_deep_directory_filtering(deep_directory_structure):
    """深い階層のディレクトリ構造に対するフィルタリングのテスト"""
    result = git_ignore_filter(str(deep_directory_structure))

    # TypeScriptファイルが含まれていることを確認
    assert "src/components/ui/buttons/primary.tsx" in result
    assert "src/components/ui/forms/input.tsx" in result
    assert "src/utils/helpers/string/format.ts" in result

    # ドキュメントファイルが含まれていることを確認
    assert "docs/api/v1/endpoints/users.md" in result
    assert "docs/api/v2/endpoints/auth.md" in result

    # テストファイルが含まれていることを確認
    assert "tests/unit/components/ui/test_buttons.py" in result
    assert "tests/integration/api/test_endpoints.py" in result


def test_deep_directory_ignore_patterns(deep_directory_structure):
    """深い階層での.gitignoreパターンの適用テスト"""
    # ローカル開発ファイルを作成
    (deep_directory_structure / "src/components/config.local.ts").write_text("content")
    (deep_directory_structure / "src/.env.local").write_text("content")

    # HTML生成ファイルを作成
    (deep_directory_structure / "docs/api/v1/page.html").write_text("content")
    (deep_directory_structure / "docs/index.html").write_text("content")

    result = git_ignore_filter(str(deep_directory_structure))

    # src/.gitignoreのパターンテスト
    assert "src/components/config.local.ts" not in result  # *.local.*にマッチ
    assert "src/.env.local" not in result  # .env.localにマッチ

    # docs/.gitignoreのパターンテスト
    assert "docs/api/v1/page.html" not in result  # *.htmlにマッチ
    assert "docs/index.html" in result  # !index.htmlで除外から除外


def test_deep_directory_custom_patterns(deep_directory_structure):
    """深い階層でのカスタムパターンの適用テスト"""
    custom_patterns = [
        # 最初に全体的なTypeScriptファイルの除外
        "**/*.ts",
        "**/*.tsx",
        # helpersディレクトリのTypeScriptファイルを除外から除外
        "!**/helpers/**/*.ts",
        # buttonsディレクトリのTypeScriptファイルを除外から除外
        "!**/buttons/**/*.tsx",
    ]

    result = git_ignore_filter(
        str(deep_directory_structure),
        custom_patterns=custom_patterns
    )

    # UIコンポーネントの確認
    assert "src/components/ui/buttons/primary.tsx" in result  # 除外から除外される
    assert "src/components/ui/forms/input.tsx" not in result  # 除外される
    assert "src/components/layout/header.tsx" not in result  # 除外される

    # TypeScriptファイルの確認
    assert "src/utils/helpers/string/format.ts" in result  # 除外から除外される
    assert "src/utils/helpers/date/format.ts" in result  # 除外から除外される


def test_deep_directory_symlinks(deep_directory_structure):
    """深い階層でのシンボリックリンクの処理テスト"""
    # 実ファイルとシンボリックリンクを作成
    source_file = deep_directory_structure / \
        "src/components/ui/buttons/primary.tsx"
    link_path = deep_directory_structure / \
        "src/components/ui/buttons/primary.link.tsx"

    try:
        os.symlink(source_file, link_path)
    except OSError:
        pytest.skip("Symlink creation not supported")

    result = git_ignore_filter(str(deep_directory_structure))

    # 元のファイルは含まれるがシンボリックリンクは除外される
    assert "src/components/ui/buttons/primary.tsx" in result
    assert "src/components/ui/buttons/primary.link.tsx" not in result


def test_deep_directory_case_sensitivity(deep_directory_structure):
    """深い階層でのファイル名の大文字小文字の区別テスト"""
    # case-testディレクトリは既にフィクスチャで作成済み
    test_file_upper = deep_directory_structure / "src/case-test/Sensitive.txt"
    test_file_lower = deep_directory_structure / "src/case-test/sensitive.txt"

    # テストファイルを作成
    test_file_upper.write_text("content")
    test_file_lower.write_text("content")

    # 大文字小文字を区別する場合
    sensitive_patterns = ["src/case-test/Sensitive.txt"]
    result_sensitive = git_ignore_filter(
        str(deep_directory_structure),
        custom_patterns=sensitive_patterns,
        case_sensitive=True
    )
    assert "src/case-test/Sensitive.txt" not in result_sensitive
    assert "src/case-test/sensitive.txt" in result_sensitive

    # 大文字小文字を区別しない場合
    result_insensitive = git_ignore_filter(
        str(deep_directory_structure),
        custom_patterns=sensitive_patterns,
        case_sensitive=False
    )

    # 大文字小文字を区別しない場合、両方がパターンにマッチして除外される
    assert "src/case-test/Sensitive.txt" not in result_insensitive
    assert "src/case-test/sensitive.txt" not in result_insensitive
