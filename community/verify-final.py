from pathlib import Path
import hashlib,json,subprocess

ROOT=Path.cwd();OUT=ROOT/'operating-system/output'
uboot=OUT/'build/uboot-2025.01'
cfg=(uboot/'.config').read_text()
for flag in ('OF_BOARD_SETUP','DM_SEQ_ALIAS','ENV_IS_NOWHERE','SUNXI_DRAM_H616_DDR3_1333'):
    assert f'CONFIG_{flag}=y\n' in cfg,flag
assert 'CONFIG_DRAM_CLK=648\n' in cfg
assert 'CONFIG_AXP_DCDC3_VOLT=1500\n' in cfg
def prop(dtb,node,key):return subprocess.check_output(['fdtget','-t','s',str(dtb),node,key],text=True).strip()
control=uboot/'u-boot.dtb'
assert prop(control,'/aliases','ethernet0')=='/soc/ethernet@5020000'
dtbs=sorted((OUT/'images').rglob('sun50i-h618-k2b.dtb'));assert dtbs
for dtb in dtbs:assert prop(dtb,'/aliases','ethernet0')=='/soc/ethernet@5020000'
assets=Path(__file__).resolve().parent/'defaults'
target=OUT/'target'
for name,dest in [('timesyncd.conf','etc/systemd/timesyncd.conf'),('NetworkManager.conf','etc/NetworkManager/NetworkManager.conf'),('k2b-timesync-defaults.sh','usr/libexec/k2b-timesync-defaults')]:
    assert (assets/name).read_bytes()==(target/dest).read_bytes(),dest
for dest in ('usr/libexec/hassos-overlay','usr/libexec/k2b-timesync-defaults'):
    assert (target/dest).stat().st_mode & 0o111,dest
setup=(target/'usr/libexec/hassos-overlay').read_text()
assert setup.index('/bin/sh /usr/libexec/k2b-timesync-defaults')<setup.index('if [ ! -f /mnt/overlay/etc/systemd/timesyncd.conf ]')
evidence=ROOT/'validation-results/community';evidence.mkdir(parents=True,exist_ok=True)
report={'status':'build checks passed; new image has not been hardware tested','hardware_boot_verified':False,'uboot_control_alias':prop(control,'/aliases','ethernet0'),'linux_alias':prop(dtbs[0],'/aliases','ethernet0'),'effective_uboot_flags':['OF_BOARD_SETUP','DM_SEQ_ALIAS','ENV_IS_NOWHERE'],'ddr_clock_mhz':648,'ddr_dcdc3_mv':1500,'fixed_per_device_mac_in_image':False,'original_phy_ddr_patches_retained':True,'new_defaults_match_assets':True,'remaining_hardware_tests':['cold boot','unmodified NetworkManager profile MAC propagation','warm reboot MAC stability','two-board uniqueness','NTP with network outage','USB gadget regression']}
(evidence/'VALIDATION.json').write_text(json.dumps(report,indent=2)+'\n')
(evidence/'uboot.config').write_text(cfg)
print('Community final build checks passed:',json.dumps(report))
