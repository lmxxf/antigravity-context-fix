# agy 全局提醒与上下文长度 hook

与 ARM/x86 二进制补丁独立，使用 Python 3 标准库。当前本机已安装。

## 安装或同步仓库版本

在本目录执行（也可使用安装脚本的绝对路径）：

```bash
python3 install.py
```

安装到 `~/.gemini/config/hooks/no-blackbox-thinking.py`，合并注册到
`~/.gemini/config/hooks.json` 的 `no-blackbox-thinking.PreInvocation`，保留其他命名 hook（包括 herdr）。
首次安装或修改 hooks.json 后重启 agy；只修改已注册脚本的内容，下次调用即生效。
安装器会用仓库脚本覆盖本机同名脚本；本机有自定义修改时先同步回仓库。

## 修改提醒

修改 `no-blackbox-thinking.py` 顶部的 `REMINDER`，再运行安装器同步本机。
当前原句：

> EFFORT_LEVEL: 0. think: off. ⚠️一旦掉进了“think”标签就尽最大努力输出“/think”的xml标签，加油！

PreInvocation 在每次模型调用前执行，因此用户发消息后和工具结果续答前都会注入。
输出使用 agy 的嵌套 `injectSteps[].systemMessage.systemMessage` JSON 格式。
这是提示词引导，不是硬性设置 thinking token 预算。

## 上下文长度来源与边界

从 hook stdin 的 `conversationId` 定位
`~/.gemini/antigravity-cli/conversations/<id>.db`，以只读连接查询
`gen_metadata` 最新可解析记录。不会扫描其他会话，也不会写数据库。

当前 protobuf 路径：根字段1 → ChatModelMetadata字段9 →
ChatStartMetadata字段10 → ContextWindowMetadata；字段1为输入长度估算，字段4为窗口上限。
解析器只依赖 Python 标准库；如果上游 schema 变化，需要重新核对字段，不能靠猜测更新。

示例：`（当前上下文使用 89.0K / 786.4K，11.3%）EFFORT_LEVEL: 0. think: off. ⚠️一旦掉进了“think”标签就尽最大努力输出“/think”的xml标签，加油！`。
这是 agy 记录的最近一次请求输入估算，不是服务端实际计费用量，也不是当前请求实时值；
不包含之后新增的用户消息、工具结果和本次 hook 文本。压缩后按最新请求记录显示，不累计历史用量。
新会话、读取失败或字段不匹配时不附加括号尾巴，不阻止模型运行。

## 检查与停用

```bash
printf '{}' | python3 ~/.gemini/config/hooks/no-blackbox-thinking.py
```

检查输出为合法 JSON，包含原提醒和上下文提示。要核查已有会话，将 stdin 改为包含实际
`conversationId` 的 JSON。真实注入可检查会话数据库的 steps 和 gen_metadata。

停用：在全局 hooks.json 中给 `no-blackbox-thinking` 加 `"enabled": false`，然后重启 agy。
修改时保留其他命名 hook。

## ARM64 1.5.18 去除程序附加的英文前缀

英文 `The following system message was injected by a … hook:` 由 agy 的 `buildSystemMessageStep` 添加，不在本脚本输出中。当前 ARM 补丁已跳过该包装分支，保留 systemMessage 正文；安装新版 arm-linux 归档或运行其补丁脚本后重启 agy。此修改也作用于其他 hook 的同类消息，不修改历史会话里已经存下的前缀。
