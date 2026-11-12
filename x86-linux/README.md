# Antigravity CLI Linux x86_64 1.5.7 修正版（2026-11-12）

## 启动与自动压缩开关（x86_64）

**当前归档默认开启自动压缩，直接运行 `agy` 即可，无需附加参数。**
开关会保持到下次切换；若之前设为 `off`，再次启动仍为关闭状态。

本机已安装快捷命令：

| 操作 | 命令 |
|---|---|
| 查看当前状态 | `agy-auto-compact status` |
| 开启自动压缩 | `agy-auto-compact on` |
| 关闭自动压缩 | `agy-auto-compact off` |
| 启动 | `agy` |

**切换后必须退出并重新启动 agy，已运行的进程不会立即改变。** 夜间无人值守工作建议保持 `on`。
开关不改变扩大的输入窗口：Argon 983040、Carbon 786432 tokens。
自动压缩与自动升级是两个独立功能。

换机器若没有快捷命令，可在 ai-theorys-study 仓库根目录运行：

```bash
python3 wechat/assets/340-A/x86-linux/auto-compact.py status
python3 wechat/assets/340-A/x86-linux/auto-compact.py on
python3 wechat/assets/340-A/x86-linux/auto-compact.py off
```

恢复归档会回到默认 `on`。脚本只接受匹配构建的完整哈希；升级后需要重新适配补丁。
此开关仅适用于本目录的 x86_64 归档，不能套用于 ARM。

## 恢复

```bash
python3 wechat/assets/340-A/x86-linux/restore-agy.py
```

脚本校验归档并备份当前安装，原子替换 ~/.local/bin/agy。随后重启 agy。
新建会话可重新加载完整规则；已裁剪或压缩的历史不会自动恢复。
这份归档只适用于 Linux x86_64；恢复脚本不是未来版本的自动补丁器。

## 修改

- Argon High/Medium/Low 1417/1418/1419，以及 Carbon High/Medium/Low 1427/1437/1438，最终 max_token_limit=1000000。
- 实际输入窗口 Argon=983040；Carbon=786432（保留262144输出预算）。
- 自动 checkpoint 默认开启，保留原生触发与摘要流程；可通过 auto-compact.py 关闭。
- 三处规则/技能读取上限24000→1048576字节；两项规则预算各131072 tokens。

## 验证

六档均正常回复OK，两处元数据窗口一致，完整加载123138字节AGENTS.md。
原版Argon Low与Carbon Low两处窗口均为256000。未跑超过256K长会话压力测试。
补丁重复运行、归档解压与安装版一致、逆向还原原版哈希、跳板直接引用检查通过。
记录见 verification.txt；完整文件校验：在本目录运行 sha256sum -c SHA256SUMS。
核查新会话：python3 verify-argon-x86.py <conversation_id> --agents /项目路径/AGENTS.md
Carbon须追加 --expected-limit 786432，默认983040用于Argon。

## 维护

未知哈希必须重新定位，禁止复用旧偏移。
pclntab=0x17652a0，Go text=0x6eef080。getter：planner+8、model+64、limit+12。
配置出口0x8685954→0xa8a4300；RDX为外层配置，RAX为checkpoint，RSI临时寄存器。
匹配六个模型编号后写12(%rax)，重放原指令，返回0x868595b。
checkpointNeeded入口0x8946260及函数体已恢复原版；跳板迁至.text内0xa8a4300的INT3对齐填充区。
文件读取点0x89a4069、0x89a4fe5、0x89aa047。
预算11字节指令组0x89ad5ec→0xa8a4360，设置EBX/EAX各131072，返回0x89ad5f7。
汇编见argon-x86-trampoline.s，机器码trampoline.bin，函数定位functions.json。
fix-argon-context-x86.py只接受本构建清单中的哈希；原版备份仅存本机。
原版SHA256：5df525a2d6908989c57b897723caea66e00d7c4d2e24411f91ad306989574642
修改版SHA256：3cac18bd597d4c6e75b27556ec4ec4cf285a2ca7d63884f7a68cbcf41acc6ddf
解压大小：280564136字节。

## 自动压缩验证

独立测试副本临时将窗口降至60000，填充输入后出现 `CHECKPOINT DONE`，随后继续回复 `OK`；正式二进制窗口未降低。未进行完整786432/983040满窗压力测试。
开启表示恢复原生自动 checkpoint 流程，不保证网络或摘要服务故障时仍能继续工作。
