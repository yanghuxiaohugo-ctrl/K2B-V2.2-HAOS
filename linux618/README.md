# KICKPI K2B V2.2: Linux 6.18 migration

This is an experimental HAOS 16.3 kernel migration, not a claim of verified hardware boot.

## Fixed sources

- haos-ace: `1fcb5e87e86cf22015e46ffc53902fe83c5ed8d1`
- official HAOS submodule: `bd5ea3763f7cb7e47c280f72b837e12b6578bd8a`
- U-Boot: `v2025.01`, approved 48-line DDR3 board config unchanged
- Linux: `6.18.62`, kernel.org tar SHA256 `490a7aedf1b355c565d3a6c05333ccccb5da82064eca46b590448a7099d7d651`
- selected Armbian patch sources: `8ddeef322b4706b5be19d0fb7869f107c117666d`, `patch/kernel/archive/sunxi-6.18`

## Important voltage finding

Inspection of the actual DTB inside the previously delivered 6.12.35 image showed both Linux DCDC3 constraints at **1100000 uV**, while its U-Boot config set DDR3 VDD to **1500 mV**. The old boot log stops around AXP313a/OHCI initialization. This is a concrete DT inconsistency and a plausible contributor to the hang; the exact hardware failure remains unproven. The new DTB sets both DCDC3 constraints to **1500000 uV**. Do not conclude from the last OHCI message alone that a USB driver defect was proven.

## Patch mapping

The old board's 001-004 files combined V1-only wireless drivers and board descriptions. They are replaced by reviewed V2 wired support. The wrong AIC8800 driver and its Bluetooth child are not carried forward. SDIO and unfitted eMMC are dormant in this wired diagnostic board description. External RTL8812AU/RTL8821CU packages are disabled; in-tree USB networking remains available.

1. Board support newly generated against vanilla 6.18.62. Preserves TF/console/PMIC/USB1 and fixes the Linux DDR3 supply. The DTB filename stays `sun50i-h618-k2b.dtb` so the existing U-Boot script can load it.
2. Armbian's shared USB PHY reset change, regenerated against the exact source.
3. Armbian's sun8i EMAC reset-at-open change, regenerated against exact source.
4. Armbian's Maxio-specific initialization hooks in stmmac open/resume. In 6.18 the hardware setup is before phylink_start, so the old no-hook 6.12 assumption is not used.
5. Preserves V2 PHY address 0, active-low PI6 reset (20000/100000 us), RGMII MAC TX/RX delay 700/2000 ps, and releases PI16 for the heartbeat LED.
6. Armbian's reviewed Maxio PHY driver including the RGMII delay-mode correction; plain rgmii retains strapped PHY delays.

The HAOS global IPv6 reachability patch is also regenerated for 6.18.62. All seven final patches were locally applied with GNU patch `-F0` and no offsets or fuzz. The pinned Buildroot's header selector says `6.12.x or later`; its existing loose header-version check supports 6.18 without changing Buildroot or inventing a new Kconfig option.

## Workflow modes

Run `.github/workflows/build-linux-6.18.yml` with:

- `validate`: verify the Linux source hash, exact patch application, effective merged config, compile the board DTB and changed networking/USB driver objects, then read the actual DTB voltage and Ethernet delay properties. This is compile validation, not hardware startup validation.
- `full`: repeat validation, then run the existing Debian/archive, container-image and full Buildroot build recipe. The final Buildroot config and DTB are checked again before publishing images.

The previous `build-one-shot.yml` is preserved. Both the U-Boot DDR3 config hash and new patch hashes are checked by preparation. Container image versions and the previous ARM64/gzip-OCI workaround are retained. Extra initcall logging is enabled for the next hardware test.

Use a separate test TF card after identifying it and obtaining explicit user confirmation; retain the current 6.12 failure card and all original logs. Test DRAM capacity, progress beyond the former last OHCI line, Ethernet link/DHCP and finally port 8123. Do not operate the user's router or production Home Assistant.

## Source references

- https://www.kernel.org/releases.json
- https://github.com/armbian/build/tree/8ddeef322b4706b5be19d0fb7869f107c117666d/patch/kernel/archive/sunxi-6.18
- https://github.com/home-assistant/buildroot/blob/02f1553a34c2b8f6e432fe4300bfe529897d5f3c/package/linux-headers/Config.in.host
