Antigravity CLI（agy）Linux x86_64 1.5.0 修正版
更新日期：2026-11-04

【怎么恢复】

退出 agy，在本仓库根目录运行：

python3 wechat/assets/340-A/x86-linux/restore-agy.py

也可以使用 restore-agy.py 的绝对路径。脚本解压同目录 agy.gz、检查 SHA256，
将当前安装版本备份到 ~/.local/share/agy-patches/，再原子替换 ~/.local/bin/agy。
已是这一份修改版则不重复操作。只需 Python 3 标准库。
这是 Linux x86_64 完整程序，ARM64 不能用。

然后重启 agy，新建会话，让完整 AGENTS.md 重新加载。
旧会话已经丢失的历史不会自动恢复。
自动升级覆盖补丁后，再运行恢复脚本可恢复本目录归档的 1.5.0，
不是为未来新版本自动打补丁。

【改了什么】

- Argon High/Medium/Low（1417/1418/1419）在最终配置合并出口
  设置 max_token_limit=1000000，实际请求上限为983040 tokens。
- 自动 checkpoint 判断返回 false,nil（同时清零 AX/BX/CX）。
- 三处规则/技能单文件读取上限：24000 → 1048576 字节。
- rules/customizations 两项最终 token 预算分别改为131072。

其他模型的窗口不修改。规则读取与预算修改对整个客户端生效。
自动 checkpoint 关闭不等于所有裁剪关闭；手动 /compact 未验证。

【验证】

Low、Medium、High 三档分别新开会话发送小请求，均正常回复 OK。
每档 executor_metadata 与 gen_metadata 实际上限均为983040。
user_rules 逐字包含本地 AGENTS.md 的119012字节全文，没有预算排除提示。
完整记录见 verification.txt。未重跑超过256K的长会话压力测试。
启动、补丁重复运行、归档解压与安装版逐字节一致、逆向补丁还原原版哈希均已检查。

【文件】

agy.gz                       修改版完整可执行文件，解压后238604688字节
restore-agy.py               安装/恢复归档
SHA256SUMS                   本目录文件校验清单
agy-x86-patches.json         原版/修改版哈希、每处修改前后字节与偏移
fix-argon-context-x86.py     对指定原版构建打补丁；支持 --target
argon-x86-trampoline.s      跳板汇编源码
trampoline.bin              跳板机器码
functions.json              新版 pclntab 定位结果，含实际虚拟地址
verify-argon-x86.py          只读核查会话数据库
verification.txt            三档真实请求的验证记录

核查自己新建的会话：
python3 verify-argon-x86.py <conversation_id> --agents /项目路径/AGENTS.md

原版只备份在本机 ~/.local/share/agy-patches/，不放入仓库。
原版 SHA256：b9043860a06a3bfa70b68f06c3d4527abc16207767f14ae9d1e06e3026081862
修改版 SHA256：59f0ec9838dd8a7252a41b7d257ee80e88fbe007be563748b6f49270864078f8

【1.5.0 重新定位与维护】
未知哈希必须重新定位，不能沿用旧偏移或删除哈希检查。
pclntab=0x1676b70，Go text=0x6a0a080。getter确认planner+8、model+64、limit+12。
最终出口0x816b494改跳0x8343000：本版RDX是外层配置，RAX是checkpoint，RSI作临时寄存器。
匹配1417..1419时写1000000到12(%rax)，重放mov %rax,16(%rdx)与mov %rdx,%rax，返回0x816b49b。
checkpointNeeded入口0x8342fe0返回false,nil，后部函数体借作两段跳板。
规则读取点：0x839dd89、0x839ed05、0x83a3dc5，24000改1MiB。
预算读取现在是4字节指令，不能硬塞5字节立即数：0x83a6d8c的11字节指令组改跳0x8343060，
保留mov %rax,%rcx，设置EBX和EAX各131072，返回0x83a6d97继续原调用。覆盖配置及默认两条路径。
源码argon-x86-trampoline.s含两段跳板，中间.org填充区同处于已短路函数体。
原版Low小请求两处窗口仍为256000。修改后三档证据见verification.txt。
原版只留本机备份；恢复修改后须重启。手动compact及本版超过256K长会话未测试。
