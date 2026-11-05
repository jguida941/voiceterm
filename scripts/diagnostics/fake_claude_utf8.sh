#!/bin/bash
# Draws a rule of box-drawing characters, but one character's bytes straddle a
# pause, so VoiceTerm's PTY reader delivers them in two chunks.
printf '\033[2J\033[H'
printf 'rule: \xe2\x94\x80\xe2\x94\x80\xe2\x94'      # two full "─" then 2 of 3 bytes of the third
sleep 7
printf '\x80\xe2\x94\x80\xe2\x94\x80\xe2\x94\x80 end'  # final byte, then more "─"
sleep 5
