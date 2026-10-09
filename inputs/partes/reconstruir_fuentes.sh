#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
sha256sum -c MANIFEST_PARTES.sha256
cat seccionado_2025.zip.part00 seccionado_2025.zip.part01 seccionado_2025.zip.part02 > ../seccionado_2025.zip
cat 65034.csv.zip.part00 65034.csv.zip.part01 65034.csv.zip.part02 65034.csv.zip.part03 > ../65034.csv.zip
printf '%s  %s\n' \
  '55c9da7e34d3bb3cb725400c35b58e72f4db2ea8321ef91237a89e708d2dbcc4' '../seccionado_2025.zip' \
  '91d3ff9a90bac1c06e26df97179daa325b65fa77c9209879d6a40333b17057f3' '../65034.csv.zip' | sha256sum -c -
echo 'Fuentes reconstruidas y verificadas.'
