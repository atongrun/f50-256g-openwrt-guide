# 我让 Codex 给中兴 F50 256GB 装 OpenWrt：过程、踩坑和可复用步骤

这是一台 F50 / MU300 256GB 实机的安装记录和 agent 操作手册。2026 年 10 月 7 日开始，10 月 10 日完成手机 Wi-Fi、USB、蜂窝网络和断电重启验证。

核心系统来自 [dikeckaan/mu300-linux](https://github.com/dikeckaan/mu300-linux)。这个仓库补充的是 **256GB 实机怎么检查、怎么避免照搬存储布局，以及出现问题后按什么证据排查**。这里不提供原厂固件、解锁镜像、设备备份、IMEI/NV、密码或代理订阅。

## 从哪里看

1. [第一人称安装实录](docs/01-installation-story.md)：我是怎么让 Codex 动手的，以及为什么“刷好了”之后又折腾了两天。
2. [给人和 agent 的操作手册](docs/02-installation-runbook.md)：检查、备份、Root、存储、安装、校验、验收。
3. [故障对照表](docs/03-troubleshooting.md)：ADB、Root、F2FS、DHCP、防火墙、SIM1 有地址没回包。
4. [日常配置与系统切换](docs/04-configuration.md)。
5. [备份与恢复边界](docs/05-recovery.md)。
6. [Clash / Mihomo 配置](docs/06-clash.md)。
7. **自动化工具必须先读 [AGENTS.md](AGENTS.md)**，再执行只读预检。不要从文章里提取几条写入命令就开始刷。

## 这台机器验证过什么

| 项目 | 实测结果 |
|---|---|
| 设备 | ZTE F50 / MU300，`ums9620_2h10_feimao`，Unisoc T760 / UMS9620 |
| 存储 | 256GB 标称，实际 251305918464 字节；没有 SD 卡 |
| 原系统 | Android 13，F50SPV1.0.0B06，A 槽 |
| 安装后的 Android | 作者工具包配套 B09，Magisk 28103，A 槽保留 |
| OpenWrt | 项目 v2026.10.11，OpenWrt 25.12.5，MU300 面板，厂商 5.4.254 内核 |
| Linux 存储 | 经单独确认缩小 userdata 后得到约 4GiB 空间；没有把 256GB 全盘复制出来 |
| 蜂窝路径 | 本机 Android 实际使用逻辑 slot 1、nr4、sipa_eth8；不是按“物理卡/内置卡”标签猜的 |
| 关键修复 | 关闭出错的软件流量加速；SIM1 用户态适配；拨号后执行原厂 `AT+SPSWDATA` |
| 联网验收 | 手机关闭移动数据后 Wi-Fi 上网；电脑绑定 F50 USB 接口完成 DNS、TLS、HTTP 200 |
| 持久性 | 普通重启和拔电重启后自动联网，约 51 秒完成拨号；后台和 DHCP 正常 |
| 系统切换 | Android 与 OpenWrt 实际往返过；保留失败回退 |

**实测样本只有这一台。** “F50 256GB”不能代替型号、GPT、固件和逻辑卡槽检查。本仓库不是跨设备免确认的一键刷机包。预检脚本只收集信息，GPT 工具只验证离线备份，均不写设备分区。

## 最新进展怎么判断

2026-10-10 检索时，上游最新正式包已到 v2026.10.16，但我们没有为了追版本覆盖已验证的系统。解决本机联网的是 [PR #72](https://github.com/dikeckaan/mu300-linux/pull/72) 的最小数据路由修复；审阅提交为 `250d292479673586ca18289a6f2c97d9b8f8fa1d`。当时 PR 仍是草稿。后续使用请重新核对它的合并状态、实现和设备测试范围。

更新可能覆盖本机适配。先备份差异并查看上游是否已包含对应修复，再更新。不要通过“锁死 Linux”取消 Android 回退来掩盖启动问题。

## 许可证与来源

本站原创文档和辅助检查脚本采用 MIT 许可证。mu300-linux、工具包、内核、Magisk、Mihomo 保留各自许可证。这个仓库没有重新打包它们的固件或二进制文件，也不是中兴官方项目。具体来源见 [SOURCES.md](SOURCES.md)。
