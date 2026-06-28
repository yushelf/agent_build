"""
agent.py — agent loop 本体。纯函数，零工具知识。

解耦的检验标准就在这个文件里：
  - 不 import 任何具体工具（没有 'from tools import ...'）
  - TOOLS（schema 列表）和 handlers（名字→函数）都是参数传进来的

做到这点，换一套完全不同的工具集，这个函数一行不改。
loop 是通用引擎，工具是插件。
"""


def agent_loop(client, model: str, system: str, tools: list,
               handlers: dict, messages: list):
    """
    核心循环：
      调 LLM → 模型决定要不要用工具 → 用就执行并喂回结果 → 再调 LLM
      直到模型 stop_reason != "tool_use"（它自己决定停下）。
    """
    turn = 0
    while True:
        turn += 1
        print(f"\n\033[1;36m─── Turn {turn} │ 调用 LLM ───\033[0m")
        response = client.messages.create(
            model=model, system=system, messages=messages,
            tools=tools, max_tokens=8000,
        )
        # 记录 assistant 这一轮的输出
        messages.append({"role": "assistant", "content": response.content})

        # 打印模型这一轮的文本（思考 / 回答）
        for block in response.content:
            if block.type == "text" and block.text.strip():
                print(f"\033[32m{block.text}\033[0m")

        # 停机原因：tool_use=继续调工具，end_turn=结束
        print(f"\033[90m[stop_reason: {response.stop_reason}]\033[0m")

        # 不再调工具 = 模型自己做完了，循环结束
        if response.stop_reason != "tool_use":
            print(f"\033[90m→ 不再调用工具，循环结束（共 {turn} 轮）\033[0m")
            return

        # 执行每个工具调用，收集结果
        results = []
        for block in response.content:
            if block.type == "tool_use":
                # 查表分发——agent 自己不知道有哪些工具，全靠 handlers 这个映射
                handler = handlers.get(block.name)
                print(f"\033[33m[工具] {block.name}\033[0m")
                if handler is None:
                    output = f"Error: Unknown tool: {block.name}"
                else:
                    output = handler(**block.input)
                # 结果预览（完整结果已喂回模型，这里只显示前 500 字符）
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
        # 把工具结果喂回模型，下一轮 LLM 能看到
        messages.append({"role": "user", "content": results})
        print(f"\033[90m→ 结果已喂回模型，进入下一轮\033[0m")
