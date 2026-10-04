#!/usr/bin/env bash
# direk_3m.scad'dan baskı dosyalarını (stl/) ve önizlemeleri (onizleme/) üretir.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p stl onizleme
PARTS=(collar0 collar1 collar2 cap3 sleeve1 sleeve2 sleeve3 plug1 plug2 plug3 pad_2.5 pad_2.7 pad_2.9 pulley base drum)
for p in "${PARTS[@]}"; do
    echo "STL: $p"
    openscad --backend=manifold --export-format binstl -D "part=\"$p\"" -o "stl/$p.stl" direk_3m.scad 2>/dev/null
    openscad --backend=manifold --render -D "part=\"$p\"" --imgsize=600,600 --colorscheme=Tomorrow \
        --autocenter --viewall --camera=0,0,0,55,0,25,0 -o "onizleme/$p.png" direk_3m.scad 2>/dev/null
done
for xv in 0 600; do
    echo "Montaj x=$xv"
    openscad --backend=manifold --render -D 'part="assembly"' -D "x=$xv" --imgsize=700,1400 --colorscheme=Tomorrow \
        --autocenter --viewall --camera=0,0,0,70,0,35,0 -o "onizleme/montaj_x$xv.png" direk_3m.scad 2>/dev/null
done
# yakın plan: en üstteki iki yaka
openscad --backend=manifold --render -D 'part="assembly"' -D "x=0" --imgsize=900,900 --colorscheme=Tomorrow \
    --camera=0,0,1000,60,0,35,420 -o "onizleme/yakin_plan.png" direk_3m.scad 2>/dev/null
echo "Bitti."
