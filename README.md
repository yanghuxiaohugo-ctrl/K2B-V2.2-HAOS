# KICKPI K2B V2.2 DDR3 / HAOS-ACE community test build

为 KICKPI K2B V2.2 DDR3、TF 卡启动、有线网口准备的非官方测试适配。请从 Releases 下载明确标记为 prerelease 的镜像，并先阅读发布说明与校验值。其他板型、Wi-Fi、蓝牙、eMMC 和官方 OTA 未验证。

基础适配固定 Linux 6.18.62、U-Boot 2025.01、ATF v2.11、HAOS-ACE `1fcb5e87e86cf22015e46ffc53902fe83c5ed8d1`。DDR3 与 Maxio PHY 的原始六份补丁保留在 `linux618/`；新社区候选、校时/联网默认值和构建检查位于 `community/`，使用独立工作流，不改变原有工作流的构建资产。

旧 PHY-ID 单项 DTB 在一块板上通过千兆、DHCP、8123 实测。新社区镜像仍待冷启动、多板唯一 MAC、断网恢复与长期运行测试，不能把旧镜像的实测结果视作本镜像的验收。

## 构建和下载

- Actions：`K2B V2.2 community test build and prerelease`；`validate` 为短验证，`full` 为完整构建与测试版发布。
- `.img.xz` 用于备用 TF 卡全新刷写，先核对 SHA256，再完成 Etcher 写后校验。
- 不发布通用 OTA 升级承诺；现有可用卡和配置先备份。
- 每份发布包含构建信息、检查结果、有效源码快照及 Buildroot source/license collection。

## 实机验收

详见 `community/HARDWARE-ACCEPTANCE.md`。新 MAC 候选需要 U-Boot 和 Linux 两侧配对；不要仅替换 Linux DTB 后宣称稳定 MAC 已修复。公开报告需移除设备 MAC、完整 SID、SSH 密钥和个人配置。

## 致谢与贡献

基础项目：[LanSilence/haos-ace](https://github.com/LanSilence/haos-ace)、[Home Assistant OS](https://github.com/home-assistant/operating-system)、[Buildroot](https://buildroot.org/)、[U-Boot](https://source.denx.de/u-boot/u-boot)、[Linux](https://kernel.org/)、[Armbian](https://github.com/armbian/build)。保留原作者和各组件许可证。

欢迎同板型测试与脱敏反馈。先收敛实机证据，再将 DDR3、PHY、MAC 和通用配置改进拆开向相应上游讨论；此仓库不代表上游已接受这些改动。
