#!/bin/sh
# Kør alle tests: sh tests/run.sh   (kræver python3 + playwright og node/npm)
cd "$(dirname "$0")"
[ -d node_modules/leaflet ] || npm i -s leaflet@1.9.4 >/dev/null
for t in test_basis.py test_setup.py test_layer.py test_feat.py test_layout.py test_area.py test_private.py test_v2.py test_v3.py test_v4.py test_v5.py test_v6.py; do
  printf '%-16s ' "$t"; python3 -I "$t" 2>&1 | tail -1
done
