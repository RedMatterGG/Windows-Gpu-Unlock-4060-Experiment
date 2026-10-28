#!/usr/bin/env python3
"""Offline AD107 transaction tests. Never opens a physical GPU or stages EFI."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--zig', required=True)
p.add_argument('--prom', required=True)
p.add_argument('--assets', required=True)
a = p.parse_args()
r = Path(__file__).resolve().parent
prom = Path(a.prom).resolve()
assets = Path(a.assets).resolve()
data = prom.read_bytes()
if len(data) == 0xd6c00:
    data += b'\xff' * (0x100000 - len(data))
if len(data) != 0x100000 or hashlib.sha256(data).hexdigest() != '6ac9d7b2428cd1bed8c41ef78558ea27d4ad0808dfe6fcb9637de179d5044a78':
    raise SystemExit('PROM is not the captured AD107 fixture')
out = r / 'test-build'
out.mkdir(exist_ok=True)
prom = out / 'ad107-prom.bin'
prom.write_bytes(data)
sources = ['port', 'compat', 'vendor/unlock_610', 'vendor/prep_610',
           'vendor/layout_610', 'vendor/vbios_610', 'vendor/gfw_eval']
for spec in json.loads((r / 'unlock/assets.json').read_text()):
    content = (assets / spec['Name']).read_bytes()
    if len(content) != spec['Bytes'] or hashlib.sha256(content).hexdigest() != spec['Sha256']:
        raise SystemExit('Asset identity mismatch: ' + spec['Name'])
cmd = [a.zig, 'cc', '-std=c11', '-fshort-wchar', '-O1', '-Wall', '-Wextra',
       '-Wno-unused-parameter', '-Wno-unused-function', '-Wno-format',
       '-D__KERNEL__', '-DGU_UEFI_PORT',
       '-Iunlock/compat', '-Ideps/edk2/MdePkg/Include', '-Ideps/edk2/MdePkg/Include/X64',
       'unlock/tests/test_ad102_transaction.c']
cmd += ['unlock/' + s + '.c' for s in sources]
exe = out / 'ad107-core.exe'
subprocess.run(cmd + ['-o', str(exe)], cwd=r, check=True)
with (out / 'ad107-core-results.txt').open('w') as log:
    result = subprocess.run([str(exe), str(prom), str(assets)], cwd=r,
                            stdout=log, stderr=subprocess.STDOUT)
text = (out / 'ad107-core-results.txt').read_text()
print(text[-8000:])
report = {'core_passed': result.returncode == 0, 'returncode': result.returncode,
          'physical_gpu_tested': False, 'prom_sha256': hashlib.sha256(prom.read_bytes()).hexdigest()}
report['identity_passed'] = False
(out / 'ad107-results.json').write_text(json.dumps(report, indent=2) + '\n')
result.check_returncode()
identity = out / 'ad107-identity.exe'
identity_cmd = [x for x in cmd if x not in ('unlock/tests/test_ad102_transaction.c', 'unlock/vendor/unlock_610.c')]
subprocess.run(identity_cmd + ['unlock/tests/test_ad107_identity.c', '-o', str(identity)], cwd=r, check=True)
subprocess.run([str(identity)], cwd=r, check=True)
flags = cmd[:cmd.index('unlock/tests/test_ad102_transaction.c')]
rejected = subprocess.run(flags + ['-fsyntax-only', '-DGU_TARGET_PCI_ID=0x270410deU',
                                  'unlock/vendor/unlock_610.c'], cwd=r, capture_output=True, text=True)
if rejected.returncode == 0 or 'Transaction PCI identity must match the selected board' not in rejected.stderr:
    raise SystemExit('Conflicting target override was not rejected as expected')
print('Conflicting build-time PCI identity rejected as expected.')
report['identity_passed'] = True
report['conflicting_override_rejected'] = True
report['passed'] = True
(out / 'ad107-results.json').write_text(json.dumps(report, indent=2) + '\n')
