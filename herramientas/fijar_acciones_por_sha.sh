#!/usr/bin/env bash
# Sustituye referencias por etiqueta (@v6) por SHA de commit inmutable.
# SHA resueltos con `git ls-remote` el 21-09-2026. Dependabot los mantendrá.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
declare -A SHA=(
  ["actions/checkout@v6"]="d23441a48e516b6c34aea4fa41551a30e30af803 # v6.1.0"
  ["actions/upload-artifact@v6"]="b7c566a772e6b6bfb58ed0dc250532a479d7789f # v6.0.0"
  ["actions/download-artifact@v6"]="018cc2cf5baa6db3ef3c5f8a56943fffe632ef53 # v6.0.0"
  ["actions/download-artifact@v7"]="37930b1c2abaa49bbe596cd826c3c89aef350131 # v7.0.0"
  ["actions/setup-python@v6"]="ece7cb06caefa5fff74198d8649806c4678c61a1 # v6.3.0"
  ["docker/setup-buildx-action@v3"]="8d2750c68a42422c14e847fe6c8ac0403b4cbd6f # v3.12.0"
  ["docker/build-push-action@v6"]="10e90e3645eae34f1e60eeb005ba3a3d33f178e8 # v6.19.2"
  ["actions/upload-pages-artifact@v4"]="7b1f4a764d45c48632c6b24a0339c27f5614fb0b # v4.0.0"
  ["actions/deploy-pages@v4"]="d6db90164ac5ed86f2b6aed7e0febac5b3c0c03e # v4.0.5"
  ["actions/configure-pages@v5"]="983d7736d9b0ae728b81ab479565c72886d7745b # v5.0.0"
  ["actions/github-script@v7"]="f28e40c7f34bde8b3046d885e986cb6290c5673b # v7.1.0"
)
for ref in "${!SHA[@]}"; do
  repo="${ref%@*}"
  sed -i.bak -E "s|uses: ${ref}([[:space:]].*)?$|uses: ${repo}@${SHA[$ref]}|" .github/workflows/*.yml
done
rm -f .github/workflows/*.bak
echo "Referencias restantes sin SHA:"
grep -hn "uses: [^ ]*@v[0-9]" .github/workflows/*.yml || echo "  ninguna"
