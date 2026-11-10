# K2B V2.2 SWT6621S 无线假设测试镜像

此镜像只供备用 TF 卡实机测试，未验证 Wi-Fi / BLE 可用，也不自动发布 GitHub Release。当前运行中的 HA 和原可用卡继续保留。

## 来源和构建边界

- 假设：板载模块 VS6621S40，Seekwave SWT6621S，SDIO `1ffe:6621`。Armbian 上游 #11006 记录了同为 V2.2、2GB DDR3 的板型；本机芯片仍需读回确认。
- 固定 Novice-PG/swt6621s `1.0.3` 发布包，下载后强制校验包 SHA256。
- 驱动源码的全部 111 个文件、16 份实际固件，与 NAS 现成 K2B V2 参考镜像所带版本逐字节一致。参考镜像压缩文件 SHA256 为 `edaac50da3d1318c27e4b5d0be75113be4a4ef10d5e491a5918df86162f3337c`，内核版本为 6.18.60。本构建改为针对 HAOS 的 6.18.62 交叉编译，不复用旧内核的二进制模块。
- 按 1.0.3 发布说明保留 `KCFLAGS=-fpatchable-function-entry=0`，避免已知 arm64 外置模块 ftrace 加载崩溃。
- DDR3、Maxio 原六份硬件补丁、固定 U-Boot / ATF / HAOS-ACE / HAOS / Buildroot 版本不变。沿用独立 community 候选的配对 Ethernet alias 和时间/联网默认值。
- 仅增加 SDIO 时钟、PG18/PG19 复位和电源时序；不启用 eMMC，不改用户的 Wi-Fi 凭据、HA Core、连接 UUID 或 DHCP 策略。
- 三个模块显式按顺序加载。无线服务失败不重启或要求有线网络；没有自动反复卸载/重载 SDIO 驱动的 watchdog。
- 驱动保留原 GPL 许可证与署名。固件为厂商二进制；公开社区发行前仍需核对其分发说明。

## 测试前

备份现有 HA 配置并保留当前可用 TF 卡。校验新镜像 SHA256，用备用卡刷写和校验。实际切换卡与断电测试会使 HA 暂停，需用户选择维护时间；不要覆盖当前系统卡，也不要把新构建直接当作 OTA 包刷入。

## 现场验收

1. 从上电起采集完整 TTL 日志，先确认 DDR3 2GiB、Maxio、千兆有线 DHCP 和 8123 不回退。
2. 读取 `/sys/bus/sdio/devices/*/vendor`、`device`、`modalias`，验证实际无线芯片；不匹配时停止套用本假设，不强制绑定错误 ID。
3. 检查 `systemctl status k2b-wireless-test.service`、`lsmod` 与 `journalctl -b -u k2b-wireless-test.service`。需出现 `skw_sdio_lite`、`swt6621s_wifi`、`skwbt`；服务成功不等于硬件功能通过。
4. Wi-Fi 分别验证 2.4GHz / 5GHz 的扫描、关联、DHCP、持续传输、有线共存和暖/冷启动恢复。凭据只在测试设备本地配置，不写入仓库或共用镜像。设置实际所在地区，不能绕过当地射频限制。
5. 蓝牙分别检查 HCI 正常、LE 扫描能持续接收已知 BLE 设备广播、HA 能发现兼容设备及需要时连接。普通蓝牙发现、hci0 存在或 BR/EDR 成功不能代替 BLE 验收。
6. 记录 Wi-Fi 与蓝牙地址在暖/冷启动中的变化；多板验收检查地址是否重复。厂商 NV 可能携带默认身份，不把一次运行当作多板唯一性证明，不将现场地址硬编码到公共镜像。
7. 检查 RTC/UTC/NTP、联网检测、USB、HA 状态和持续负载。分别记录测试时长与未测项目。
8. 失败时留存日志，换回原可用卡恢复。不要在不可移除 SDIO 上反复 `modprobe -r` 试图恢复。

参考来源：

- https://github.com/armbian/build/pull/11006
- https://github.com/Novice-PG/swt6621s/releases/tag/1.0.3
- https://www.home-assistant.io/integrations/bluetooth/
