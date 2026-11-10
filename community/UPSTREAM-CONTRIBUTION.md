# Upstream contribution outline — not submitted

First destination: LanSilence/haos-ace, after community testing. Keep the published community image separate from any upstream support promise.

Proposed subject: `Add KICKPI K2B V2.2 DDR3 wired boot support`

The existing K2B configuration targets a different memory/PHY arrangement. On V2.2 DDR3, retain DDR3-1333 timing at 648 MHz with the AXP313 DCDC3 rail at 1.5 V in both bootloader configuration and Linux constraints. Use the V2 PHY address/reset/RGMII settings and explicit Maxio binding. Preserve the original authors of the imported Armbian/vendor patches and document every local adaptation.

Evidence already available from one V2.2 DDR3 board: a PHY-compatible-only DTB change selected the Maxio driver, removed the observed DMA reset failure, established 1 Gbit/s full duplex, obtained DHCP and served Home Assistant on port 8123. The DT-declared PHY ID is not proof of a new hardware-register read; an absent receive clock is an inference unless separately measured.

Keep the following review units separate:

1. DDR3 bootloader configuration and board-specific regulator constraints.
2. V2 Ethernet DTS and the Maxio driver/initialization changes, with minimal before/after evidence.
3. Paired U-Boot/Linux Ethernet aliases for SID-based MAC propagation, only after actual boot logs establish the intended path and USB numbering. Currently a build-checked candidate; cold boot and two-board uniqueness remain unverified.
4. Host time/connectivity defaults, with old-overlay migration behavior and NetworkManager conditional override caveats. These are not board electrical fixes and deserve a separate discussion.
5. Linux 6.18 and external-module API compatibility, independently from the board-specific fixes.

Before opening a PR, compare against the then-current upstream base, read its contribution requirements, attach sanitized test results, and identify any retained out-of-tree workaround. Linux and U-Boot submissions should be narrowed further and follow each project's own contribution process. No upstream issue, comment, branch or PR has been created by this preparation.
