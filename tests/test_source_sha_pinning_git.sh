#!/usr/bin/env bash
set -euo pipefail

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

git -C "$tmp" init -b main >/dev/null
git -C "$tmp" config user.name "DDD Test"
git -C "$tmp" config user.email "ddd-test@example.invalid"

printf 'contract-A\n' > "$tmp/contract.txt"
git -C "$tmp" add contract.txt
git -C "$tmp" commit -m A >/dev/null
source_sha="$(git -C "$tmp" rev-parse HEAD)"

printf 'contract-B\n' > "$tmp/contract.txt"
git -C "$tmp" add contract.txt
git -C "$tmp" commit -m B >/dev/null
main_after_advance="$(git -C "$tmp" rev-parse main)"

[[ "$main_after_advance" != "$source_sha" ]] || {
  echo "::error::main no avanzó respecto del SHA inicial"
  exit 1
}

git -C "$tmp" checkout --detach "$source_sha" >/dev/null 2>&1

[[ "$(git -C "$tmp" rev-parse HEAD)" == "$source_sha" ]] || {
  echo "::error::checkout por SHA no conservó el commit inicial"
  exit 1
}
[[ "$(cat "$tmp/contract.txt")" == "contract-A" ]] || {
  echo "::error::el contrato del checkout fijado cambió tras avanzar main"
  exit 1
}
[[ "$(git -C "$tmp" rev-parse main)" == "$main_after_advance" ]] || {
  echo "::error::la simulación no conserva el avance independiente de main"
  exit 1
}

printf 'source_sha=%s\nmain_after_advance=%s\ncontract=contract-A\n' "$source_sha" "$main_after_advance"
