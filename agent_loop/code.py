#!/usr/bin/env python3
"""
agent_loop.py - The Agent Loop
The entire secret of an AI coding agent in one pattern:
    while stop_reason == "tool_use":
        response = LLM(messages, tools)
        execute tools
        append results
    +----------+      +-------+      +---------+
    |   User   | ---> |  LLM  | ---> |  Tool   |
    |  prompt  |      |       |      | execute |
    +----------+      +---+---+      +----+----+
                          ^               |
                          |   tool_result |
                          +---------------+
                          (loop continues)
This is the core loop: feed tool results back to the model
until the model decides to stop. Production agents layer
policy, hooks, and lifecycle controls on top.
配置来源：读取父目录的 settings.json（与 Claude Code 共用同一份配置）
Usage:
    pip install anthropic
    python agent_loop/code.py
"""
import os
import json
import subprocess
from pathlib import Path
from anthropic import Anthropic

# ── 从 settings.json 加载配置（不再读环境变量/.env）────────
# 优先找脚本父目录的 settings.json，回退到脚本同目录
_SETTINGS_CANDIDATES = [
    Path(__file__).resolve().parent.parent / "settings.json",
    Path(__file__).resolve().parent / "settings.json",
]
SETTINGS_PATH = next((p for p in _SETTINGS_CANDIDATES if p.exists()), None)
if SETTINGS_PATH is None:
    raise FileNotFoundError("找不到 settings.json，请放在 agent_loop/ 的父目录或同目录")

with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
    settings = json.load(f)

env_cfg = settings.get("env", {})
# 注入到 os.environ，让 Anthropic SDK 自动读取
# ANTHROPIC_BASE_URL（自定义转发地址）和 ANTHROPIC_AUTH_TOKEN（Bearer 认证）
for key, value in env_cfg.items():
    os.environ[key] = str(value)

# 模型：优先 env.ANTHROPIC_MODEL，回退顶层 model
MODEL = env_cfg.get("ANTHROPIC_MODEL") or settings.get("model")
if not MODEL:
    raise RuntimeError("settings.json 中未找到 ANTHROPIC_MODEL 或 model 字段")

client = Anthropic(base_url=os.getenv("ANTHROPIC_BASE_URL"))
SYSTEM = f"You are a coding agent at {os.getcwd()}. Use bash to solve tasks. Act, don't explain."
# ── Tool definition: just bash ────────────────────────────
TOOLS = [{
    "name": "bash",
    "description": "Run a shell command.",
    "input_schema": {
        "type": "object",
        "properties": {"command": {"type": "string"}},
        "required": ["command"],
    },
}]
# ── Tool execution ────────────────────────────────────────
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
        r = subprocess.run(command, shell=True, cwd=os.getcwd(),
                           capture_output=True, text=True, timeout=120)
        out = (r.stdout + r.stderr).strip()
        return out[:50000] if out else "(no output)"
    except subprocess.TimeoutExpired:
        return "Error: Timeout (120s)"
    except (FileNotFoundError, OSError) as e:
        return f"Error: {e}"
# ── The core pattern: a while loop that calls tools until the model stops ──
def agent_loop(messages: list):
    turn = 0
    while True:
        turn += 1
        print(f"\n\033[1;36m─── Turn {turn} │ 调用 LLM ───\033[0m")
        response = client.messages.create(
            model=MODEL, system=SYSTEM, messages=messages,
            tools=TOOLS, max_tokens=8000,
        )
        # Append assistant turn
        messages.append({"role": "assistant", "content": response.content})

        # 打印模型这一轮输出的文本（思考过程 / 回答）
        for block in response.content:
            if block.type == "text" and block.text.strip():
                print(f"\033[32m{block.text}\033[0m")

        # 打印停机原因：tool_use=继续调工具，end_turn=结束
        print(f"\033[90m[stop_reason: {response.stop_reason}]\033[0m")

        # If the model didn't call a tool, we're done
        if response.stop_reason != "tool_use":
            print(f"\033[90m→ 不再调用工具，循环结束（共 {turn} 轮）\033[0m")
            return

        # Execute each tool call, collect results
        results = []
        for block in response.content:
            if block.type == "tool_use":
                cmd = block.input["command"]
                print(f"\033[33m[工具] bash\n$ {cmd}\033[0m")
                output = run_bash(cmd)
                # 工具结果预览（完整结果已喂回模型，这里只显示前 500 字符）
                if len(output) <= 500:
                    preview = output
                else:
                    preview = output[:500] + f"\n...（共 {len(output)} 字符，已截断）"
                print(f"\033[90m[结果]\n{preview}\033[0m")
                results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": output,
                })
        # Feed tool results back, loop continues
        messages.append({"role": "user", "content": results})
        print(f"\033[90m→ 结果已喂回模型，进入下一轮\033[0m")
# ── Entry point ──────────────────────────────────────────
if __name__ == "__main__":
    print("s01: Agent Loop")
    print(f"配置文件: {SETTINGS_PATH}")
    print(f"模型: {MODEL}  Base URL: {os.getenv('ANTHROPIC_BASE_URL')}")
    print("输入问题，回车发送。输入 q 退出。\n")
    history = []
    while True:
        try:
            query = input("\033[36ms01 >> \033[0m")
        except (EOFError, KeyboardInterrupt):
            break
        if query.strip().lower() in ("q", "exit", ""):
            break
        history.append({"role": "user", "content": query})
        agent_loop(history)
        print()
