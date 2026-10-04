#!/usr/bin/env bash
# mini_direk.scad'dan baskı dosyalarını (stl/) ve önizlemeleri (onizleme/) üretir.
# Ölçü değiştirdikten sonra yeniden çalıştırın:  ./build.sh
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p stl onizleme

PARTS=(tube0 tube1 tube2 tube3 collar0 collar1 collar2 cap3 pulley stand drum)
for p in "${PARTS[@]}"; do
    echo "STL: $p"
    openscad --backend=manifold --export-format binstl -D "part=\"$p\"" -o "stl/$p.stl" mini_direk.scad 2>/dev/null
    openscad --backend=manifold --render -D "part=\"$p\"" --imgsize=600,600 --colorscheme=Tomorrow \
        --autocenter --viewall --camera=0,0,0,55,0,25,0 -o "onizleme/$p.png" mini_direk.scad 2>/dev/null
done

for xv in 0 125; do
    echo "Montaj x=$xv"
    openscad --backend=manifold --render -D 'part="assembly"' -D "x=$xv" --imgsize=900,1200 --colorscheme=Tomorrow \
        --autocenter --viewall --camera=0,0,0,70,0,35,0 -o "onizleme/montaj_x$xv.png" mini_direk.scad 2>/dev/null
done
echo "Bitti."
