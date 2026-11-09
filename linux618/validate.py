#!/usr/bin/env python3
"""Validate hashes, patches, config, DTB and changed driver objects on Linux."""
from pathlib import Path
from urllib.request import urlopen
import hashlib,json,os,subprocess,tarfile,struct,shutil

ASSETS=Path(__file__).resolve().parent
SOURCE=Path.cwd()
OS=SOURCE/'operating-system'
EXTERNAL=OS/'buildroot-external'
BOARD=EXTERNAL/'board/hardkernel/kickpi-k2b'
manifest=json.loads((ASSETS/'patch-manifest.json').read_text())
version=manifest['kernel_version']
CACHE=Path(os.environ.get('K2B_KERNEL_CACHE',str(Path.home()/'hassos-cache/dl/linux')))
CACHE.mkdir(parents=True,exist_ok=True)
archive=CACHE/f'linux-{version}.tar.xz'
if not archive.exists():
    with urlopen(f'https://cdn.kernel.org/pub/linux/kernel/v6.x/linux-{version}.tar.xz',timeout=90) as remote,archive.open('wb') as target:shutil.copyfileobj(remote,target)
with archive.open('rb') as f:actual=hashlib.file_digest(f,'sha256').hexdigest()
assert actual==manifest['kernel_sha256'],actual
print('Kernel source SHA256 verified:',actual,flush=True)
CHECK=Path(os.environ['RUNNER_TEMP'])/'k2b-kernel-check'
CHECK.mkdir(exist_ok=True)
with tarfile.open(archive) as tar:tar.extractall(CHECK,filter='data')
KERNEL=CHECK/f'linux-{version}'
def run(args,**kwargs):
    print('+',' '.join(map(str,args)),flush=True)
    subprocess.run(args,check=True,**kwargs)
for directory in (EXTERNAL/'patches/linux',BOARD/'patches/linux'):
    for patch in sorted(directory.glob('*.patch')):
        run(['patch','-F0','-g0','-p1','--no-backup-if-mismatch','-t','-N','-i',str(patch)],cwd=KERNEL)

config=EXTERNAL/'kernel/v6.12.y'
fragments=[config/'kernel-k2b-h618.config',config/'hassos.config',config/'docker.config',config/'device-support.config',config/'device-support-wireless.config',BOARD/'kernel.config']
env=dict(os.environ,ARCH='arm64',CROSS_COMPILE='aarch64-linux-gnu-')
run(['bash',str(KERNEL/'scripts/kconfig/merge_config.sh'),'-m',*map(str,fragments)],cwd=KERNEL,env=env)
make=['make','ARCH=arm64','CROSS_COMPILE=aarch64-linux-gnu-',f'-j{os.cpu_count()}']
run(make+['olddefconfig'],cwd=KERNEL,env=env)
actual_config=(KERNEL/'.config').read_text()
required=['MAXIO_PHY','DWMAC_SUN8I','PHY_SUN4I_USB','USB_EHCI_HCD_PLATFORM','USB_OHCI_HCD_PLATFORM','MFD_AXP20X_I2C','REGULATOR_AXP20X','SERIAL_8250_DW','EROFS_FS','EXT4_FS','IKCONFIG_PROC','IPV6_REACHABILITY_PROBE']
for option in required:assert f'CONFIG_{option}=y\n' in actual_config,option
assert 'CONFIG_AIC8800_WLAN_SUPPORT=' not in actual_config
run(make+['prepare','scripts','allwinner/sun50i-h618-k2b.dtb','drivers/net/phy/maxio.o','drivers/net/ethernet/stmicro/stmmac/stmmac_main.o','drivers/net/ethernet/stmicro/stmmac/dwmac-sun8i.o','drivers/phy/allwinner/phy-sun4i-usb.o','drivers/usb/host/ohci-platform.o','drivers/usb/host/ehci-platform.o'],cwd=KERNEL,env=env)
# Also compile the pinned external modules, catching API changes before a full build.
external=[
    ('v4l2loopback','https://codeload.github.com/umlaeute/v4l2loopback/tar.gz/v0.13.2','1e57e1e382d7451aa2a88d63cc9f146eab1f425b90e76104d4c3d73127e34771','',['v4l2loopback.o']),
    ('generic_raw_uart','https://codeload.github.com/alexreinert/piVCCU/tar.gz/b80aacfb75e9689d14d4e2c94380728816c6313e','1a99e87c48e95c173ce6f43b8783ac359022886265bb2ed86f67c6d05cf12658','kernel',['generic_raw_uart.o','rpi_rf_mod_led.o','dummy_rx8130.o','hb_rf_usb.o','hb_rf_usb_2.o','hb_rf_eth.o']),
]
for name,url,expected,subdir,objects in external:
    target=CHECK/name;target.mkdir(exist_ok=True)
    packed=CHECK/(name+'.tar.gz')
    with urlopen(url,timeout=90) as remote,packed.open('wb') as f:shutil.copyfileobj(remote,f)
    with packed.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==expected,name
    with tarfile.open(packed) as tar:tar.extractall(target,filter='data')
    unpacked=next(p for p in target.iterdir() if p.is_dir())
    patchdirs=[EXTERNAL/'patches'/name]
    if name=='generic_raw_uart':patchdirs.insert(0,EXTERNAL/'package/generic_raw_uart')
    for directory in patchdirs:
        for patch in sorted(directory.glob('*.patch')):
            run(['patch','-F0','-g0','-p1','--no-backup-if-mismatch','-t','-N','-i',str(patch)],cwd=unpacked)
    module=unpacked/subdir
    run(make+[f'M={module}',*objects],cwd=KERNEL,env=env)
dtb=KERNEL/'arch/arm64/boot/dts/allwinner/sun50i-h618-k2b.dtb'
def getprop(node,prop):
    return subprocess.check_output(['fdtget','-t','u',str(dtb),node,prop],text=True).strip()
node='/soc/i2c@7081400/pmic@36/regulators/dcdc3'
assert getprop(node,'regulator-min-microvolt')=='1500000'
assert getprop(node,'regulator-max-microvolt')=='1500000'
assert getprop('/soc/ethernet@5020000','allwinner,rx-delay-ps')=='2000'
assert getprop('/soc/ethernet@5020000','allwinner,tx-delay-ps')=='700'
compatible=subprocess.check_output(['fdtget','-t','s',str(dtb),'/soc/ethernet@5020000/mdio/ethernet-phy@0','compatible'],text=True).strip().split()
assert compatible==['ethernet-phy-id7b74.4411','ethernet-phy-ieee802.3-c22'],compatible
report={'kernel':version,'source_sha256':actual,'dtb_sha256':hashlib.sha256(dtb.read_bytes()).hexdigest(),'ddr3_linux_microvolts':1500000,'checks':'exact patches, effective config, DTB, changed driver objects and pinned external modules passed','hardware_boot_verified':False}
result=SOURCE/'validation-results';result.mkdir(exist_ok=True)
shutil.copyfile(KERNEL/'.config',result/'kernel.config')
shutil.copyfile(dtb,result/dtb.name)
(result/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
print('kernel validation: all checks passed',json.dumps(report),flush=True)
