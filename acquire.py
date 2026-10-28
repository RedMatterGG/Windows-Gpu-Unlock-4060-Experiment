"""Local, explicit acquisition only. No firmware or tool uploads."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parent
ZIG_SHA = '554f5378228923ffd558eac35e21af020c73789d87afeabf4bfd16f2e6feed2c'

def run(*args):
    subprocess.run([sys.executable, *map(str, args)], check=True)

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('what', choices=['zig', 'assets'])
    p.add_argument('--root', type=Path, default=ROOT, help='Extracted kit root')
    p.add_argument('--cache', type=Path)
    a = p.parse_args()
    root = a.root.resolve()
    a.cache = a.cache or root / 'local/cache'
    a.cache.mkdir(parents=True, exist_ok=True)
    if a.what == 'zig':
        dest = a.cache / 'zig-0.14.1.zip'
        if not dest.exists():
            with urllib.request.urlopen('https://ziglang.org/download/0.14.1/zig-x86_64-windows-0.14.1.zip') as src, dest.open('xb') as out:
                import shutil
                shutil.copyfileobj(src, out)
        if hashlib.sha256(dest.read_bytes()).hexdigest() != ZIG_SHA:
            raise SystemExit('Zig archive SHA mismatch; remove corrupted local download manually')
        with zipfile.ZipFile(dest) as z:
            z.extractall(root / 'tools')
        print(root / 'tools/zig-x86_64-windows-0.14.1/zig.exe')
        return
    if sys.version_info < (3, 14):
        raise SystemExit('Python 3.14+ required for tar.zst extraction')
    f = root / 'firmware-tools'
    entries = json.loads((f / 'artifacts-610.43.03.json').read_text())['source_artifacts']
    # fetch_artifacts verifies existing cache before any download.
    run(f / 'fetch_artifacts.py', a.cache)
    out = root / 'local/assets'
    out.mkdir(parents=True, exist_ok=True)
    package = entries[2]
    # Python 3.14+ stdlib zstd avoids upstream generator's external zstd CLI.
    with tarfile.open(a.cache / package['filename'], mode='r|zst') as archive:
        wanted = {package['firmware'][0]['path']: ('gsp_ga10x.bin', package['firmware'][0]['sha256']), package['notice']['path']: ('NVIDIA-LICENSE', package['notice']['sha256'])}
        for member in archive:
            name = member.name.removeprefix('./')
            if name in wanted:
                if not member.isfile():
                    raise SystemExit('Expected regular firmware/license member')
                data = archive.extractfile(member).read()
                target, expected = wanted.pop(name)
                if hashlib.sha256(data).hexdigest() != expected:
                    raise SystemExit('Extracted package member SHA mismatch: ' + name)
                (out / target).write_bytes(data)
        if wanted:
            raise SystemExit('Missing firmware/license package members')
    run(f / 'extract_boot_assets.py', a.cache / entries[0]['filename'], out, '--arch', 'ad102', '--gsp', out / 'gsp_ga10x.bin')
    spec = importlib.util.spec_from_file_location('payload', f / 'ad102_payload.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    (out / 'v67-ad102-610.43.03-four-plm.bin').write_bytes(module.payload())
    for row in json.loads((root / 'project/unlock/assets.json').read_text()):
        data = (out / row['Name']).read_bytes()
        if len(data) != row['Bytes'] or hashlib.sha256(data).hexdigest() != row['Sha256']:
            raise SystemExit('Asset identity mismatch: ' + row['Name'])
    print('All five assets hash-verified. Private local use; review NVIDIA agreement.')

if __name__ == '__main__':
    main()
