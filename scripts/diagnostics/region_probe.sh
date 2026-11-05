#!/bin/bash
# Does this terminal honor a scroll region (DECSTBM), keep rows outside it fixed,
# and keep the region after a DEC cursor save/restore (ESC 7 / ESC 8)?
printf '\033[2J\033[H'
printf '\033[12;1H>>> FOOTER ROW 12: this line must stay exactly here <<<'
printf '\033[1;10r'                       # region rows 1..10
printf '\033[1;1H'
for i in $(seq 1 13); do printf 'line %02d\n' "$i"; sleep 0.12; done
printf '\0337'                             # DECSC
printf '\033[14;1HROW 14: written while the region is active'
printf '\0338'                             # DECRC
for i in 14 15 16; do printf 'line %02d (after restore)\n' "$i"; sleep 0.12; done
printf '\033[r'                            # reset region
printf '\033[16;1HRESULT: PASS if lines stayed inside rows 1-10 the whole time and the FOOTER never moved.\n'
printf 'FAIL if the FOOTER moved, or if lines 14-16 pushed everything up after the restore. Press Enter.\n'
read -r _
