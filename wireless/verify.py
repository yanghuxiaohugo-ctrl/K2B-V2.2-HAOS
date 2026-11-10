from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess

ROOT=Path.cwd();ASSETS=Path(__file__).resolve().parent
def run(args,**kwargs):
    print('+',' '.join(map(str,args)),flush=True);subprocess.run(args,check=True,**kwargs)
def prop(dtb,node,key,kind='s'):
    return subprocess.check_output(['fdtget','-t',kind,str(dtb),node,key],text=True).strip()
def dtb_checks(dtb):
    assert prop(dtb,'/soc/mmc@4021000','status')=='okay'
    assert prop(dtb,'/soc/mmc@4021000','max-frequency','u')=='100000000'
    resets=list(map(int,prop(dtb,'/pwrseq','reset-gpios','u').split()))
    assert len(resets)==8 and resets[0]==resets[4] and resets[1:4]==[6,18,1] and resets[5:]==[6,19,1],resets
    assert prop(dtb,'/aliases','ethernet0')=='/soc/ethernet@5020000'
    assert prop(dtb,'/soc/ethernet@5020000/mdio/ethernet-phy@0','compatible').split()==['ethernet-phy-id7b74.4411','ethernet-phy-ieee802.3-c22']
    node='/soc/i2c@7081400/pmic@36/regulators/dcdc3'
    for name in ('regulator-min-microvolt','regulator-max-microvolt'):assert prop(dtb,node,name,'u')=='1500000'
    assert prop(dtb,'/soc/mmc@4022000','status')=='disabled','eMMC must stay disabled on this target'

parser=argparse.ArgumentParser();parser.add_argument('--stage',choices=['preflight','final'],required=True);args=parser.parse_args()
evidence=ROOT/'validation-results/wireless';evidence.mkdir(parents=True,exist_ok=True)
if args.stage=='preflight':
    kernel=Path(os.environ['RUNNER_TEMP'])/'k2b-kernel-check/linux-6.18.62'
    original=ROOT/'operating-system/buildroot-external/package/k2b-swt6621s/payload/src'
    module=Path(os.environ['RUNNER_TEMP'])/'k2b-wireless-object-check'
    shutil.copytree(original,module)
    make=['make','ARCH=arm64','CROSS_COMPILE=aarch64-linux-gnu-',f'-j{os.cpu_count()}','KCFLAGS=-fpatchable-function-entry=0']
    run(make+['modules_prepare'],cwd=kernel)
    objects=[]
    for subdir,name in [('seekwaveplatform_lite','skw_sdio_lite'),('swt6621s_wifi','swt6621s_wifi'),('swtbt4l','skwbt')]:
        run(make+[f'M={module/subdir}',name+'.o'],cwd=kernel)
        file=module/subdir/(name+'.o')
        header=subprocess.check_output(['aarch64-linux-gnu-readelf','-h',str(file)],text=True)
        assert 'AArch64' in header
        objects.append({'module':name,'object_sha256':hashlib.sha256(file.read_bytes()).hexdigest()})
    dtb=kernel/'arch/arm64/boot/dts/allwinner/sun50i-h618-k2b.dtb';dtb_checks(dtb)
    report={'stage':'compiled all three AArch64 composite objects; final link deferred to full Buildroot build','modules':objects,'dtb_sha256':hashlib.sha256(dtb.read_bytes()).hexdigest(),'hardware_verified':False}
else:
    output=ROOT/'operating-system/output';target=output/'target'
    config=(output/'build/linux-6.18.62/.config').read_text()
    for line in ('CONFIG_WLAN=y','CONFIG_CFG80211=m','CONFIG_BT=m','CONFIG_BT_LE=y','CONFIG_PWRSEQ_SIMPLE=y'):assert line+'\n' in config,line
    result=[]
    for name in ('skw_sdio_lite','swt6621s_wifi','skwbt'):
        files=list((target/'lib/modules').rglob(name+'.ko*'));assert len(files)==1,(name,files)
        file=files[0];vermagic=subprocess.check_output(['modinfo','-F','vermagic',str(file)],text=True).strip();assert vermagic.startswith('6.18.62'),vermagic
        result.append({'name':name,'path':str(file.relative_to(target)),'vermagic':vermagic,'sha256':hashlib.sha256(file.read_bytes()).hexdigest()})
    manifest=json.loads((evidence/'source-manifest.json').read_text())
    for file in manifest['files']:
        if file['path'].startswith('rootfs-overlay/lib/firmware/'):
            path=target/file['path'].removeprefix('rootfs-overlay/');assert hashlib.sha256(path.read_bytes()).hexdigest()==file['sha256'],str(path)
    assert (target/'usr/lib/systemd/system/multi-user.target.wants/k2b-wireless-test.service').is_symlink()
    for dtb in (output/'images').rglob('sun50i-h618-k2b.dtb'):dtb_checks(dtb)
    report={'stage':'full build modules linked, installed and verified','modules':result,'driver_version':'1.0.3','firmware_verified':True,'hardware_verified':False,'sdio_id_hypothesis':'1ffe:6621','public_release_created':False}
(evidence/(args.stage+'-validation.json')).write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print('Wireless '+args.stage+' validation passed: '+json.dumps(report),flush=True)
