# F50 上的 Clash / Mihomo：分流、管理、升级和停用

## 本例选择

基础网络修好后，我让 Codex 继续配置 Clash。订阅从我电脑本地的文件读取，没有发给在线转换服务，也没有放进这个仓库。

装的是 **Mihomo / Clash Meta v1.19.32 ARM64**，不是把完整 OpenClash LuCI 插件塞进旧版系统。管理面板为本地托管的 MetaCubeXD。它作为独立应用运行，没有升级 Linux 内核、OpenWrt rootfs 或 boot_b。

原因很具体：本机主项目是 v2026.10.11；作者后来拆出的 `mu300-linux-vpn` 模块要求 v2026.10.16+。不能为了装代理忽略依赖，更不能整包升级时把刚修好的 SIM1 脚本覆盖掉。

**2026-10-11 再次检查官方 release，v1.19.32 仍是最新稳定版。** 没有把 alpha/开发构建当成“更新一下”。未来版本要重新检查。

## 当前功能

- 手机/电脑连接 F50 Wi-Fi 或 USB，客户端不需要再开 Clash。
- 国内域名和中国 IP 直连，其他流量进入 PROXY 策略组。
- PROXY 默认选择 AUTO；AUTO 对订阅节点做延迟探测。用户可以在面板手动指定节点。
- 订阅通过 Mihomo HTTP provider 每 24 小时刷新；本地缓存使重启不必先下载订阅才能启动。
- 配置和订阅凭据只保存在设备和用户本地的私密目录。
- 当前以 IPv4 代理为验收范围，没有声称完整 IPv6 代理。

## 安装与调试顺序

1. 先验证没有代理时蜂窝、Wi-Fi、USB 都正常，保存配置和脚本哈希。
2. 从 [MetaCubeX/mihomo](https://github.com/MetaCubeX/mihomo/releases/latest) 选择 `linux-arm64` 正式版，核对发布资产 SHA256；解压后再记录可执行文件 SHA256。
3. 读取订阅只导入节点，重新构建本机配置。不直接接受订阅里的管理接口、监听端口、TUN 和任意本地路径设置。
4. 下载规则和面板只用核实过的官方来源，并校验发布摘要或 Git blob。不得把订阅密钥传给第三方转换网站。
5. 把文件通过二进制 SSH 上传到暂存目录，读回 SHA256。设备内核放 `/usr/local/bin/mihomo`，配置 `/etc/mihomo/config.yaml`，目录 0700、配置 0600。
6. 先 `mihomo -t` 检查，再用 TUN 关闭的测试配置启动，通过仅回环地址的代理测试 Google、YouTube、国内站点。这一步不抢全网流量。
7. 测试成功后启用 TUN、DNS 转发和原生 procd 服务；备份所有改动并再次读回。最后做 USB 无客户端代理测试、手机关闭自身 VPN/移动数据测试、重启自启测试。

示例配置见 [mihomo-f50.example.yaml](../examples/mihomo-f50.example.yaml)。它没有可用订阅和管理密钥，不能原样放到路由器上运行。实际出口接口需按本机判断，不要照抄 sipa_eth8。

## 5.4 内核又踩了一个坑

开启 `auto-redirect: true` 后，Mihomo 返回：

```
Start TUN listening error: auto redirect: ... netlink receive: operation not supported
```

测试节点能用，并不代表透明代理已经建立。此时 TUN 网卡不存在、策略路由没出现。没有为此关闭防火墙，也没有重刷内核。

本例最终使用：

```yaml
tun:
  enable: true
  stack: gvisor
  device: mihomo
  auto-route: true
  auto-redirect: false
  strict-route: true
  mtu: 1400
  dns-hijack:
    - any:53
    - tcp://any:53
  route-exclude-address:
    - 192.168.77.0/24
```

也就是标准 TUN 策略路由，加一个仅覆盖 `mihomo` 网卡的防火墙区域，以及 `lan → f50_mihomo` 的转发。原有 WAN、防火墙和 SIM1 拨号修复保留，软件流量加速仍关闭。

DNS 由原来的 dnsmasq 提供 LAN 服务，转发到 Mihomo 的 `127.0.0.1:1053`。本例原 dnsmasq 没有自定义 server/noresolv，所以服务启用时设置转发，停止时恢复这两个原始选项。**其他设备有自定义 DNS 时不能照抄恢复逻辑，应保留其原配置。**

## 本例管理入口

MU300 原后台仍在 `http://192.168.77.1`。Mihomo 管理面板位于：

```
http://192.168.77.1:9090/ui/
```

控制接口是 `http://192.168.77.1:9090`，需要本机随机生成的 Secret；Secret 保存在设备主人的本地说明文件里。本仓库不给出默认密码。控制器只监听 LAN 地址，WAN 没有对应放行规则；HTTP/SOCKS 混合端口仅监听回环地址。

选择节点、查看连接和更新 provider 可以在面板操作。不要把 Secret 填到来历不明的在线面板。

## 启停

本机服务名为 `f50-mihomo`：

```sh
/etc/init.d/f50-mihomo stop       # 停止代理，恢复原 DNS 选项；不等于关闭下次自启
/etc/init.d/f50-mihomo start
/etc/init.d/f50-mihomo restart
/etc/init.d/f50-mihomo disable    # 取消开机自启
/etc/init.d/f50-mihomo enable
```

长期停用时先 `stop` 再 `disable`。确认 `ip rule` 和表 2022 的代理路由已清理、原 DNS 能用，不能只杀进程就认为恢复完成。

## 内核可以单独升级

这里说的“Mihomo 内核”是一个应用程序文件，不是 Linux 5.4 内核。升级它不需要写 boot 分区。

操作顺序：

1. 查询官方最新**稳定版**，与 `/usr/local/bin/mihomo -v` 比较。已经相同就无需重复替换。
2. 私密备份 `/etc/mihomo`、当前二进制、服务脚本、DNS 和防火墙设置；记录 SHA256。
3. 下载 ARM64 包，校验发布摘要，解压到暂存目录。不要直接覆盖正在运行的文件。
4. 将新二进制通过非 PTY 通道上传 `/tmp/` 并读回校验，例如本仓库的 `ssh-upload-verified.py`。本机 SFTP 未配置，普通现代 `scp` 可能失败；不能改用 PowerShell 文本重定向传二进制。
5. 用新二进制的 `-v` 和 `-t -d /etc/mihomo -f /etc/mihomo/config.yaml` 检查架构与兼容性。
6. 停服务，把旧内核保留在备份路径，用经过校验的新文件原子替换目标，保持 0755，再读回 SHA256并启动。
7. 验证 LAN 后台、国内直连、国外代理、Wi-Fi、USB 和重启。失败时停止服务，恢复旧内核与相应配置，再启动和复测。

订阅刷新、Mihomo 应用升级、MU300 面板升级、OpenWrt/内核升级要分开处理。不能为了升级一个代理内核去运行整机刷写脚本。

---

节点用的是我自己在 DediOne 洛杉矶那台小机器上搭的，同款套餐见 [aibuy.bid/vps/dedione](https://aibuy.bid/vps/dedione/)（返利链接），有特价款和常规款，端口和流量不一样，买之前看清楚。
