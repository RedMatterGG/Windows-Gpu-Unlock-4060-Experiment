/* SPDX-License-Identifier: GPL-2.0-only */
/* Exercise the exact static checks that rejected RUN03; all IO is simulated. */
#define main original_fixture_main
#include "test_efi_transaction.c"
#undef main
#include "../vendor/unlock_610.c"

int main(void) {
  setup(SUCCESS);
  CHECK(GuTargetConfig((UINT32 *)config,0,7,0,0));
  CHECK(!GuTargetConfig((UINT32 *)config,1,7,0,0));
  *(UINT32 *)(config+0x2c)=0x179510de;
  CHECK(!GuTargetConfig((UINT32 *)config,0,7,0,0));
  *(UINT32 *)(config+0x2c)=GU_BOARD_SUBSYSTEM;
  struct pci_dev device={0};
  struct unlock_transaction_work work={.pdev=&device,.bar=(void *)(UINTN)Gu.bar_base,.bar_len=sizeof(registers),.mapped=true};
  UINT32 value;
  CHECK(!read_target_plm(&work,PLM,&value) && value==0xffffff8f);
  registers[PLM/4]=0xffffffff;
  CHECK(!read_target_plm(&work,PLM,&value) && value==0xffffffff);
  registers[PLM/4]=0xbadf5620;
  CHECK(read_target_plm(&work,PLM,&value)==-ENODEV);
  registers[PLM/4]=0xffffff8f;
  registers[0]=0x193000a1;
  CHECK(read_target_plm(&work,PLM,&value)==-ENODEV);
  CHECK(sec2_restore_falcon_access(&work)==-ENODEV && !fake.mmio_writes);
  registers[0]=GU_BOARD_CHIP;
  *(UINT32 *)config=0x270410de;
  CHECK(read_target_plm(&work,PLM,&value)==-ENODEV);
  *(UINT32 *)config=GU_BOARD_ID;
  GuStarted();
  CHECK(!sec2_restore_falcon_access(&work));
  CHECK(registers[(SEC2+0x84)/4]==GU_BOARD_CHIP);
  CHECK(!fake.gsp_starts && !fake.sec2_starts && !fake.flrs && !fake.maps);
  puts("AD107 identity checks passed: board/subsystem, exact chip/PCI, all-ones PLM, sentinel rejection, Falcon RM identity; simulated IO only.");
  return 0;
}
