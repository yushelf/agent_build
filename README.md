# agent_build

学习用 AI coding agent 最小实现。

## 内容

- `s01_agent_loop/code.py` — Agent Loop 核心模式：`while stop_reason == "tool_use"` 循环调用 LLM + 工具，直到模型自行停止。
- `settings.example.json` — 配置模板（密钥已脱敏）。

## 配置

复制配置模板，填入你自己的密钥：

```bash
cp settings.example.json settings.json
```

然后编辑 `settings.json`，把 `ANTHROPIC_AUTH_TOKEN` 改成你自己的 token。

> **注意**：`settings.json` 已在 `.gitignore` 中忽略，真实密钥不会被提交。

## 运行

```bash
pip install anthropic
python s01_agent_loop/code.py
```

## 工作原理

```
+----------+      +-------+      +---------+
|   User   | ---> |  LLM  | ---> |  Tool   |
|  prompt  |      |       |      | execute |
+----------+      +---+---+      +----+----+
                      ^               |
                      |   tool_result |
                      +---------------+
                      (loop continues)
```

核心就是把工具结果喂回模型，循环往复，直到模型决定停止。生产级 agent 在此基础上叠加策略、hooks 和生命周期控制。
