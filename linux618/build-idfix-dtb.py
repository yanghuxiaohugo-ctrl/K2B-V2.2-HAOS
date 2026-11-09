#!/usr/bin/env python3
"""Compile an ID-only test DTB and compare every property to the delivered DTB."""
from pathlib import Path
from urllib.request import urlopen
import hashlib, json, os, shutil, struct, subprocess, tarfile

ROOT = Path.cwd()
ASSETS = ROOT / 'linux618'
BASELINE = ROOT / 'baseline'
OUT = ROOT / 'idfix-output'
TEMP = Path(os.environ['RUNNER_TEMP']) / 'k2b-idfix-kernel'
manifest = json.loads((ASSETS / 'patch-manifest.json').read_text())
version = manifest['kernel_version']
assert version == '6.18.62'

def digest(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def run(args, **kwargs):
    print('+', ' '.join(map(str, args)), flush=True)
    subprocess.run(args, check=True, **kwargs)

def parse_fdt(blob):
    header = struct.unpack_from('>10I', blob)
    assert header[0] == 0xd00dfeed and header[1] <= len(blob)
    off = header[2]
    strings = blob[header[3]:header[3] + header[8]]
    nodes, props, stack = set(), {}, []
    while True:
        token = struct.unpack_from('>I', blob, off)[0]
        off += 4
        if token == 1:
            end = blob.index(b'\0', off)
            stack.append(blob[off:end].decode())
            nodes.add('/'.join(stack))
            off = (end + 4) & ~3
        elif token == 2:
            stack.pop()
        elif token == 3:
            length, nameoff = struct.unpack_from('>II', blob, off)
            off += 8
            name = strings[nameoff:strings.index(b'\0', nameoff)].decode()
            props[('/'.join(stack), name)] = blob[off:off + length]
            off = (off + length + 3) & ~3
        elif token == 4:
            pass
        elif token == 9:
            break
        else:
            raise ValueError(token)
    off = header[4]
    reserves = []
    while True:
        entry = struct.unpack_from('>QQ', blob, off)
        off += 16
        if entry == (0, 0):
            break
        reserves.append(entry)
    return nodes, props, reserves

baseline_dtb = BASELINE / 'sun50i-h618-k2b.dtb'
baseline_sha = '4395f58bb250e7d98056c173a9be280bd7dc65bd9cd10dc505a5a49f0ec97dbd'
assert digest(baseline_dtb) == baseline_sha
baseline_config = BASELINE / 'kernel.config'
assert 'Linux/arm64 6.18.62 Kernel Configuration' in baseline_config.read_text()
TEMP.mkdir(parents=True, exist_ok=True)
archive = TEMP / f'linux-{version}.tar.xz'
with urlopen(f'https://cdn.kernel.org/pub/linux/kernel/v6.x/linux-{version}.tar.xz', timeout=120) as remote, archive.open('wb') as f:
    shutil.copyfileobj(remote, f)
assert digest(archive) == manifest['kernel_sha256']
with tarfile.open(archive) as tar:
    tar.extractall(TEMP, filter='data')
kernel = TEMP / f'linux-{version}'
patches = sorted((ASSETS / 'global-patches/linux').glob('*.patch'))
for entry in manifest['patches']:
    patch = ASSETS / 'patches' / entry['patch']
    assert digest(patch) == entry['sha256'], str(patch)
    patches.append(patch)
for patch in patches:
    run(['patch', '-F0', '-g0', '-p1', '--no-backup-if-mismatch', '-t', '-N', '-i', str(patch)], cwd=kernel)
shutil.copyfile(baseline_config, kernel / '.config')
make = ['make', 'ARCH=arm64', 'CROSS_COMPILE=aarch64-linux-gnu-', 'DTC_FLAGS=-@', f'-j{os.cpu_count()}']
run(make + ['olddefconfig'], cwd=kernel)
config = (kernel / '.config').read_text()
for option in ('MAXIO_PHY', 'DWMAC_SUN8I', 'PHY_SUN4I_USB', 'REGULATOR_AXP20X'):
    assert f'CONFIG_{option}=y\n' in config, option
run(make + ['allwinner/sun50i-h618-k2b.dtb'], cwd=kernel)
built = kernel / 'arch/arm64/boot/dts/allwinner/sun50i-h618-k2b.dtb'
old_nodes, old_props, old_reserves = parse_fdt(baseline_dtb.read_bytes())
new_nodes, new_props, new_reserves = parse_fdt(built.read_bytes())
assert old_nodes == new_nodes, 'Unexpected DT node change'
assert old_reserves == new_reserves, 'Unexpected memory reservation change'
assert old_props.keys() == new_props.keys(), 'Unexpected property added or removed'
changed = [key for key in old_props if old_props[key] != new_props[key]]
key = ('/soc/ethernet@5020000/mdio/ethernet-phy@0', 'compatible')
assert changed == [key], changed
assert old_props[key] == b'ethernet-phy-ieee802.3-c22\0'
assert new_props[key] == b'ethernet-phy-id7b74.4411\0ethernet-phy-ieee802.3-c22\0'
rail = '/soc/i2c@7081400/pmic@36/regulators/dcdc3'
for prop in ('regulator-min-microvolt', 'regulator-max-microvolt'):
    assert struct.unpack('>I', new_props[(rail, prop)])[0] == 1500000
OUT.mkdir(exist_ok=True)
shutil.copyfile(built, OUT / built.name)
original = OUT / 'original'
original.mkdir(exist_ok=True)
shutil.copyfile(baseline_dtb, original / baseline_dtb.name)
shutil.copyfile(ASSETS / 'IDFIX-TEST-INSTRUCTIONS.md', OUT / 'IDFIX-TEST-INSTRUCTIONS.md')
report = {
    'kernel': version,
    'kernel_source_sha256': manifest['kernel_sha256'],
    'baseline_run': 42506899967,
    'baseline_dtb_sha256': baseline_sha,
    'test_dtb_sha256': digest(built),
    'test_dtb_size': built.stat().st_size,
    'changed_property': {'node': key[0], 'property': key[1], 'before': old_props[key].decode().rstrip('\0').split('\0'), 'after': new_props[key].decode().rstrip('\0').split('\0')},
    'all_other_properties_nodes_and_reservations_identical': True,
    'ddr3_linux_microvolts': 1500000,
    'hardware_boot_verified': False,
    'commit': os.environ.get('GITHUB_SHA'),
}
(OUT / 'validation.json').write_text(json.dumps(report, indent=2) + '\n')
checksums = []
for path in sorted(OUT.rglob('*')):
    if path.is_file():
        checksums.append(f'{digest(path)}  {path.relative_to(OUT).as_posix()}')
(OUT / 'SHA256SUMS.txt').write_text('\n'.join(checksums) + '\n')
print('IDFIX DTB validation: all checks passed', json.dumps(report), flush=True)
