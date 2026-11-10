# Community image acceptance checklist

Use a spare TF card and an explicitly authorized test board. Preserve the working installation. The build does not connect to or modify the running Home Assistant host, upgrade its Core, migrate its backup, or change router settings.

- Confirm K2B V2.2 DDR3 and record build SHA / image hash. Verify image checksum and flash verification.
- Capture a full serial log from power-on. Confirm 2 GiB DDR3, no memory faults, Maxio driver, 1 Gbit/s full duplex, DHCP, route and 8123 access.
- On a clean installation without a NetworkManager cloned-MAC override, compare U-Boot ethaddr, USB Ethernet sequence, runtime DT local-mac-address and the kernel's initial Ethernet address. Reject USB development defaults and random addresses as the intended hardware identity. Never publish raw SID or machine secrets.
- Repeat warm reboots and actual power-off cold starts; verify boot IDs change while the LAN MAC stays stable. A cold boot is separate evidence from RTC power-loss retention.
- On the same board, test a second fresh TF card; the intended SID-based MAC should agree. On a second board, confirm a different address. One board cannot prove board-to-board uniqueness.
- With USB gadget present, confirm USB/LAN identity and numbering remain separate and both expected functions work.
- Confirm accurate UTC and successful NTP synchronization, normal connectivity `full`, host/supervisor online, and TLS. Test boot with no network, later link restoration, one failed NTP provider and DNS failure. Long outage recovery can take tens of minutes under default systemd polling; a 10-second connection retry is not a 10-second recovery guarantee.
- Test a clean overlay, byte-identical old NTP default, explicit custom NTP, opt-out, existing backup, and a restored user configuration. Old-default migration must retain its backup; custom content must survive.
- Back up and review NetworkManager configuration including internal conditional `.was/.set` overrides. A changed base URI can invalidate an old conditional override; do not assume all effective customizations survive just because no file is edited.
- Confirm user-defined MAC, connection UUID, DHCP client-id and static/reserved address policy are not rewritten. Existing custom MAC can hide a lower-level failure, so test the clean baseline separately.
- Verify the user's expected Core/HACS/configuration versions after any separately authorized restore. The image build does not promise to pin a restored application's version.
- Run a sustained workload, monitor link drops/memory/storage/thermal events, and record the actual duration before claiming long-term stability.
- Verify rollback by restoring the preserved original card. Do not test cross-build RAUC trust on the production installation.

Publish only measured results. An explicit PHY ID in DT selects the driver; it is not a fresh hardware ID register read. Missing receive clock remains an inference unless measured. Build success cannot establish these hardware outcomes.
