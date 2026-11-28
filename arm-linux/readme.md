# agy ARM64 补丁维护操作说明

更新：2026-11-28。此目录只保留当前修改版；用于 agy 自动升级后恢复长上下文、完整规则注入和关闭自动压缩。按用户指定保留 `readme.md` 作为操作入口，供后续 agent/skill 读取，不自动安装到技能目录。

## 当前产物

| 文件 | 用途 |
|---|---|
| `agy.gz` | 已修改的 Linux ARM64 1.5.18 可执行文件，解压后 262689456 字节 |
| `agy.sha256` | 解压后的执行文件校验值 |
| `agy-patches.json` | 原版/修改版 SHA256、每处文件偏移和修改前后完整字节 |
| `fix-argon-context.py` | 此构建的完整幂等补丁；支持 `--target`，默认修改 `~/.local/bin/agy` |
| `verify-request.py` | 只读检查指定会话数据库中的请求窗口、规则全文注入 |
| `verification.json` | 当前版本已完成的小请求验证记录；不是新版本的验证证据 |

原版 SHA256：`a0d0c7e6ee545e0d8ef0e3490de4626e2e86e169de1a5a5133b232b771345a67`

修改版 SHA256：`11b8075620441f578e27dba02cb3a2f4779d6c2d7556b995a0708ae5931df337`

目录不存原版二进制。安装位置保留 `agy-1.5.18-original.bak`；补丁脚本创建备份且不会覆盖不同内容的备份。旧版 README、封面及归档已按要求移除，x86-linux 不在本次维护范围。

## 已知版本：恢复或重新打补丁

先检查 `command -v agy`、`file`、`agy --version` 和 SHA256。同为 1.5.18 也可能重新构建，以哈希为准。

对匹配原版哈希的文件执行：

```bash
python3 fix-argon-context.py
```

已是修改版则报告 Already patched；本脚本只接受当前构建原版或修改版哈希。未知哈希直接退出，不能删校验硬套。脚本在同目录写临时文件、保留执行权限，再原子替换，避免对运行中的文件原地写入。

解包归档用于检查或恢复（当前目录已有解包文件时先确认它的用途）：

```bash
gzip -dk agy.gz
chmod +x agy
sha256sum -c agy.sha256
```

需要覆盖安装时，先备份当前安装版，再把校验通过的解包文件通过临时文件原子替换到安装路径。恢复归档会回到本目录的版本；用户要求适配新版本时，走下一节，不用旧归档冒充升级适配。

## 窗口与压缩阈值

ARM64 1.5.18 在最终配置出口覆写 Argon、Carbon、Neon 十档窗口预算为 1000000，并关闭自动 checkpoint。配置出口 0x8a30804，checkpointNeeded 入口 0x8cdc5c0，跳板 0x8cdc5e0。补丁仅接受本构建原版或修改版哈希。

### 两层规则限制一起处理

单文件24000字节截断与总预算20000 tokens是两件事。只放开字节数会让整份文件超过总预算，最后完全不注入。

本构建三处 `mov x2,#24000`（`0xd28bb802`）改为 `0xd2a00202`：

| 文件偏移 | 函数 |
|---|---|
| `0x8d3c6d8` | readGlobalRules |
| `0x8d3d3d4` | parseRuleFile |
| `0x8d419a4` | convertSkillPath |

总预算要修改实际消费的配置读取路径和默认路径，两项共四处：

| 偏移 | 原指令 | 新指令 |
|---|---|---|
| `0x8d442c4` | `0xb98000e7` | `0xd2a00047` |
| `0x8d442d4` | `0xd289c407` | `0xd2a00047` |
| `0x8d44324` | `0xb98000c6` | `0xd2a00046` |
| `0x8d44334` | `0xd289c406` | `0xd2a00046` |

即 x7/x6 都设131072。函数前部还存在用于判断是否配置预算的读取，不要误认成最终消费点；沿控制流追到汇合及预算参数传递处。

### 制作补丁与验证

先保存原版哈希和独立备份，再生成每处原字节/新字节清单。写入前校验整个构建哈希及每处原指令，修改后校验文件长度、指令和预期哈希。未知版本或结构不符时停止写入，继续定位；不得靠试偏移覆盖可执行文件。

