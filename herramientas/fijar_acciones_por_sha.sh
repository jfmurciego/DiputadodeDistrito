#!/usr/bin/env bash
# Sustituye referencias por etiqueta por SHA de commit inmutable.
# SHA actualizados el 06-10-2026; Dependabot los mantendrá.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
declare -A SHA=(
  ["actions/checkout@v7"]="3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1"
  ["actions/upload-artifact@v7"]="043fb46d1a93c77aae656e7c1c64a875d1fc6a0a # v7.0.1"
  ["actions/download-artifact@v8"]="3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c # v8.0.1"
  ["actions/setup-python@v7"]="5fda3b95a4ea91299a34e894583c3862153e4b97 # v7.0.0"
  ["docker/setup-buildx-action@v4"]="f87e5991a6d7451dcb8d9637bfbc97413f497069 # v4.4.1"
  ["docker/build-push-action@v7"]="c3c9e263c25d99ce0380d002d59b67737d91b0dc # v7.4.0"
  ["actions/upload-pages-artifact@v5"]="fc324d3547104276b827a68afc52ff2a11cc49c9 # v5.0.0"
  ["actions/deploy-pages@v5"]="368f82528645a54fb793d4d04e342629a3f51346 # v5.0.1"
  ["actions/configure-pages@v6"]="45bfe0192ca1faeb007ade9deae92b16b8254a0d # v6.0.0"
  ["actions/github-script@v9"]="3a2844b7e9c422d3c10d287c895573f7108da1b3 # v9.0.0"
)
for ref in "${!SHA[@]}"; do
  repo="${ref%@*}"
  sed -i.bak -E "s|uses: ${ref}([[:space:]].*)?$|uses: ${repo}@${SHA[$ref]}|" .github/workflows/*.yml
done
rm -f .github/workflows/*.bak
echo "Referencias restantes sin SHA:"
grep -hn "uses: [^ ]*@v[0-9]" .github/workflows/*.yml || echo "  ninguna"
