import json
import re
from pathlib import Path
from typing import Callable, Union, Dict, List, Tuple, Iterator

from model import FDPath

PDict = Union[Dict, List]
DPath = Tuple[Union[str, int], ...]


# 检查文本是否包含日语字符
def contains_japanese(text: str) -> bool:
    return bool(
        re.search(r'[\u3000-\u303f\u3040-\u309f\u30a0-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uF900-\uFAFF\uFF66-\uFF9F]',
                  text))


def format_dpath(dpath: DPath) -> str:
    return '.'.join(map(str, dpath))


def format_path(path: FDPath) -> str:
    return f"{path.path}:{format_dpath(path.dpath)}"


# 递归遍历嵌套字典结构的迭代器
def traverse_dict(d: Union[Dict, List], parent_path: DPath = ()) \
        -> Iterator[Tuple[DPath, str]]:
    if isinstance(d, dict):
        for key, value in d.items():
            if not (isinstance(key, str) or isinstance(key, int)):
                continue
            current_path = parent_path + (key,)
            if isinstance(value, dict) or isinstance(value, list):
                yield from traverse_dict(value, current_path)
            elif isinstance(value, str) and contains_japanese(value):
                yield current_path, value
    elif isinstance(d, list):
        for i, item in enumerate(d):
            yield from traverse_dict(item, parent_path + (i,))


def scan(path: Path, prg_callback: Callable[[float], None], warn_callback: Callable[[Exception], None]) \
        -> List[Tuple[FDPath, str]]:
    print("开始扫描")
    total_files = sum(1 for _ in path.rglob('*.json'))
    processed_files = 0

    result: List[Tuple[FDPath, str]] = []
    # 遍历文件
    for file in path.rglob('*.json'):
        print(file)
        try:
            text= file.read_text(encoding='utf-8')
            if not contains_japanese(text):
                continue
            data = json.loads(text)
            for dpath, v in traverse_dict(data):
                print(f"找到日文 {file}: {format_dpath(dpath)} = {v}")
                result.append((FDPath(path=file, dpath=dpath), v))

        except Exception as e:
            warn_callback(e)

        # 更新进度
        processed_files += 1
        progress = processed_files / total_files
        prg_callback(progress)  # 调用回调函数更新进度
    return result
