"""Fail closed on binary/private files and local executable paths in a source ZIP."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tempfile
import zipfile

ALLOWED = {'.c', '.h', '.inc', '.py', '.ps1', '.cmd', '.bat', '.md', '.txt', '.json', '.yml', '.yaml', '.cu', '.toml'}
EXEC = {'.c', '.h', '.inc', '.py', '.ps1', '.cmd', '.bat', '.cu'}

def audit(path):
    errors = []
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        if len(names) != len(set(names)):
            errors.append('duplicate ZIP members')
        manifest = json.loads(z.read('SHA256SUMS.json'))
        if set(manifest) != set(names) - {'SHA256SUMS.json'}:
            errors.append('manifest membership mismatch')
        for name in names:
            p = PurePosixPath(name)
            data = z.read(name)
            if p.is_absolute() or '..' in p.parts or '\\' in name or ':' in name:
                errors.append('unsafe member: ' + name)
            if p.suffix.lower() not in ALLOWED and p.name not in {'LICENSE', 'NOTICE', '.gitignore', '.gitattributes'}:
                errors.append('not source allowlist: ' + name)
            if any(x.lower() in {'.git', 'cache', 'local', 'data', 'captures', 'results', 'usb', '__pycache__', 'test-build'} for x in p.parts):
                errors.append('private/generated directory: ' + name)
            if data.startswith((b'MZ', b'\x7fELF', b'PK\x03\x04')) or b'\0' in data:
                errors.append('binary content: ' + name)
            text = data.decode('utf-8-sig', errors='replace')
            if p.suffix.lower() in EXEC and re.search(r'(?i)\b[FG]:[\\/]', text):
                errors.append('machine-local executable path: ' + name)
            if re.search(r'(?i)(BootNext|BootOrder|FirmwareBootVariables|prom_view\.bin|BEGIN (?:RSA |OPENSSH )?PRIVATE KEY)', text) and p.suffix.lower() in {'.ps1', '.cmd', '.json'}:
                errors.append('boot/private material: ' + name)
            if name != 'SHA256SUMS.json' and hashlib.sha256(data).hexdigest() != manifest.get(name):
                errors.append('hash mismatch: ' + name)
    if errors:
        raise SystemExit('\n'.join(errors))
    print(f'PASS: {len(names)} source members; hashes, paths, binary/private checks')

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('zip')
    p.add_argument('--zig', type=Path, help='Also extract into a temporary sibling folder and build/test with this Zig')
    a = p.parse_args()
    audit(a.zip)
    if a.zig:
        zig = a.zig.resolve()
        with tempfile.TemporaryDirectory(prefix='source-portability-', dir=Path(a.zip).resolve().parent) as temp:
            with zipfile.ZipFile(a.zip) as z:
                z.extractall(temp)
            root = Path(temp)
            fixed = (root / 'verify_fixed.py').is_file()
            commands = ([['verify_fixed.py', '--zig', str(zig)]] if fixed else [
                ['project/build.py', '--zig', str(zig)],
                ['project/build.py', '--zig', str(zig), '--unlock'],
                ['project/test.py', '--zig', str(zig)],
                ['make_test_fixtures.py'],
                ['-m', 'unittest', 'discover', '-s', 'benchmark-app', '-v'],
            ])
            for command in commands:
                subprocess.run([sys.executable, *command], cwd=root, check=True)
            print('PASS: extracted fixed-4060 source rebuild is byte-identical; no hardware tested' if fixed else
                  'PASS: extracted source capture/unlock builds, portable host tests, synthetic GUI tests; no hardware tested')
