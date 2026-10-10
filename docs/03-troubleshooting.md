# 按现象排查，不按感觉重刷

| 现象 | 本例证据 | 处理和停止条件 |
|---|---|---|
| 电脑看到 F50，ADB 空 | 设备端 USB 调试没开启 | 登录原厂 usb_port 页面；只安装核实来源的驱动 |
| `su` 存在，Root 不可用 | 配套 Magisk 运行文件缺失 | 核对匹配版本，补官方运行环境，实际验证 UID 0 |
| 256GB 但没有安装区 | GPT 的 userdata 接近磁盘末尾 | 优先 SD；没有 SD 时经确认缩数据区，不能借用未验证地址 |
| 分区已变小，文件系统仍大 | F2FS block_count 仍是旧值 | 不装 Linux；经确认让 Recovery 按新边界重建，再检查 |
| Wi-Fi 可见但无法拿地址/后台打不开 | fw4 flowtable 报 EBUSY，实际规则缺 LAN | 关闭软件 flow offloading、重载并核对；保持防火墙开启 |
| Linux 报未插卡，Android 能用 | Android 逻辑 slot 1、nr4、sipa_eth8 | 不按外插/内置标签猜，核对实际映射并统一所有调用者 |
| 拨号 CONNECT、WAN 有 IP、RX=0 | SIM1 适配后仍无 DNS/TCP 回包 | 先查 IPA、路由、防火墙和地址一致性；符合证据再看 SPSWDATA |
| boot_b 整体哈希启动后变化 | 项目把运行日志写在镜像保留区 | 按构建元数据核对不变区，不盲目重刷 |

## 5.4 的 fw4 问题

先备份 `/etc/config/firewall` 并记录 SHA256。只有出现相同证据才做：

```sh
uci set firewall.@defaults[0].flow_offloading='0'
uci commit firewall
/etc/init.d/firewall reload
fw4 check
nft list ruleset
```

检查 br-lan 输入放行、WAN 转发和 masquerade 是否真实存在。不要用 `service firewall stop` 作为最终修复。上游新版有进一步处理，见 #67、#69、#98；旧版的临时处理与新版修复不能混称。

## 第二逻辑卡槽有 IP 却没回包

按顺序留下证据：

1. Android 能否用同一卡联网？其逻辑 slot、接口和 AT 通道分别是什么？本例为 1 / sipa_eth8 / nr4。
2. Linux 所有相关组件是否指向同一卡？拨号、IPA 等待、面板、teardown 不能各用各的编号。
3. `CGATT`、注册、PDP 地址是否有效？设备接口地址是否等于基带当前地址？
4. `sipa_dele` 是否在正确时机加载，SIPC 握手是否存在？该模块可能是 permanent，不应反复卸载/加载。
5. 检查 `ip rule`、所有相关路由表、VPN kill switch；退出 VPN 不一定移除遗留规则。
6. 用 DNS/TCP/TLS 而不只是 ping 验证。部分运营商不响应 ICMP。
7. 前面都对，仍是 CONNECT + RX=0，再审阅 PR #72 和本机原厂 RIL 的 `SPSWDATA` 使用路径。

### 本例验证有效的最小步骤

这是**症状及映射已经确认后**的步骤，不是任意 F50 上的通用探测命令。必须有正在运行的 nr4 owner，不能让 AT 客户端静默回退到 nr1 或直接反复开关 TTY：

```sh
test -p /run/mu300-at4/cmd || exit 1
cat /sys/class/net/sipa_eth8/statistics/rx_packets
/opt/mu300/bin/mobile-data radio-locked /usr/bin/env \
  MU300_AT_DIR=/run/mu300-at4 /opt/mu300/bin/mu300-at -t 8 'AT+SPSWDATA'
```

检查结果是独立的一行 `OK`，再做运营商 DNS 和 USB HTTPS；不要把 AT 客户端返回 0 当作成功。很多 ERROR 也会导致客户端正常退出。

本例从 RX=0 立即恢复 DNS 回答，因此才把下面逻辑并入已有、已经校验的 SIM1 拨号路径：

```sh
# 放在 CGDATA 明确 CONNECT 之后，仅对已验证的逻辑 slot 1 生效。
if [ "$SIM_SLOT" = 1 ]; then
    at 'AT+SPSWDATA' 8 | grep -x OK >/dev/null || return 1
fi
```

还应在 SIM1 的 CGDATA 未返回 CONNECT 时直接失败，而不是仍向 netifd 报告已连接。必须备份脚本、检查语法、读回 SHA256，再做重启和冷启动验证。本案例没有替换整个草稿 SIM 控制器，没有为了修下行去写 NV 或重新刷 TrustOS。

`AT+SPSWITCHDATACARD=1,1` 在本机返回 CME ERROR 4，已停止；不要把它和不带参数的 `AT+SPSWDATA` 混为一谈。`SMMSWAP=0` 也不是可以按逻辑卡槽号随意改成 1 的设置。

## APN 名称不同不一定是错

原厂 Android 请求 cmnet/IPV4V6，但活动 bearer 返回 cmiot5g，仍然正常上网。社区 PR #72 也记录了这个行为。判断是否错误要看原厂对照、注册和真实回包，不要只为了让两串名称一样就持续改 APN。
