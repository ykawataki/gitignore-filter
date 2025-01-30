import os
from pathlib import Path

import pytest

from gitignore_filter.utils.path import make_relative, normalize_path, split_path


def test_normalize_path_basic():
    assert normalize_path('foo/bar') == str(Path('foo/bar').resolve())
    assert normalize_path('foo\\bar') == str(Path('foo/bar').resolve())
    assert normalize_path('./foo/bar') == str(Path('foo/bar').resolve())


def test_normalize_path_trailing_slash():
    assert not normalize_path('foo/bar/').endswith('/')
    assert normalize_path('/') == '/'  # ルートディレクトリは特別扱い


def test_normalize_path_multiple_slashes():
    path = normalize_path('foo//bar///baz')
    assert '//' not in path
    assert '///' not in path


def test_normalize_path_with_path_object():
    path = Path('foo/bar')
    assert normalize_path(path) == str(path.resolve())


@pytest.mark.parametrize('path,base,expected', [
    ('foo/bar', 'foo', 'bar'),
    ('foo/bar/baz', 'foo', 'bar/baz'),
    ('./foo/bar', '.', 'foo/bar'),
    ('/absolute/path/foo', '/absolute/path', 'foo'),
])
def test_make_relative(path, base, expected):
    # テスト環境のパス区切り文字に合わせて期待値を調整
    expected = expected.replace('/', os.sep)
    result = make_relative(path, base)
    # 結果をPOSIX形式に正規化して比較
    assert result.replace('\\', '/') == expected.replace('\\', '/')


def test_make_relative_with_path_objects():
    path = Path('foo/bar/baz')
    base = Path('foo')
    assert make_relative(path, base) == 'bar/baz'.replace('/', os.sep)


def test_make_relative_not_under_base():
    path = '/other/path'
    base = '/base/path'
    # ベースパスの配下にないパスは正規化して返される
    assert make_relative(path, base) == normalize_path(path)


def test_split_path_basic():
    assert split_path('foo/bar/baz') == ['foo', 'bar', 'baz']
    assert split_path('foo\\bar\\baz') == ['foo', 'bar', 'baz']


def test_split_path_with_empty_components():
    assert split_path('foo//bar///baz') == ['foo', 'bar', 'baz']
    assert split_path('/foo/bar/') == ['foo', 'bar']


def test_split_path_with_path_object():
    path = Path('foo/bar/baz')
    assert split_path(path) == ['foo', 'bar', 'baz']


def test_split_path_dots():
    assert split_path('./foo/bar') == ['foo', 'bar']
    assert split_path('../foo/bar') == ['..', 'foo', 'bar']
