from pathlib import Path
from urllib.request import urlopen
import hashlib,json,os,shutil,subprocess,tarfile

ROOT=Path.cwd();external=ROOT/'operating-system/buildroot-external'
board=external/'board/hardkernel/kickpi-k2b'
folder=Path(os.environ['RUNNER_TEMP'])/'k2b-community-uboot';folder.mkdir(exist_ok=True)
archive=folder/'u-boot-2025.01.tar.bz2'
with urlopen('https://ftp.denx.de/pub/u-boot/u-boot-2025.01.tar.bz2',timeout=90) as remote,archive.open('wb') as target:shutil.copyfileobj(remote,target)
with archive.open('rb') as source:assert hashlib.file_digest(source,'sha256').hexdigest()=='cdef7d507c93f1bbd9f015ea9bc21fa074268481405501945abc6f854d5b686f'
with tarfile.open(archive) as tar:tar.extractall(folder,filter='data')
uboot=folder/'u-boot-2025.01'
for directory in (external/'patches/uboot',board/'patches/uboot'):
    for patch in sorted(directory.glob('*.patch')):
        subprocess.run(['patch','-F0','-g0','-p1','--no-backup-if-mismatch','-t','-N','-i',str(patch)],cwd=uboot,check=True)
fragments=[board/'uboot.config',external/'bootloader/uboot.config',board/'uboot.config']
config='\n'.join(path.read_text() for path in fragments)+'\n'
(uboot/'.config').write_text(config)
subprocess.run(['make','ARCH=arm','CROSS_COMPILE=aarch64-linux-gnu-','olddefconfig'],cwd=uboot,check=True)
actual=(uboot/'.config').read_text()
for flag in ('OF_BOARD_SETUP','DM_SEQ_ALIAS','ENV_IS_NOWHERE','SUNXI_DRAM_H616_DDR3_1333'):
    assert f'CONFIG_{flag}=y\n' in actual,flag
for line in ('CONFIG_DRAM_CLK=648','CONFIG_AXP_DCDC3_VOLT=1500'):
    assert line+'\n' in actual,line
dts=uboot/'dts/upstream/src/arm64/allwinner/sun50i-h618-k2b.dts'
assert 'ethernet0 = &emac0;' in dts.read_text()
evidence=ROOT/'validation-results/community-preflight';evidence.mkdir(parents=True,exist_ok=True)
shutil.copyfile(uboot/'.config',evidence/'uboot.config')
(evidence/'validation.json').write_text(json.dumps({'status':'exact U-Boot patches and effective Kconfig passed','source_sha256':'cdef7d507c93f1bbd9f015ea9bc21fa074268481405501945abc6f854d5b686f','hardware_boot_verified':False},indent=2)+'\n')
print('Community U-Boot source/config preflight passed; hardware behavior remains unverified')
