# 来源与版本

- 主项目：[dikeckaan/mu300-linux](https://github.com/dikeckaan/mu300-linux)。本机安装包 v2026.10.11；初次审阅 main 为 `aff105fa3ed9f4b6add2e8d91ef1cf2d63cee92b`。
- 固件/Root 工具：[dikeckaan/zte-f50-toolkit](https://github.com/dikeckaan/zte-f50-toolkit)。只按其兼容性说明和本机核对结果使用。
- Magisk：[topjohnwu/Magisk](https://github.com/topjohnwu/Magisk)。本案例配套版本 28103；不能把这个版本机械用于其他补丁镜像。
- [FINDINGS](https://github.com/dikeckaan/mu300-linux/blob/main/docs/FINDINGS.md)：IPA、SIPC、启动槽位及历史问题。阅读时注意章节的 superseded 状态。
- [Issue #67](https://github.com/dikeckaan/mu300-linux/issues/67)、[PR #69](https://github.com/dikeckaan/mu300-linux/pull/69)、[PR #98](https://github.com/dikeckaan/mu300-linux/pull/98)：5.4 / fw4 flowtable 问题及后续修复。
- [PR #72](https://github.com/dikeckaan/mu300-linux/pull/72)：F50 SIM 选择和 SPSWDATA；本机审阅 `250d292479673586ca18289a6f2c97d9b8f8fa1d`，只移植已验证的最小路径。
- [PR #73](https://github.com/dikeckaan/mu300-linux/pull/73)：U30 Air 双卡；不直接把其厂商初始化序列用在 F50。
- [MetaCubeX/mihomo](https://github.com/MetaCubeX/mihomo)、[官方 TUN 文档](https://wiki.metacubex.one/config/inbound/tun/)、[官方 DNS 文档](https://wiki.metacubex.one/config/dns/)。
- [mu300-linux-vpn](https://github.com/dikeckaan/mu300-linux-vpn)：新独立模块要求主项目 v2026.10.16+，不能忽略依赖直接装到本案例 v2026.10.11。

本仓库的事实截止于 2026-10-10 的本机测试。版本、PR 状态和作者推荐会变化，执行前重新检查。没有把其他作者的固件或原厂二进制重新发布到这里。
