"""Prepare an isolated HAOS build checkout for the SWT6621S hypothesis."""
from pathlib import Path
from urllib.request import urlopen
import argparse,hashlib,io,json,os,shutil,tarfile,time

ASSETS=Path(__file__).resolve().parent
PACKAGES={
    'swt6621s-dkms_1.0.3_all.deb':'8217004dc1517e0d983d488dcfe24269474e7ecb218b3a456d177a9d57a57aa2',
    'swt6621s-firmware_1.0.3_all.deb':'c7e5237dd7ae4d786685d11afc9b003d946c68041434fe4a61f8f9bb74dda753',
}

def sha(data):return hashlib.sha256(data).hexdigest()

def data_members(package):
    blob=package.read_bytes();assert blob.startswith(b'!<arch>\n')
    offset=8
    while offset+60<=len(blob):
        header=blob[offset:offset+60];assert header[58:60]==b'`\n'
        name=header[:16].decode().strip().rstrip('/');size=int(header[48:58]);offset+=60
        content=blob[offset:offset+size];offset+=size+(size%2)
        if name.startswith('data.tar'):
            return tarfile.open(fileobj=io.BytesIO(content),mode='r:*')
    raise ValueError('Debian package has no data archive')

def download(cache,name,expected):
    target=cache/name
    if target.exists() and sha(target.read_bytes())==expected:return target
    url='https://github.com/Novice-PG/swt6621s/releases/download/1.0.3/'+name
    for attempt in range(3):
        try:
            with urlopen(url,timeout=45) as source:data=source.read()
            assert sha(data)==expected,('Source package checksum mismatch',name)
            target.write_bytes(data);return target
        except Exception:
            if attempt==2:raise
            time.sleep(2)
    raise AssertionError('unreachable')

def prepare(root,cache):
    root=root.resolve();cache.mkdir(parents=True,exist_ok=True)
    external=root/'haos-overlay/buildroot-external'
    board=external/'board/hardkernel/kickpi-k2b'
    assert '6.18.62' in (external/'configs/k2b_h618_defconfig').read_text()
    expected='59b8087d15e07338b363d2851bb071e155dfc45dc0c98252d8403a0d80ad8b3b'
    assert sha((board/'uboot.config').read_text().encode())==expected,'DDR3 configuration changed'
    package=external/'package/k2b-swt6621s';payload=package/'payload';payload.mkdir(parents=True,exist_ok=True)
    firmware=external/'rootfs-overlay/lib/firmware';firmware.mkdir(parents=True,exist_ok=True)
    extracted=[]
    for name,expected_sha in PACKAGES.items():
        path=download(cache,name,expected_sha)
        with data_members(path) as tar:
            for item in tar:
                if not item.isfile():continue
                member=item.name.removeprefix('./')
                if member.startswith('usr/src/swt6621s-1.0.3/'):
                    relative=member.removeprefix('usr/src/swt6621s-1.0.3/')
                    assert '..' not in Path(relative).parts
                    target=payload/relative
                elif member.startswith('lib/firmware/'):
                    relative=member.removeprefix('lib/firmware/')
                    if relative=='SHA256SUMS':continue
                    assert '..' not in Path(relative).parts
                    target=firmware/relative
                else:continue
                data=tar.extractfile(item).read();target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
                target.chmod(item.mode & 0o777)
                extracted.append({'path':target.relative_to(external).as_posix(),'bytes':len(data),'sha256':sha(data)})
    assert (payload/'src/Makefile').is_file()
    assert (payload/'LICENSE').is_file()
    assert (firmware/'sv6160lite.nvbin').is_file()
    config=package/'Config.in'
    config.write_text('config BR2_PACKAGE_K2B_SWT6621S\n\tbool "K2B SWT6621S wireless test driver"\n\tdepends on BR2_LINUX_KERNEL\n\thelp\n\t  Pinned 1.0.3 SDIO Wi-Fi and Bluetooth modules for K2B V2.2.\n',encoding='utf-8')
    (package/'k2b-swt6621s.mk').write_text('''# Source package is verified and staged by wireless/prepare.py.
K2B_SWT6621S_VERSION = 1.0.3
K2B_SWT6621S_SITE = $(BR2_EXTERNAL_HASSOS_PATH)/package/k2b-swt6621s/payload
K2B_SWT6621S_SITE_METHOD = local
K2B_SWT6621S_LICENSE = GPL-2.0
K2B_SWT6621S_LICENSE_FILES = LICENSE
K2B_SWT6621S_MODULE_SUBDIRS = src
# Match the published 1.0.3 fix for arm64 module ftrace load crashes.
K2B_SWT6621S_MODULE_MAKE_OPTS = KCFLAGS=-fpatchable-function-entry=0
$(eval $(kernel-module))
$(eval $(generic-package))
''',encoding='utf-8')
    root_config=external/'Config.in'
    source=(root_config if root_config.exists() else root/'operating-system/buildroot-external/Config.in').read_text()
    line='source "$BR2_EXTERNAL_HASSOS_PATH/package/k2b-swt6621s/Config.in"\n'
    if line not in source:root_config.write_text(source+'\n'+line,encoding='utf-8')
    defconfig=external/'configs/k2b_h618_defconfig';source=defconfig.read_text()
    if 'BR2_PACKAGE_K2B_SWT6621S=y\n' not in source:defconfig.write_text(source+'\nBR2_PACKAGE_K2B_SWT6621S=y\n',encoding='utf-8')
    fragment=board/'kernel.config';source=fragment.read_text()
    addition='''
# SWT6621S hypothesis test: no change to DDR3 or Maxio settings.
CONFIG_WLAN=y
CONFIG_CFG80211=m
CONFIG_RFKILL=y
CONFIG_BT=m
CONFIG_BT_BREDR=y
CONFIG_BT_LE=y
CONFIG_PWRSEQ_SIMPLE=y
'''
    if addition not in source:fragment.write_text(source+addition,encoding='utf-8')
    patch=ASSETS/'008-k2b-swt6621s-sdio-test.patch'
    shutil.copyfile(patch,board/'patches/linux'/patch.name)
    overlay=external/'rootfs-overlay'
    for relative in ('usr/libexec/k2b-wireless-test','usr/lib/systemd/system/k2b-wireless-test.service'):
        target=overlay/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ASSETS/'rootfs'/relative,target)
        target.chmod(0o755 if relative.endswith('k2b-wireless-test') else 0o644)
    wants=overlay/'usr/lib/systemd/system/multi-user.target.wants';wants.mkdir(parents=True,exist_ok=True)
    link=wants/'k2b-wireless-test.service'
    if not link.exists():link.symlink_to('../k2b-wireless-test.service')
    report={'hypothesis':'K2B V2.2 VS6621S40 / SWT6621S SDIO 1ffe:6621','hardware_verified':False,'driver_version':'1.0.3','source_packages':PACKAGES,'source_url':'https://github.com/Novice-PG/swt6621s/releases/tag/1.0.3','original_ddr3_config_sha256':expected,'firmware_is_vendor_binary':True,'public_release_approved':False,'files':extracted}
    output=root/'validation-results/wireless';output.mkdir(parents=True,exist_ok=True)
    (output/'source-manifest.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('Wireless preparation: pinned source/firmware verified; three external modules; original DDR3/Maxio retained; hardware hypothesis unverified',flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkout',type=Path,default=Path.cwd())
    parser.add_argument('--cache',type=Path,default=Path(os.environ.get('RUNNER_TEMP',ASSETS))/'k2b-wireless-downloads')
    args=parser.parse_args();prepare(args.checkout,args.cache)
