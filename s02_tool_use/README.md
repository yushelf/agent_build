# s02: Tool Use — 解耦版

s01 把整个 agent 塞进一个文件，工具只有 bash。s02 拆成四层，工具变成可插拔的插件：换一套工具，agent loop 一行不改。

## 这一步学了什么

### 1. 工具 = handler 函数 + schema dict

- **handler** 是真正干活的 Python 函数（如 `run_bash(command)`）
- **schema** 是喂给 API 的 `tools=` 参数，告诉模型"有这个工具、参数长这样"

两者一一对应，分开存放。`tools/bash.py` 里就是 `run_bash` + `BASH_TOOL` 这一对。

### 2. 查表分发

agent loop 自己**不知道有哪些工具**。它拿到模型返回的 `tool_use` block，用 `block.name` 去 `TOOL_HANDLERS` 映射里查到对应函数，调 `handler(**block.input)`。加工具不用动 loop。

```python
handler = handlers.get(block.name)        # 查表
output = handler(**block.input)           # 分发
```

### 3. 解耦的四层

```
config.py   ── 配置加载（WORKDIR / MODEL / client / SYSTEM），最底层
   │
tools/      ── 工具包：每个工具一个模块（handler + schema）
   │          __init__.py 负责登记成 TOOLS + TOOL_HANDLERS
   │
agent.py    ── 纯 loop，零工具知识；tools / handlers 全是参数传进来
   │
main.py     ── 入口 / REPL，把三层接起来
```

**解耦的检验标准**：`agent.py` 里没有 `from tools import ...`。做到这点，换一套完全不同的工具集，这个函数一行不改。loop 是通用引擎，工具是插件。

### 4. safe_path 路径越界校验

所有文件操作先过 `safe_path`：把相对路径解析到 `WORKDIR` 内，用 `is_relative_to(WORKDIR)` 校验，禁止逃逸。这是把 agent 圈在沙箱里的最小手段——比 s01 纯靠危险命令黑名单靠谱。

```python
def safe_path(p: str) -> Path:
    path = (WORKDIR / p).resolve()
    if not path.is_relative_to(WORKDIR):
        raise ValueError(f"Path escapes workspace: {p}")
    return path
```

## 工具清单

| 工具 | handler | 作用 |
|---|---|---|
| `bash` | `run_bash` | 执行 shell 命令（带危险命令护栏） |
| `read_file` | `run_read` | 读文件（支持 `limit` 截断） |
| `write_file` | `run_write` | 写文件 |
| `edit_file` | `run_edit` | 精确替换一段文本（仅首处） |
| `glob` | `run_glob` | 按模式查找文件 |

加新工具的流程：写一个新模块（handler + schema）→ 在 `tools/__init__.py` 加一行 import + 两个登记。`agent.py` 永远不用改。

## 运行

```bash
pip install anthropic
python s02_tool_use/main.py
```

配置仍读父目录的 `settings.json`（与 s01、Claude Code 共用同一份）。

## 与 s01 的对比

| | s01 | s02 |
|---|---|---|
| 结构 | 单文件 | 四层解耦 |
| 工具 | 1 个（bash），硬编码在 loop 里 | 5 个，可插拔 |
| loop | 绑定具体工具 | 纯函数，工具作参数 |
| 安全 | 危险命令黑名单 | + `safe_path` 路径隔离 |

**核心收获**：把 loop 和工具的边界划干净，agent 的复杂度才能随工具增长而不爆炸。
