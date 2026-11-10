from pathlib import Path
import hashlib,json,subprocess,sys

ASSETS=Path(__file__).resolve().parent
ROOT=Path.cwd()
BOARD=ROOT/'haos-overlay/buildroot-external/board/hardkernel/kickpi-k2b'
expected='629fdd6e5e8571bb7c82689fb0c75723bd958c8248848b555b86768a61c6470f'
old=BOARD/'patches/uboot/002-h618-dts.patch'
assert hashlib.sha256(old.read_bytes()).hexdigest()==expected,'Pinned U-Boot DTS patch changed'
source=ASSETS/'uboot/003-k2b-ethernet-alias-stable-mac.patch'
target=BOARD/'patches/uboot'/source.name
assert not target.exists(),'Unexpected pre-existing MAC patch'
target.write_bytes(source.read_bytes())
manifest=json.loads((ASSETS/'patch-manifest.json').read_text())
for entry in manifest['patches']:
    source=ASSETS/'linux'/entry['patch'] if entry['patch'].startswith('007-') else BOARD/'patches/linux'/entry['patch']
    assert hashlib.sha256(source.read_bytes()).hexdigest()==entry['sha256'],entry['patch']
    if entry['patch'].startswith('007-'):
        (BOARD/'patches/linux'/source.name).write_bytes(source.read_bytes())
subprocess.run([sys.executable,str(ASSETS/'defaults/apply-clock-network-defaults.py'),'--checkout',str(ROOT)],check=True)
print('Community preparation: paired Linux/U-Boot ethernet aliases; no fixed MAC; original PHY/DDR patches retained')
