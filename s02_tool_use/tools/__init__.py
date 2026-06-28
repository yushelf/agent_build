"""
tools/__init__.py — 工具加载（解耦的关键文件）。
从各工具模块导入 handler + schema，组装成两个集合：
  - TOOLS：schema 列表，直接喂给 API 的 tools= 参数
  - TOOL_HANDLERS：名字→函数 的映射，agent loop 查表调用

加新工具时：写一个新模块（handler + schema），然后在这里加一行 import + 两个登记。
agent.py 永远不用改。这就是"工具加载"独立出来的意义。
"""
from .bash import run_bash, BASH_TOOL
from .files import (
    run_read, run_write, run_edit, run_glob,
    READ_TOOL, WRITE_TOOL, EDIT_TOOL, GLOB_TOOL,
)

# 喂给 Anthropic API 的工具 schema 列表
TOOLS = [BASH_TOOL, READ_TOOL, WRITE_TOOL, EDIT_TOOL, GLOB_TOOL]

# 名字 → handler 函数。agent loop 靠这个查表分发
TOOL_HANDLERS = {
    "bash": run_bash,
    "read_file": run_read,
    "write_file": run_write,
    "edit_file": run_edit,
    "glob": run_glob,
}
