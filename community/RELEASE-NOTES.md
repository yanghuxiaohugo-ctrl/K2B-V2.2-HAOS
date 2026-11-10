# KICKPI K2B V2.2 DDR3 社区测试版

这是非官方 HAOS-ACE 板卡适配测试镜像，适用于 KICKPI K2B V2.2 DDR3、TF 卡启动、有线网口。不要据此推定其他内存版本或板卡修订版兼容。

## 本版内容

- 保留已实机验证的 DDR3-1333 / 648MHz / DCDC3 1.5V 配置和 Maxio MAE0621 PHY 适配。
- Linux 6.18.62、U-Boot 2025.01、ATF v2.11；保留固定的 HAOS-ACE 与 HAOS 源码版本。
- 增加配对的 U-Boot 控制树 / Linux ethernet0 别名，沿用 U-Boot 每板 SID 派生 MAC 的路径。镜像不硬编码任何现场设备 MAC。
- 默认备用校时源改为阿里、腾讯和 Cloudflare；只有字节完全一致的旧默认校时文件会在启动前迁移，并保留备份；自定义配置保留。
- NetworkManager 默认联网检测使用 Home Assistant 官方直接响应端点，保留联网检测与 TLS 验证。

## 验证边界

旧版 PHY-ID 修复已经在一台 V2.2 DDR3 上验证驱动绑定、千兆全双工、DHCP 和 Home Assistant 8123 页面可访问。那些结果不等于本次新镜像已经通过实机测试。

本镜像只完成构建、配置、设备树及本地隔离测试。新 MAC 路径、断电冷启动、两块板地址唯一性、长时间断网恢复、USB gadget 回归与持续运行均待实机验证。Wi-Fi、蓝牙、eMMC、通用 OTA 和 RTC 掉电保持不在已验证承诺中。

## 使用

1. 下载 `.img.xz`、`SHA256SUMS.txt` 并校验镜像哈希。
2. 备份现有可用卡和 Home Assistant 配置，使用备用 TF 卡。用 Etcher 写入并完成写后校验；不要覆盖生产系统卡。
3. 插网线上电，观察串口日志和路由器 DHCP。首次启动需等待系统完成初始化。
4. 按仓库验收清单验证冷启动、MAC、联网检测和校时。报告问题时提供构建编号、板型和脱敏日志。

公开附件只提供全新刷写镜像。每次构建生成的开发签名不同，不能承诺跨构建 `.raucb` 互相接受，也不要将本版当作官方 HAOS 升级渠道。

已有用户明确设置的 MAC、连接配置和 DHCP client-id 不会被本版脚本主动重写；已有 NetworkManager 内部覆盖在基础 URI 改变时可能失效，升级前请对照验收说明备份核对。

## 来源与致谢

基于 LanSilence/haos-ace、Home Assistant OS、Buildroot、U-Boot、Linux 和 Armbian；Maxio 驱动保留原作者 Zhao Yang 及上游署名。所有组件保留各自许可证。本仓库是社区适配项目，不代表这些项目的官方支持或合并承诺。

准确的源码提交、构建地址见 `BUILD-INFO.json`，构建检查见 `VALIDATION.json`，源码与许可证材料见 `SOURCE-README.md`。
