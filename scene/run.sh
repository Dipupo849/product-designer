#!/usr/bin/env bash
BL="/c/Users/USER/AppData/Local/Temp/bl/blender-5.2.1-windows-x64/blender.exe"
MODE="${1:-preview}"
shift || true
for spec in "$@"; do
  drv="${spec%%:*}"; shot="${spec##*:}"
  script="render_couch.py"; [ "$drv" = "p" ] && script="render_param.py"
  t0=$(date +%s)
  if [ "$MODE" = "final" ]; then
    "$BL" -b -P "$script" -- "$shot" > "logs/${drv}_${shot}.log" 2>&1
  else
    "$BL" -b -P "$script" -- "$shot" preview > "logs/${drv}_${shot}.log" 2>&1
  fi
  rc=$?
  t1=$(date +%s)
  grep -q "Traceback" "logs/${drv}_${shot}.log" && rc=1
  if [ $rc -ne 0 ]; then
    echo "FAIL  ${drv}:${shot}  ($((t1-t0))s)"
    grep -E "Error|Traceback|line [0-9]+, in" "logs/${drv}_${shot}.log" | head -6
  else
    echo "ok    ${drv}:${shot}  $((t1-t0))s"
  fi
done
echo "BATCH DONE"
