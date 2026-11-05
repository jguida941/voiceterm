#!/bin/bash
# Does this terminal honor insert-line (CSI L) and delete-line (CSI M)?
printf '\033[2J\033[H'
for i in $(seq 1 15); do printf 'row %02d\n' "$i"; done
printf '\033[20;1H>>> MARKER ROW 20 (must end up on row 19 after the delete, back on 20 after the insert) <<<'
sleep 1.5
printf '\033[1;1H\033[M'            # delete row 1: rows 2..N shift up one
sleep 1.5
printf '\033[5;1H\033[L'            # insert a blank line at row 5: rows 5..N shift down one
printf '\033[22;1HRESULT: PASS if "row 01" is gone, a blank line sits at row 5, and the MARKER is back on row 20.\nPress Enter.\n'
read -r _
