Antigravity CLI Linux x86_64 1.5.5 修正版（2026-11-11）

恢复：python3 wechat/assets/340-A/x86-linux/restore-agy.py
脚本校验归档并备份当前安装，原子替换 ~/.local/bin/agy。随后重启 agy。
新建会话可重新加载完整规则；已裁剪或压缩的历史不会自动恢复。
这份归档只适用于 Linux x86_64；恢复脚本不是未来版本的自动补丁器。

修改：
- Argon High/Medium/Low 1417/1418/1419，以及 Carbon High/Medium/Low 1427/1437/1438，最终 max_token_limit=1000000。
- 实际输入窗口 Argon=983040；Carbon=786432（保留262144输出预算）。
- 自动 checkpoint 返回 false,nil；不代表所有裁剪关闭，手动 /compact 未测试。
- 三处规则/技能读取上限24000→1048576字节；两项规则预算各131072 tokens。

验证：六档均正常回复OK，两处元数据窗口一致，完整加载122885字节AGENTS.md。
原版Argon Low与Carbon Low两处窗口均为256000。未跑超过256K长会话压力测试。
补丁重复运行、归档解压与安装版一致、逆向还原原版哈希、跳板直接引用检查通过。
记录见 verification.txt；完整文件校验：在本目录运行 sha256sum -c SHA256SUMS。
核查新会话：python3 verify-argon-x86.py <conversation_id> --agents /项目路径/AGENTS.md
Carbon须追加 --expected-limit 786432，默认983040用于Argon。

维护：未知哈希必须重新定位，禁止复用旧偏移。
pclntab=0x1725d70，Go text=0x6d94080。getter：planner+8、model+64、limit+12。
配置出口0x8507b74→0x879a760；RDX为外层配置，RAX为checkpoint，RSI临时寄存器。
匹配六个模型编号后写12(%rax)，重放原指令，返回0x8507b7b。
checkpointNeeded入口0x879a740短路，后部函数体作为跳板。
文件读取点0x87f9a29、0x87fa9a5、0x87ffa65。
预算11字节指令组0x880300c→0x879a7c0，设置EBX/EAX各131072，返回0x8803017。
汇编见argon-x86-trampoline.s，机器码trampoline.bin，函数定位functions.json。
fix-argon-context-x86.py只接受本构建清单中的哈希；原版备份仅存本机。
原版SHA256：89f16bdb87f62e6d07484c52e6bafe76a81b0fd13d740110c77dc3c3c8d8d8b6
修改版SHA256：e17edb49873b90f48a3c4b6b4ccc986ad7adb8e5ab4d3d79c893e81e5a39cbfb
解压大小：247853456字节。
