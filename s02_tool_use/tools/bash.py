"""
tools/bash.py — bash 工具：执行 shell 命令。
一个工具 = 一个 handler 函数 + 一个 schema dict。
"""
import subprocess
from config import WORKDIR


def run_bash(command: str) -> str:
    # 危险命令拦截（示意性护栏，非生产级安全防护）
    # 生产 agent 不靠黑名单做安全——靠沙箱和权限隔离。这里只是防教学时手滑误删
    # 命令名：匹配第一个词，避免 'del' 子串误伤 'delete' / 'delta'
    DANGEROUS_CMDS = {"del", "rmdir", "rd", "format", "diskpart",
                      "shutdown", "reboot", "sudo"}
    # 复合模式：带参数的危险组合（子串匹配）
    DANGEROUS_PATTERNS = ["rm -rf /", "rm -rf ~", "rm -rf *", "> /dev/"]
    stripped = command.strip()
    first = stripped.split()[0].lower() if stripped else ""
    if first in DANGEROUS_CMDS or any(p in command for p in DANGEROUS_PATTERNS):
        return "Error: Dangerous command blocked"
    try:
        r = subprocess.run(command, shell=True, cwd=WORKDIR,
                           capture_output=True, text=True, timeout=120)
        out = (r.stdout + r.stderr).strip()
        return out[:50000] if out else "(no output)"
    except subprocess.TimeoutExpired:
        return "Error: Timeout (120s)"
    except (FileNotFoundError, OSError) as e:
        return f"Error: {e}"


# 这个工具的 schema——直接喂给 Anthropic API 的 tools= 参数
BASH_TOOL = {
    "name": "bash",
    "description": "Run a shell command.",
    "input_schema": {
        "type": "object",
        "properties": {"command": {"type": "string"}},
        "required": ["command"],
    },
}
