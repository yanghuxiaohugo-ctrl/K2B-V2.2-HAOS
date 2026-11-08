#!/usr/bin/env python3
"""Apply the reviewed 6.18 migration to the pinned haos-ace checkout."""
from pathlib import Path
import hashlib,json,re,shutil

ASSETS=Path(__file__).resolve().parent
ROOT=Path.cwd()
OVERLAY=ROOT/'haos-overlay/buildroot-external'
BOARD=OVERLAY/'board/hardkernel/kickpi-k2b'
MANIFEST=json.loads((ASSETS/'patch-manifest.json').read_text())
EXPECTED_UBOOT='59b8087d15e07338b363d2851bb071e155dfc45dc0c98252d8403a0d80ad8b3b'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
uboot_before=(BOARD/'uboot.config').read_bytes()
assert hashlib.sha256((BOARD/'uboot.config').read_text().encode()).hexdigest()==EXPECTED_UBOOT,'Approved DDR3 U-Boot configuration changed'
for entry in MANIFEST['patches']:
    assert sha(ASSETS/'patches'/entry['patch'])==entry['sha256'],entry['patch']

patchdir=BOARD/'patches/linux'
expected_old={'001-h618-wifi.patch','002-h618-usb.patch','003-h618-eth.patch','004-h618-bluetooth.patch','005-k2b-v2-eth-dts.patch','006-add-maxio-mae0621-phy-driver.patch'}
expected_new={entry['patch'] for entry in MANIFEST['patches']}
existing={p.name for p in patchdir.glob('*.patch')}
assert existing in (expected_old,expected_new),existing
for p in patchdir.glob('*.patch'):p.unlink()
for entry in MANIFEST['patches']:shutil.copyfile(ASSETS/'patches'/entry['patch'],patchdir/entry['patch'])

# Retain the HAOS IPv6 reachability behavior, rebased with exact 6.18 context.
globaldir=OVERLAY/'patches/linux';globaldir.mkdir(parents=True,exist_ok=True)
for p in (ASSETS/'global-patches/linux').glob('*.patch'):shutil.copyfile(p,globaldir/p.name)

defconfig=OVERLAY/'configs/k2b_h618_defconfig'
source=defconfig.read_text()
assert source.count('BR2_LINUX_KERNEL_CUSTOM_VERSION_VALUE=')==1
source=re.sub(r'^BR2_LINUX_KERNEL_CUSTOM_VERSION_VALUE=.*$',f'BR2_LINUX_KERNEL_CUSTOM_VERSION_VALUE="{MANIFEST["kernel_version"]}"',source,flags=re.M)
# This pinned Buildroot defines CUSTOM_6_12 as "6.12.x or later" and uses loose header checking.
assert 'BR2_PACKAGE_HOST_LINUX_HEADERS_CUSTOM_6_12=y' in source
# The V1-only AIC8800 and external USB Wi-Fi drivers are outside the wired V2 test scope.
for option in ('BR2_PACKAGE_RTL8812AU_AIRCRACK_NG','BR2_PACKAGE_RTL8821CU'):
    source=re.sub(rf'^{option}=y$',f'# {option} is not set',source,flags=re.M)
defconfig.write_text(source,encoding='utf-8')

fragment=BOARD/'kernel.config'
extra='''
# K2B V2.2 Linux 6.18 migration: wired boot and observable startup.
CONFIG_MAXIO_PHY=y
CONFIG_DWMAC_SUN8I=y
CONFIG_STMMAC_ETH=y
CONFIG_STMMAC_PLATFORM=y
CONFIG_PHY_SUN4I_USB=y
CONFIG_USB_EHCI_HCD=y
CONFIG_USB_EHCI_HCD_PLATFORM=y
CONFIG_USB_OHCI_HCD=y
CONFIG_USB_OHCI_HCD_PLATFORM=y
CONFIG_MFD_AXP20X_I2C=y
CONFIG_REGULATOR_AXP20X=y
CONFIG_SERIAL_8250_DW=y
CONFIG_SERIAL_8250_CONSOLE=y
CONFIG_GPIO_CDEV=y
CONFIG_LEDS_GPIO=y
CONFIG_LEDS_TRIGGER_HEARTBEAT=y
CONFIG_MAGIC_SYSRQ=y
CONFIG_IKCONFIG=y
CONFIG_IKCONFIG_PROC=y
CONFIG_ZRAM_BACKEND_LZ4=y
CONFIG_ZRAM_DEF_COMP_LZ4=y
'''
if extra not in fragment.read_text():fragment.write_text(fragment.read_text()+extra,encoding='utf-8')
cmdline=BOARD/'cmdline.txt'
args=cmdline.read_text().strip().split()
for arg in ('initcall_debug','ignore_loglevel','loglevel=7'):
    if arg not in args:args.append(arg)
cmdline.write_text(' '.join(args)+'\n',encoding='utf-8')

assert (BOARD/'uboot.config').read_bytes()==uboot_before
assert '<1500000>' in (patchdir/'001-k2b-v22-board-support.patch').read_text()
print('Migration: Linux',MANIFEST['kernel_version'])
print('Migration: DDR3 U-Boot unchanged:',EXPECTED_UBOOT)
print('Migration: Linux DCDC3 constraints fixed at 1500000uV')
print('Migration: six exact-context board patches plus rebased HAOS IPv6 patch')
print('Migration: V1 wireless support omitted; wired USB/Ethernet boot retained')
print('customize: all sanity checks passed')
