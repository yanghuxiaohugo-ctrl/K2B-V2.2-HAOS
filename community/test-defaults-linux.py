from pathlib import Path
import hashlib,os,subprocess,tempfile

HERE=Path(__file__).resolve().parent
legacy=(HERE/'fixtures/legacy-timesyncd.conf').read_bytes()
defaults=HERE/'defaults/timesyncd.conf'
helper=HERE/'defaults/k2b-timesync-defaults.sh'
assert hashlib.sha256(legacy).hexdigest()=='67be8c7b9f10d4ef26fa84c480a828808ea68647241a635b931aa7b518099ad0'
assert os.name=='posix','Native Linux test required'
subprocess.run(['/bin/sh','-n',str(helper)],check=True)
passed=[]
with tempfile.TemporaryDirectory(prefix='k2b-clock-native-') as temporary:
    root=Path(temporary)
    cases=[('legacy',legacy,False,None,True),('custom',b'[Time]\nNTP=private.example\n',False,None,False),('empty',b'',False,None,False),('optout',legacy,True,None,False),('backup-conflict',legacy,False,b'custom backup\n',False),('existing-good-backup',legacy,False,legacy,True),('missing',None,False,None,False)]
    for name,initial,keep,backup,migrates in cases:
        folder=root/name;folder.mkdir();config=folder/'timesyncd.conf'
        if initial is not None:config.write_bytes(initial)
        if keep:(folder/'timesyncd.conf.k2b-keep').touch()
        saved=folder/'timesyncd.conf.pre-k2b-ntp-v1'
        if backup is not None:saved.write_bytes(backup)
        subprocess.run(['/bin/sh',str(helper),str(config),str(defaults)],check=True)
        expected=defaults.read_bytes() if migrates else initial
        assert (config.read_bytes() if config.exists() else None)==expected,name
        if migrates:
            assert saved.read_bytes()==legacy,name
            subprocess.run(['/bin/sh',str(helper),str(config),str(defaults)],check=True)
            assert config.read_bytes()==expected and saved.read_bytes()==legacy
        if backup is not None and not migrates:assert saved.read_bytes()==backup
        passed.append(name)
    folder=root/'symlink';folder.mkdir();original=folder/'custom';original.write_bytes(legacy)
    link=folder/'timesyncd.conf';link.symlink_to(original)
    subprocess.run(['/bin/sh',str(helper),str(link),str(defaults)],check=True)
    assert link.is_symlink() and original.read_bytes()==legacy
    passed.append('symlink-preserved')
print('Native Linux migration cases passed:',', '.join(passed))
