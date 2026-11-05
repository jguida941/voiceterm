#!/bin/bash
# Same probe, but inside the alternate screen (what Codex uses). Does this
# terminal mode honor absolute positioning and a scroll region there?
printf '\033[?1049h\033[2J\033[H'
printf '\033[12;1H>>> FOOTER ROW 12: this line must stay exactly here <<<'
printf '\033[1;10r'
printf '\033[1;1H'
for i in $(seq 1 13); do printf 'line %02d\n' "$i"; sleep 0.12; done
printf '\0337'
printf '\033[14;1HROW 14: written while the region is active'
printf '\0338'
for i in 14 15 16; do printf 'line %02d (after restore)\n' "$i"; sleep 0.12; done
printf '\033[r'
printf '\033[16;1HRESULT: PASS = lines stayed in rows 1-10 and the FOOTER is on row 12 above this text.\n'
printf 'Take a screenshot now, then press Enter to leave the alternate screen.\n'
read -r _
printf '\033[?1049l'
