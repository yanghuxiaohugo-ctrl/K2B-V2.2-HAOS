# 给现场 Agent：仅替换 PHY ID 测试 DTB

这是 Linux 6.18.62 已交付镜像的单项验证包，不是完整刷卡镜像。只修改 PHY 节点 compatible，显式指定 Maxio ID 0x7b744411。其余设备树节点、属性与内存保留项通过自动比较，必须与已交付 DTB 完全一致；内核、U-Boot、DDR3 电压、PHY 地址/复位/延时均不改变。

## 文件选择

- 包根目录 `sun50i-h618-k2b.dtb`：新测试文件。
- `original/sun50i-h618-k2b.dtb`：上一轮交付 DTB，仅供对照/恢复；仍应另备份现场卡实际文件。
- `validation.json`：新旧 SHA256、唯一属性差异、编译提交。
- `SHA256SUMS.txt`：本包校验清单。

旧 DTB SHA256：4395f58bb250e7d98056c173a9be280bd7dc65bd9cd10dc505a5a49f0ec97dbd。
本包新 DTB 的 SHA256 以 validation.json 和 SHA256SUMS.txt 为准。

## 替换步骤

1. 保持串口日志可用，先保存当前启动日志。能进入系统时正常关机，随后切断板卡电源再拔 TF 卡。
2. 插读卡器，只读识别当前测试 TF 卡的型号、容量、磁盘号和启动分区盘符。不要沿用旧电脑的盘号，不要格式化 Windows 不认识的分区。
3. 校验包根目录的新 DTB 哈希，与清单一致。
4. 将启动分区根目录的原 `sun50i-h618-k2b.dtb` 复制到现场电脑的新建备份目录，记录 SHA256。若不是上述旧哈希，先停在这里核对卡和文件，不盲目覆盖。
5. 向用户展示已识别的目标 TF 卡、启动分区盘符和备份位置，取得对这张卡上此文件替换的确认。然后只覆盖启动分区根目录这一文件，不重刷整卡，不动 boot.scr、cmdline.txt、内核或其他分区。回读目标文件 SHA256，须等于本包新哈希。
6. 安全弹出，断电状态插回板卡；先开串口记录，再上电。网线使用已知正常网线和端口。

串口使用 115200/8N1/无流控，3.3V TTL；板卡 17(TX)→适配器 RX，19→GND，需要输入时 15(RX)←适配器 TX；VCC 不接。排针方向按实物确认。

## 观察与判断

重点记录从上电开始的全部输出，然后在 HAOS 主机 shell 查看：

```sh
uname -a
cat /sys/bus/mdio_bus/devices/stmmac-0:00/phy_id
readlink -f /sys/bus/mdio_bus/devices/stmmac-0:00/driver
tr '\0' '\n' < /proc/device-tree/soc/ethernet@5020000/mdio/ethernet-phy@0/compatible
dmesg | grep -iE 'maxio|mae0621|stmmac|dwmac|eth0|dma'
ip -br link
ip -br address
ip route
```

若 eth0 尚未打开，记录原状态后执行一次 `ip link set eth0 up`，等 10 秒，再查看 `dmesg | tail -n 200`、`cat /sys/class/net/eth0/carrier`、`ethtool eth0`。接口名不同则使用实际名称。

预期分阶段：

1. compatible 包含 ethernet-phy-id7b74.4411；Maxio 驱动绑定，出现 probe/config_init 相关打印。
2. 网卡能够拉起，原 DMA reset timeout 不再出现。
3. carrier=1 / Link Up，随后拿到 DHCP 地址。
4. 最后测试到网关的连通性和 IP:8123。

注意：新 sysfs phy_id 为 0x7b744411 是设备树声明的结果，不能作为硬件 ID 寄存器已修好的证据。MAE0621A READY 或 probe 打印也不单独代表网络验收成功，必须继续观察 Link、IP 和通信。

若 Maxio 已绑定仍报初始化错误，保存完整原文，不马上判定硬件损坏，也不追加方案 B、改 PHY 地址/延时或写寄存器。必要时按同样的备份、目标确认和哈希校验步骤恢复原 DTB。

回报：新 DTB 哈希、完整串口日志、实际绑定驱动、DMA 错误是否消失、carrier/速度、IP/路由/网关通信、8123 状态。实机验证成功后，再由构建端生成正式完整镜像。

本测试包不验证旧 6.12 卡，不覆盖旧故障现场；不操作生产 HA、R76S 或其他 NAS 目录。
