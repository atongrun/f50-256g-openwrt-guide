# 装好后的配置与使用

## 登录

本案例 OpenWrt 网关 `192.168.77.1`，MU300 面板位于 `/cgi-bin/luci/admin/home`，SSH 用户为 root。实际密码由本次安装产生，只交给设备主人；这个仓库没有默认通用密码。

Wi-Fi 名称和密码可以从本机原厂配置导入，也可以在 LuCI 修改。不要把另一台设备的热点配置一起打包进镜像。更改后确认手机确实使用新设置，并拿到同一 LAN 的 DHCP 地址。

## 两个系统怎么切

OpenWrt SSH 中：

```sh
mu300-next-boot android
reboot
```

Android 原厂后台在本案例为 `http://192.168.0.1`。返回已安装的 Linux，在电脑上执行：

```sh
adb -s <SERIAL> shell su -c mu300-linux
```

也可以使用作者 Magisk 切换模块的 Action 按钮。回到 OpenWrt 后如希望以后默认进它：

```sh
mu300-next-boot linux
mu300-next-boot status
```

这些是现有系统的切换，不需要重新刷 boot_b。保留失败回退；本例为连续五次没完成启动后回 Android。它不是检测互联网是否可用的机制：系统启动成功但蜂窝不上网，不一定触发回退。

## 日常检查

```sh
ubus call network.interface.wan status
ip -4 addr
ip route
ip rule
cat /tmp/dhcp.leases
fw4 check
```

查看实际蜂窝接口的 `statistics/rx_packets`、`tx_packets`，结合 DNS/TCP 测试。不要在未核对逻辑卡槽时把 sipa_eth0 当作唯一可能。

本案例软件 flow offloading 保持关闭。更换新版内核或 fw4 后，如要重新开启，先确认上游对应修复并测试 DHCP、后台、NAT 及重启；不要只为界面开关看起来完整而打开。

## 升级前

保存本机修改过的 `mobile-data`、AT owner 服务、netifd 协议、面板 AT 适配和 SIM 选择配置，以及 network/firewall。备份中可能有密码，只保存在本地。

确认新版本是否包含同等修复，再选择移植或升级。草稿 PR 的全部改动和其中一个本机验证过的修复不是一回事。升级系统、升级代理内核、刷新订阅是三件不同的事。
