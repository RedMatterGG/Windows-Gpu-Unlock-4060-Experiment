"""Rebuild the exact tested EFI from this source bundle; no hardware writes."""
import argparse
import hashlib
from pathlib import Path
import subprocess
import sys

EXPECTED = 'a33a506b1522fd050341c6adc05766be6d1cb379242821975a643770e4bf7924'

def main():
    root = Path(__file__).resolve().parent
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--zig', default=str(root / 'tools/zig-x86_64-windows-0.14.1/zig.exe'))
    a = p.parse_args()
    subprocess.run([sys.executable, str(root / 'project/build.py'), '--zig', a.zig], check=True)
    artifact = root / 'project/USB/EFI/BOOT/BOOTX64.EFI'
    digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
    if digest != EXPECTED:
        raise SystemExit('EFI differs from hardware-tested candidate: ' + digest)
    print('PASS: rebuilt EFI is byte-identical to the hardware-tested RTX 4060 candidate.')

if __name__ == '__main__':
    main()