先检查 `--version` 能启动和重复运行脚本幂等，再发一条不调用工具的小请求；启动成功不代表补丁生效。在包含实际 AGENTS.md 的项目根目录开新会话：

```bash
agy --model gemini-4-argon-low --print '只回复 OK，不调用工具。' --print-timeout 45s --output-format json
```

取输出的 conversation_id，运行：

```bash
python3 verify-request.py <conversation_id> --agents /实际项目/AGENTS.md
```

该脚本读取 `~/.gemini/antigravity-cli/conversations/<id>.db`。它按当前 protobuf 字段号检查 gen_metadata：ChatModelMetadata→ChatStartMetadata→ContextWindowMetadata.max_context_tokens；prompt_sections 中 user_rules 必须逐字包含本地文件，并且没有预算排除提示。新版本字段变化时先从二进制 protobuf descriptor 核对，不能把解析失败直接当补丁失败。

同时核对 executor_metadata 中运行配置的 checkpoint 上限。当前 schema：executor 根字段10→CascadeConfig 字段2→CheckpointConfig 字段5；gen 根字段1→chat 字段9→start 字段10→window 字段4。脚本当前检查后者，前者用字段解析核对。

当前构建十档真实请求结果见 verification.json；必须同时检查 executor/gen 窗口和完整规则注入。未做超过256K的长会话压力测试；1.3.5 曾达到474.8K，不能当新版验收。需要完整长会话验收时交用户运行，再检查历史是否保留及是否裁剪。

## 每次更新本目录

确认本机补丁验证通过后，更新同名文件，不堆 v1/v2。以当前安装文件生成 `agy.gz`，同步哈希、补丁脚本、字节清单与验证记录；解压逐字节比对安装版，并将补丁清单逆向恢复的原版哈希对上，以免归档和脚本来自不同构建。

更新本文的版本、大小、定位和验证边界。操作完成后提示重启正在运行的 agy；新会话可重新加载完整规则，旧会话已丢的内容不会自动恢复。不改 git index，不自动提交或发布。

## 10月23日：ARM64 1.4.6

原版 Low 真实请求的 executor 窗口仍为256000。新版重新定位后，Low/Medium/High 三档均正常回复 OK，executor 与 gen 两处实际上限均为983040；user_rules 各121354字节，逐字包含 AGENTS.md 全部120983字节。

已检查 getter 字段布局、补丁入口和最终配置出口、预算消费点，并扫描确认跳板无函数外原始直接分支引用。启动、补丁幂等、归档逐字节比对和逆向恢复原版哈希均通过。未跑超过256K长会话压力测试，未验证手动 compact。自动升级保持原样，重启正在运行的 agy 后生效。

## 10月26日：ARM64 1.4.7

