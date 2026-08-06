#!/usr/bin/env bash
# The terminal cast that docs/demo.tape records. Run from the repo root:
#   bash docs/demo.sh
# Both replies are printed from examples/debug-report/ — nothing here is
# hand-written demo copy.
set -u
export LANG=C.UTF-8

GRN=$'\e[32m'
BOLD=$'\e[1m'
DIM=$'\e[2m'
RST=$'\e[0m'

# Sleep without spawning a process per call (WSL process spawn is slow enough
# to wreck per-character pacing). The read-write open keeps the fifo from EOF.
exec 3<> <(:)
nap() { read -rst "$1" -u 3 _ || :; }

type_out() { # typewriter-print stdin, one char per $1 seconds
  local delay="$1" c
  while IFS= read -r -N1 c; do
    printf '%s' "$c"
    nap "$delay"
  done
}

question() { # $1 = "typed" | "instant"
  printf '%s❯ %s' "$GRN" "$RST$BOLD"
  if [ "$1" = typed ]; then
    printf 'ok what did you find?' | type_out 0.05
  else
    printf 'ok what did you find?'
  fi
  printf '%s\n\n' "$RST"
}

clear
nap 0.8
question typed
nap 0.8

printf '%s── without grokkable-output ────────────────────────────────────────────%s\n\n' "$DIM" "$RST"
fold -s -w 76 examples/debug-report/before.md | while IFS= read -r line; do
  printf '%s\n' "$line"
  nap 0.04
done
nap 2.5

clear
question instant
printf '%s── with grokkable-output ───────────────────────────────────────────────%s\n\n' "$DIM" "$RST"
head -n1 examples/debug-report/after.md | fold -s -w 76 | type_out 0.011
printf '\n\n'
nap 1.2
printf '%s— you can stop reading here.%s\n' "$DIM" "$RST"

# Hold the final frame; vhs stops capturing on its own schedule before this ends.
nap 30
