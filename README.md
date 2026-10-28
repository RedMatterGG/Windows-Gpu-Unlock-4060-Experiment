# RTX 4060 AD107 Windows UEFI unlock — tested source

Experimental, exact-card source release. **Not a universal RTX 40 unlocker.**
No benchmark app, firmware images, EFI binaries, private captures or boot-variable
scripts are included. Nothing here installs itself, edits boot priority or reboots.

## Hardware-success configuration

| Component | Recorded configuration |
|---|---|
| GPU | Gigabyte RTX 4060 8 GB, PCI `10de:2882`, subsystem `1458:410b` |
| Chip | AD107, exact `PMC_BOOT_0 = 0x197000a1` |
| VBIOS | `95.07.31.00.c2` |
| Motherboard / BIOS | Gigabyte B450 AORUS PRO-CF / F67a |
| CPU | Ryzen 7 5700X3D; single physical GPU, no iGPU |
| Windows driver | NVIDIA 621.01 |
| Firmware framebuffer state | one physical GOP; GPU at `0000:07:00.0` |
| Usable framebuffer register | `0x1ffc` MiB (8188 MiB) |

Another machine with these model names is **not automatically compatible**.
Exact device/subsystem/chip, PCI capabilities, cold state and both ROM/PROM hashes
must pass unchanged. Different VBIOS, firmware ownership, console routing or BAR
state may reject the attempt. Never replace hashes or delete checks to force it.
Only this one machine/boot has a recorded hardware-success result. The retained
UEFI port is based on GPL-2.0-only upstream work; see notices and provenance.

## What made this 4060 work

The earlier experiment successfully ran FWSEC-FRTS, then stopped because two
transaction checks still required AD103's `0x193000a1`. They now use the selected
AD107 chip from `port.h`. A stale build-time PCI-ID override was removed, and a
conflicting override is a compile error. Earlier bus-1 and non-GOP-child assumptions
were already corrected in this source. The signed AD102-family four-PLM payload
was unchanged. No VBIOS flash or Windows driver patch is performed.

Recorded RUN04: required PLMs opened; completion marker/HALT passed; SS0 became
`0x88888888`, SS1 `0x8`; both survived one FLR and GOP reconnect. Final result was
clean: no retained DMA mappings or fault. FP16/BF16 FP32-accumulate and TF32 issue
rates roughly doubled; controls stayed similar. This does not establish application
speedups, gaming gains, long-term stability or sleep/hibernate support.

## Build from source (Windows x64)

Use Python 3.14+ (stdlib Zstandard support for asset extraction). No administrator
access is needed to acquire inputs or build. Run from this extracted repository:

```powershell
python acquire.py zig
python acquire.py assets
python verify_fixed.py
```

`acquire.py zig` fetches official **Zig 0.14.1** and verifies its pinned SHA-256.
`acquire.py assets` fetches pinned, hash-verified NVIDIA/CachyOS inputs, extracts
four stock assets and generates the GPL four-PLM payload locally. Review the NVIDIA
license saved with the assets. No firmware redistribution permission is implied.
EDK2 headers are included with notices; all 639 were verified against pinned
upstream commit `c1415771ac592ad8509351c46cd3cda4f38d7d52` (see `PROVENANCE.json`).

`verify_fixed.py` builds `project/USB/EFI/BOOT/BOOTX64.EFI` and requires SHA-256
`a33a506b1522fd050341c6adc05766be6d1cb379242821975a643770e4bf7924`, identical to
the recorded working EFI. Build source hashes and PE checks are in
`project/build-result.json`. A matching rebuild is not hardware validation on a
different PC. No CUDA installation is required for this unlock-only repository.

## Manual USB layout

Back up an existing stick first. Use an already prepared, firmware-bootable FAT32
USB; this repository never formats or repartitions a disk. Copy the built EFI to
`EFI/BOOT/BOOTX64.EFI`. Create `RTX4080-EXPERIMENT/ASSETS/` at the USB root and copy
the contents of `local/assets/` into it. The historical directory name is deliberate:
changing it changes the exact tested binary. Existing run logs must be preserved.

```text
EFI/BOOT/BOOTX64.EFI
RTX4080-EXPERIMENT/ASSETS/booter_load_ad102.bin
RTX4080-EXPERIMENT/ASSETS/v67-ad102-610.43.03-four-plm.bin
RTX4080-EXPERIMENT/ASSETS/gsp_ga10x.bin
RTX4080-EXPERIMENT/ASSETS/gsp_boot_ad102.bin
RTX4080-EXPERIMENT/ASSETS/gsp_boot_desc_ad102.bin
RTX4080-EXPERIMENT/ASSETS/NVIDIA-LICENSE
```

## Test and recovery

Before any test: save work and recovery credentials, ensure Windows is fully
decrypted with BitLocker protection off and Secure Boot already disabled. The
application does not change these settings. Keep Windows Boot Manager first and
use the firmware's **one-time USB boot menu** (F12 on the recorded machine).
Fully power off and start again; do not assume a warm restart is a cold GPU.

The app performs preflight, then waits up to 30 seconds for **U**. Esc/timeout
cancels. U releases the GPU's firmware display driver; the screen can go black.
One SEC2 launch is allowed. Inability to prove cleanup produces STOP and retains
DMA resources. **On STOP or no Windows return: physically power off, remove the
USB, then select Windows Boot Manager. Do not retry in the same power session.**
There is no fallback iGPU on the tested PC. Do not make this a permanent boot
default. Never interrupt a running attempt or hot-unplug the USB.

Logs are `RTX4080-EXPERIMENT/RUNxx/REPORT.TXT` and `LAST.TXT`. A three-attempt
budget and a root `ABORT.TXT` file provide bounds; do not reset the budget simply
to repeat a failed attempt. A clean Windows return alone does not prove unlocking:
inspect post-FLR/post-GOP selectors and compare a matched baseline workload.
Power loss and sleep can clear the volatile override. Nothing writes GPU flash.

## Offline tests and limitations

The private kit's captured PROM permits 43 simulated transaction tests plus direct
identity and override checks. Those private ROM bytes are intentionally absent
here; `project/test_ad107.py` accepts a user's own matching captured fixture and
local assets. Public source can be rebuilt and checked byte-for-byte without any
PROM image. Build verification does not test firmware execution or physical recovery.

Root `LICENSE` covers GPL-2.0-only project code; EDK2/NVIDIA/other separately
attributed components keep their licenses in `LICENSES/` and upstream notices.
Source references: [Zagitta/gpu-unlock](https://github.com/Zagitta/gpu-unlock),
[Windows-GPU-UNLOCK](https://github.com/impacifist/Windows-GPU-UNLOCK), and the
preserved AD103-derived port attribution. No GitHub repository has been created or
published by these packaging tools.
