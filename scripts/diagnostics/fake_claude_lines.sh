#!/bin/bash
# A child that believes it has N rows and streams more lines than fit, like Claude streaming an answer.
printf '\033[2J\033[H'
for i in $(seq 1 40); do printf 'answer line %02d\n' "$i"; sleep 0.08; done
sleep 4
