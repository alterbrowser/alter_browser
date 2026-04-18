"""
Pytest configuration — 确保 alterbrowser 包可被导入（无需 pip install）。
"""
import sys
from pathlib import Path

# 把 repo 根目录（alterbrowser/ 包的父目录）加入 sys.path，便于 `pytest` 直接运行
_PKG_PARENT = Path(__file__).resolve().parent.parent
if str(_PKG_PARENT) not in sys.path:
    sys.path.insert(0, str(_PKG_PARENT))
