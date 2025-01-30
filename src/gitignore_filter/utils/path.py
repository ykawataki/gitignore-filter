from pathlib import Path
from typing import List, Union


def normalize_path(path: Union[str, Path]) -> str:
    """パスを正規化する

    - バックスラッシュをスラッシュに変換
    - 連続するスラッシュを単一のスラッシュに
    - 相対パス表現 (./, ../) を解決
    - 末尾のスラッシュを除去

    Args:
        path: 正規化するパス

    Returns:
        正規化されたパス文字列
    """
    # Pathオブジェクトに変換して正規化
    normalized = str(Path(path).resolve())

    # Windows形式のパスをPOSIX形式に変換
    normalized = normalized.replace('\\', '/')

    # 末尾のスラッシュを除去
    if normalized.endswith('/') and len(normalized) > 1:
        normalized = normalized[:-1]

    return normalized


def make_relative(path: Union[str, Path], base: Union[str, Path]) -> str:
    """パスをベースパスからの相対パスに変換する

    Args:
        path: 変換するパス
        base: ベースとなるディレクトリパス

    Returns:
        baseからの相対パスを表す文字列
    """
    # 両方のパスを絶対パスに変換
    abs_path = Path(path).resolve()
    abs_base = Path(base).resolve()

    try:
        # 相対パスを取得
        rel_path = str(abs_path.relative_to(abs_base))
        # Windows形式のパスをPOSIX形式に変換
        return rel_path.replace('\\', '/')
    except ValueError:
        # パスがベースパスの配下にない場合は元のパスを正規化して返す
        return normalize_path(path)


def split_path(path: Union[str, Path]) -> List[str]:
    """パスをコンポーネントに分割する

    Args:
        path: 分割するパス

    Returns:
        パスコンポーネントのリスト。
        カレントディレクトリを示す'.'は除去されるが、
        親ディレクトリを示す'..'は保持される。
    """
    # 文字列に変換してスラッシュで正規化
    normalized = str(path).replace('\\', '/')

    # 連続するスラッシュを単一のスラッシュに
    while '//' in normalized:
        normalized = normalized.replace('//', '/')

    # 先頭と末尾のスラッシュを除去（ただし、パスが '/' のみの場合は除く）
    if normalized != '/':
        normalized = normalized.strip('/')

    # コンポーネントに分割
    components = []
    for component in normalized.split('/'):
        # 空のコンポーネントと単なる'.'は除去
        if component and component != '.':
            components.append(component)

    return components
