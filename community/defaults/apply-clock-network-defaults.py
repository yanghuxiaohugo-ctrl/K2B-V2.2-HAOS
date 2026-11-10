#!/usr/bin/env python3
"""Prepare clock/connectivity defaults in a build checkout; never a live board."""
from pathlib import Path
import argparse
import hashlib

ASSETS = Path(__file__).resolve().parent
LEGACY_SHA = '67be8c7b9f10d4ef26fa84c480a828808ea68647241a635b931aa7b518099ad0'
OVERLAY_SETUP_SHA = '35ca7cc0ed2565ebb96cccb91cd6b8f69abd1881717c8eb8b7f7c68265d8f709'
LEGACY_NM_SHA = 'f2fb54fcf5431394e4620d0c9cb5800d3c88f6be1a07b11c072ca4c6873be4ad'

def sha(data):
    return hashlib.sha256(data).hexdigest()

def normalized(path):
    return path.read_text(encoding='utf-8').encode('utf-8')

def apply(checkout):
    root = checkout.resolve()
    overlay = root / 'haos-overlay/buildroot-external/rootfs-overlay'
    upstream = root / 'operating-system/buildroot-external/rootfs-overlay'
    config = overlay / 'etc/systemd/timesyncd.conf'
    nm_config = overlay / 'etc/NetworkManager/NetworkManager.conf'
    setup = upstream / 'usr/libexec/hassos-overlay'
    if not config.is_file() or not setup.is_file() or not nm_config.is_file():
        raise ValueError('Expected a haos-ace build checkout with its operating-system submodule')
    new_config = normalized(ASSETS / 'timesyncd.conf')
    new_nm_config = normalized(ASSETS / 'NetworkManager.conf')
    if sha(normalized(nm_config)) not in (LEGACY_NM_SHA, sha(new_nm_config)):
        raise ValueError('Build overlay contains customized NetworkManager defaults; refusing to overwrite')
    if sha(normalized(config)) not in (LEGACY_SHA, sha(new_config)):
        raise ValueError('Build overlay contains a customized time config; refusing to overwrite')
    old_setup = normalized(setup)
    if sha(old_setup) != OVERLAY_SETUP_SHA:
        raise ValueError('Pinned upstream overlay initialization changed; review before applying')
    marker = b'# TimeSync\n'
    assert old_setup.count(marker) == 1
    patched_setup = old_setup.replace(marker, marker +
        b'/bin/sh /usr/libexec/k2b-timesync-defaults /mnt/overlay/etc/systemd/timesyncd.conf /etc/systemd/timesyncd.conf\n')
    helper = normalized(ASSETS / 'k2b-timesync-defaults.sh')
    targets = {
        overlay / 'usr/libexec/hassos-overlay': patched_setup,
        overlay / 'usr/libexec/k2b-timesync-defaults': helper,
    }
    for target, data in targets.items():
        if target.exists() and normalized(target) != data:
            raise ValueError(f'Conflicting overlay file: {target}')
    config.write_bytes(new_config)
    nm_config.write_bytes(new_nm_config)
    for target, data in targets.items():
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        target.chmod(0o755)
    print('clock/network defaults preparation: guarded NTP migration and direct connectivity URI installed')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkout', type=Path, required=True)
    apply(parser.parse_args().checkout)