与 x86 1.4.7 的记录交叉核对：GetMaxTokenLimit 从 +16 移至 +12，跳板改写 str w3,[x1,#12]；外层配置指针仍写 [x0,#16]，不可混淆。原版 Low 会话 0b8704cd-77bb-493a-8e9c-ed589bfb3b73 的 executor/gen 两处窗口均为256000。

修改后三档真实小请求均回复OK，两处窗口均为983040，完整注入113322字节 AGENTS.md（user_rules 113693字节）。验证记录见 verification.json。已检查启动、补丁幂等、跳板无函数外原始直接 B/BL 引用、归档逐字节一致和逆向恢复原版哈希。未跑超过256K长会话压力测试，未验证手动 compact；自动升级保持原样，重启 agy 后生效。

## 10月29日：ARM64 1.4.9

参照 x86 1.4.9 记录并重新核对 ARM getter，max_token_limit 仍为+12，外层 checkpoint 指针仍为+16。原版 Low 会话 0bb4d2c1-ad3f-493b-8a1a-5e8d6483ff27 的 executor/gen 两处窗口均为256000。

修改后三档均回复OK，两处窗口均为983040，user_rules 各116368字节，逐字包含 AGENTS.md 全部115997字节。启动、补丁幂等、跳板无函数外原始直接 B/BL 引用、归档逐字节比对、逆向恢复原版哈希均通过。未跑超过256K长会话压力测试，未验证手动 compact。自动升级保持原样，重启 agy 后生效。

## 10月30日：ARM64 1.4.11

重新定位 Go pclntab、三个 getter、配置出口和规则预算消费点；max_token_limit 仍为+12，外层 checkpoint 指针仍为+16。原版 Low 会话 1883785f-9d7d-4d2e-8217-603afe043a2e 的 executor/gen 两处窗口均为256000。

修改后三档均回复OK，两处窗口均为983040，user_rules 各116368字节，逐字包含 AGENTS.md 全部115997字节。启动、补丁幂等、跳板无函数外原始直接 B/BL 引用、归档逐字节比对、逆向恢复原版哈希均通过。未跑超过256K长会话压力测试，未验证手动 compact。自动升级保持原样，重启 agy 后生效。

## 11月2日：ARM64 1.4.12

参照 x86 1.4.12 记录，重新定位并核对 ARM getter、配置出口、checkpoint 函数和规则预算消费点；max_token_limit 仍为+12，外层指针仍为+16。原版 Low 会话 b3aff6d5-6d3b-43fd-908b-c7b9aad7767c 的 executor/gen 两处窗口均为256000。

修改后三档均回复OK，两处窗口均为983040，user_rules 各116368字节，逐字包含 AGENTS.md 全部115997字节。启动、补丁幂等、跳板无函数外原始直接 B/BL 引用、归档逐字节比对、逆向恢复原版哈希均通过。未跑超过256K长会话压力测试，未验证手动 compact。自动升级保持原样，重启 agy 后生效。

## 11月6日：ARM64 1.5.2

重新定位后确认配置出口寄存器已变化：x3 为外层配置，x0 为 checkpoint，x4 作跳板临时寄存器。跳板检查 [x3,#8] 中 planner 的 model+64，匹配1417..1419时写1000000到 [x0,#12]，重放 str x0,[x3,#16] 后返回。规则预算仍为两项四处消费/默认路径，一并修改。

修改后三档均回复OK，executor/gen 两处窗口均为983040，user_rules 各116368字节，逐字包含 AGENTS.md 全部115997字节。启动、补丁幂等、跳板无函数外原始直接 B/BL 引用、归档逐字节比对、逆向恢复原版哈希均通过。未跑超过256K长会话压力测试，未验证手动 compact。自动升级保持原样，重启 agy 后生效。

原版对照重试成功：会话 067e567d-31e4-4fab-a8d2-c7ce4e568aa3 回复OK，executor/gen窗口均为256000。

## 11月10日：ARM64 1.5.3 与禁用自动升级

重新核对 getter、配置出口及两层规则限制，寄存器与1.5.2一致（x3外层、x0 checkpoint、x4临时）。原版对照会话584044de-900e-4a9e-b5cd-ab3f68447918两处窗口均为256000。三档修改版小请求、完整规则及两处窗口的结果见verification.json；本版未跑超过256K长会话压力测试，未验证手动compact。

按用户要求，本机 ~/.bashrc 与 ~/.profile 已加入：

```bash
export AGY_CLI_DISABLE_AUTO_UPDATE=true
```

反汇编 updater.triggerUpdateShared 确认自动路径只认字面值 true（长度4），1不生效。新登录shell已核对为true；已有终端需执行上述export或重开终端再启动agy。此设置属于本机环境，不改变归档二进制的更新逻辑，换机器时也需设置。恢复脚本仍仅安装当前归档。

## 11月10日下午：ARM64 1.5.4

重新定位并核对字段/寄存器布局，与1.5.3一致。原版对照8284da3e-a478-4163-bd6a-bdd02b17215b两处窗口均256000。修改版三档验证见verification.json。未做超过256K长会话测试。当前shell的AGY_CLI_DISABLE_AUTO_UPDATE=true已确认，但此次升级触发来源未确定，不能据此归因于变量失效。

## 11月11日：ARM64 1.5.5，同时覆盖 Argon 与 Carbon

拉取x86最新适配后，发现本机已自动升级到1.5.5，因此重新定位ARM 1.5.5。跳板匹配Argon 1417..1419与Carbon 1427、1437、1438，匹配后先检查checkpoint非空，再设1000000。Carbon预留输出262144，所以实际输入窗口786432；Argon实际983040。

今后每次升级均须保留两组模型匹配，并验证两组各三档。不可假设Carbon编号连续，不可将Argon的983040用作Carbon预期值。验证Carbon时传 --expected-limit 786432。完整六档结果见verification.json。归档保持同名文件，一键恢复脚本自动读取新清单。未跑超过256K长会话测试。

### 11月13日：ARM64 1.5.8 六档补丁

按新版重新定位配置出口、checkpoint及规则预算消费点，已安装1.5.8补丁。Argon三档executor/gen均为983040，Carbon三档均为786432，六档均回复OK并完整加载123402字节AGENTS.md。保留Carbon的262144输出预留和ARM版关闭自动checkpoint的原有行为。归档、脚本、字节清单与验证记录已同步；启动、幂等、归档比对及逆向还原哈希检查通过。x86归档保持1.5.7。本版未跑超过256K长会话压力测试，重启agy后生效，已丢失历史不会自动恢复。

### 11月15日：ARM64 1.5.9 六档补丁

重新定位新版配置出口、checkpoint及规则预算消费点，已安装1.5.9补丁。Argon三档executor/gen均为983040，Carbon三档均为786432，六档均回复OK并完整加载123538字节AGENTS.md。保留Carbon的262144输出预留和ARM关闭自动checkpoint的行为。归档、脚本、清单、哈希和验证记录已同步；启动、幂等、直接分支引用检查、归档比对及逆向还原原版哈希通过。x86归档保持1.5.7，hook保持原样。本版未跑超过256K长会话压力测试，重启agy后生效。

### 11月18日：ARM64 1.5.11 六档补丁

已重新定位并安装补丁。Argon 三档实际窗口为 983040，Carbon 三档为 786432。六档小请求均回复 OK，完整加载 123538 字节 AGENTS.md。归档比对、幂等及逆向还原原版哈希检查通过。未做超过 256K 的长会话压力测试。

### 11月19日：ARM64 1.5.11 加入 Neon

Neon High、Medium、Low、XHigh 分别对应 1532、1533、1534、1535。四档实际请求窗口均从 512000 提高至 786432。原六档补丁可直接运行新版 ARM 补丁脚本升级，重启 agy 后生效。

### 11月19日：ARM64 1.5.12

已核对十档真实小请求。Neon 四档和 Carbon 三档均为 786432，Argon 三档均为 983040。executor 与 gen 记录一致，十档均完整加载项目规则。归档与安装版逐字节一致，逆向还原原版哈希通过。未跑超过 256K 的长会话测试。

### 11月23日：ARM64 1.5.15

设置原生 100% 压缩阈值，三个规则读取点提高到 1 MiB，两项规则预算各为 131072 tokens。十档小请求均完整加载项目规则，Argon 三档窗口为 983040，Carbon 三档和 Neon 四档为 786432。未做超过 256K 的长会话测试。

### 11月24日：ARM64 1.5.15 切模型窗口修复

ARM64 1.5.15 在最终配置出口覆写 Argon、Carbon、Neon 十档窗口预算为 1000000，并关闭自动 checkpoint。移除测试进程的 AGY_CLI_AUTO_COMPACT_OVERRIDE 后，十档请求窗口与规则全文均验证通过。另在独立会话 54f96469-dcb7-44c7-860e-094391dfa75b 从 Argon Low（983040）续聊切到 Carbon Low（786432）。未跑长会话压力测试。

### 11月28日：ARM64 1.5.18

重新定位最终配置出口、checkpoint 函数及两层规则限制。Argon 三档、Carbon 三档和 Neon 四档共十档真实短请求均回复 OK；executor/gen 窗口一致，Argon 为 983040，Carbon/Neon 为 786432。每档 user_rules 均逐字包含项目 AGENTS.md 全部 124311 字节。验证进程移除了 AGY_CLI_AUTO_COMPACT_OVERRIDE，沿用 ARM 关闭自动 checkpoint 的行为。

启动、幂等、跳板无函数外直接分支引用、归档逐字节比对及逆向还原原版哈希通过。原版备份在 ~/.local/bin/agy-1.5.18-original.bak。未做超过 256K 长会话压力测试；重启 agy 后生效。
