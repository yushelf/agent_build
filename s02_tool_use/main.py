"""
main.py — 入口 / REPL。把 config、tools、agent 三层接起来。
这是唯一知道"用什么模型 + 带哪些工具 + 怎么跑 loop"的地方。
"""
from config import client, MODEL, SYSTEM, SETTINGS_PATH, WORKDIR, BASE_URL
from tools import TOOLS, TOOL_HANDLERS
from agent import agent_loop

try:
    import readline
    # macOS 的 libedit 在处理中文输入时有退格问题，这四行修复它
    readline.parse_and_bind('set bind-tty-special-chars off')
    readline.parse_and_bind('set input-meta on')
    readline.parse_and_bind('set output-meta on')
    readline.parse_and_bind('set convert-meta off')
except ImportError:
    pass


def main():
    print("s02: Tool Use — 解耦版（config / tools / agent / main 分离）")
    print(f"配置文件: {SETTINGS_PATH}")
    print(f"工作目录: {WORKDIR}")
    print(f"模型: {MODEL}  Base URL: {BASE_URL}")
    print(f"已加载工具: {list(TOOL_HANDLERS.keys())}")
    print("输入问题，回车发送。输入 q 退出。\n")

    history = []
    while True:
        try:
            query = input("\033[36ms02 >> \033[0m")
        except (EOFError, KeyboardInterrupt):
            break
        if query.strip().lower() in ("q", "exit", ""):
            break
        history.append({"role": "user", "content": query})
        # 三层接线：client/model/system 来自 config，TOOLS/HANDLERS 来自 tools 包
        agent_loop(client, MODEL, SYSTEM, TOOLS, TOOL_HANDLERS, history)
        print()


if __name__ == "__main__":
    main()
