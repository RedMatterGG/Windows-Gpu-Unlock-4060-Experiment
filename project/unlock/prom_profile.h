#ifndef GU_PROM_PROFILE_H
#define GU_PROM_PROFILE_H
/* RUN04 hardware dump: BAR0+0x300000 already begins at AD103.rom+0x9400.
 * PROM[0,0xd6c00) == full ROM[0x9400,0xe0000), byte for byte.
 * Share this mapping between preflight verification and FWSEC extraction. */
#define GU_PROM_BAR_OFFSET 0x300000U
#define GU_PROM_VIEW_BYTES 0xd6c00U
#define GU_PROM_VIEW_SHA256 "c7758cbd4351c18dd2187da503f6c719e1126fc47afced7c1790956caebab2c9"
#endif
