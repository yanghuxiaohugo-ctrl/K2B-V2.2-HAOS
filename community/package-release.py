from pathlib import Path
import hashlib,json,os,shutil,subprocess,tarfile

ROOT=Path.cwd();ASSETS=Path(__file__).resolve().parent
release=ROOT/'community-release';release.mkdir(exist_ok=True)
images=ROOT/'output/images'
for image in images.glob('haos*.img.xz'):shutil.copyfile(image,release/image.name)
assert list(release.glob('*.img.xz')),'No image for release'
shutil.copyfile(ASSETS/'RELEASE-NOTES.md',release/'RELEASE-NOTES.md')
shutil.copyfile(ASSETS/'SOURCE-README.md',release/'SOURCE-README.md')
shutil.copyfile(ROOT/'validation-results/community/VALIDATION.json',release/'VALIDATION.json')
info={'repository':os.environ['GITHUB_REPOSITORY'],'commit':os.environ['GITHUB_SHA'],'run_url':f'https://github.com/{os.environ["GITHUB_REPOSITORY"]}/actions/runs/{os.environ["GITHUB_RUN_ID"]}','haos_ace_commit':'1fcb5e87e86cf22015e46ffc53902fe83c5ed8d1','haos_commit':'bd5ea3763f7cb7e47c280f72b837e12b6578bd8a','buildroot_commit':'02f1553a34c2b8f6e432fe4300bfe529897d5f3c','kernel':'6.18.62','uboot':'2025.01','atf':'v2.11','hardware_boot_verified':False,'classification':'community prerelease, new image untested on hardware'}
(release/'BUILD-INFO.json').write_text(json.dumps(info,indent=2)+'\n')
# Include effective sources, overlays, complete source/license collection, and public
# build/validation material. Never copy the build tree's generated signing key.
snapshot=release/'source-build-snapshot.tar.gz'
with tarfile.open(snapshot,'w:gz',compresslevel=3) as tar:
    def include(entry):
        parts=Path(entry.name).parts
        if any(part in ('.git','output','__pycache__') for part in parts):return None
        if Path(entry.name).name in ('key.pem','cert.pem'):return None
        return entry
    for source,name in [(ROOT/'operating-system','operating-system'),(ROOT/'haos-overlay','haos-overlay'),(ROOT/'scripts','haos-ace-scripts'),(ROOT/'build.sh','haos-ace-build.sh'),(ASSETS.parent,'community-build-repository')]:
        tar.add(source,arcname=name,filter=include)
legal=ROOT/'operating-system/output/legal-info';assert legal.is_dir()
with tarfile.open(release/'licenses-package-sources.tar.gz','w:gz',compresslevel=3) as tar:
    tar.add(legal,arcname='legal-info')
# GitHub limits an individual release asset to 2 GiB. Keep large source sets
# available without dropping any bytes; document concatenation in SOURCE-README.
limit=1900*1024*1024
for archive in list(release.glob('*.tar.gz')):
    if archive.stat().st_size>limit:
        with archive.open('rb') as source:
            number=0
            while True:
                block=source.read(limit)
                if not block:break
                (release/(archive.name+f'.part{number:03d}')).write_bytes(block);number+=1
        archive.unlink()
with (release/'SHA256SUMS.txt').open('w') as target:
    for file in sorted(release.iterdir()):
        if file.is_file() and file.name!='SHA256SUMS.txt':
            with file.open('rb') as data:digest=hashlib.file_digest(data,'sha256').hexdigest()
            target.write(f'{digest}  {file.name}\n')
print('Release payload files:',json.dumps({p.name:p.stat().st_size for p in release.iterdir()}))
