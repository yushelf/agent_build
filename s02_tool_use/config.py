"""
config.py — 配置加载层（整个项目的最底层依赖）。
读 settings.json，产出：WORKDIR / SETTINGS_PATH / MODEL / BASE_URL / client / SYSTEM。
不含工具，不含 loop。被 tools 包和 main 依赖。
"""
import os
import json
from pathlib import Path
from anthropic import Anthropic

# ── 工作目录 = 本项目目录（s02_tool_use/）────────────────
# agent 的所有文件操作都被 safe_path 圈在这个目录内，不能逃逸
WORKDIR = Path(__file__).resolve().parent

# ── 从 settings.json 加载（找父目录，回退到本项目内）──────
_SETTINGS_CANDIDATES = [
    WORKDIR.parent / "settings.json",   # agent_build/settings.json（与 Claude Code 共用）
    WORKDIR / "settings.json",          # s02_tool_use/settings.json（回退）
]
SETTINGS_PATH = next((p for p in _SETTINGS_CANDIDATES if p.exists()), None)
if SETTINGS_PATH is None:
    raise FileNotFoundError("找不到 settings.json，请放在 s02_tool_use/ 的父目录或同目录")

with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
    settings = json.load(f)

env_cfg = settings.get("env", {})
# 注入 os.environ，让 Anthropic SDK 自动读取 ANTHROPIC_BASE_URL / ANTHROPIC_AUTH_TOKEN
for key, value in env_cfg.items():
    os.environ[key] = str(value)

# 模型：优先 env.ANTHROPIC_MODEL，回退顶层 model
MODEL = env_cfg.get("ANTHROPIC_MODEL") or settings.get("model")
if not MODEL:
    raise RuntimeError("settings.json 中未找到 ANTHROPIC_MODEL 或 model 字段")

BASE_URL = os.getenv("ANTHROPIC_BASE_URL")
client = Anthropic(base_url=BASE_URL)

SYSTEM = (
    f"You are a coding agent working in {WORKDIR}. "
    f"Use the provided tools to solve tasks. Act, don't explain."
)
