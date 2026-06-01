"""
registry.py — Gộp tất cả tools từ 5 người thành 1 danh sách
Import file này trong agent và run scripts
"""
from tools.cs_tools_p1 import TOOLS_P1
from tools.cs_tools_p2 import TOOLS_P2
from tools.cs_tools_p3 import TOOLS_P3
from tools.cs_tools_p4 import TOOLS_P4
from tools.cs_tools_p5 import TOOLS_P5

ALL_TOOLS = TOOLS_P1 + TOOLS_P2 + TOOLS_P3 + TOOLS_P4 + TOOLS_P5

# Map name → function để agent gọi nhanh
TOOL_MAP = {t["name"]: t["function"] for t in ALL_TOOLS}
