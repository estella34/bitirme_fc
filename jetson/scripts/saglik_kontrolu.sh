#!/usr/bin/env bash
# Jetson temel sağlık kontrolü (Aşama B çıktısı).
#
# Kartın modelini, belleğini, Jetson Linux / JetPack sürümünü, depolamayı,
# güç modunu, CUDA/TensorRT/OpenCV durumunu, kameraları ve ağı tek bir
# Markdown raporunda toplar. Sistemde hiçbir şeyi değiştirmez.
#
# Kullanım:
#   ./jetson/scripts/saglik_kontrolu.sh              # rapor jetson/kayitlar/ altına yazılır
#   ./jetson/scripts/saglik_kontrolu.sh -o /tmp      # başka klasöre yaz
#
# sudo parolası sorulabilir: önyükleyici (QSPI) sürümü ve güç modu yalnız
# yetkiyle okunabiliyor. Parola verilmezse o satırlar "okunamadı" olur.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT_DIR="${SCRIPT_DIR}/../kayitlar"

while getopts "o:h" opt; do
    case "$opt" in
        o) OUT_DIR="$OPTARG" ;;
        h) sed -n '2,13p' "$0"; exit 0 ;;
        *) exit 1 ;;
    esac
done

if [[ ! -e /etc/nv_tegra_release && ! -e /proc/device-tree/model ]]; then
    echo "Bu betik Jetson üzerinde çalıştırılmalı." >&2
    exit 1
fi

mkdir -p "$OUT_DIR"
HOST="$(hostname)"
STAMP="$(date +%Y%m%d-%H%M)"
REPORT="$(cd "$OUT_DIR" && pwd)/saglik-${HOST}-${STAMP}.md"

# sudo gerektiren komutlar için parolayı bir kez iste; olmazsa devam et.
HAS_SUDO=0
if sudo -n true 2>/dev/null || sudo -v 2>/dev/null; then
    HAS_SUDO=1
fi

run() {  # komutu çalıştır, çıktı yoksa/başarısızsa not düş
    local out
    out="$("$@" 2>&1)" && [[ -n "$out" ]] && { echo "$out"; return; }
    echo "(okunamadı: $*)"
}

run_sudo() {
    if [[ $HAS_SUDO -eq 1 ]]; then run sudo "$@"; else echo "(sudo yok, atlandı: $*)"; fi
}

section() { printf '\n## %s\n\n```text\n' "$1"; }
end_section() { printf '```\n'; }

{
    echo "# Jetson sağlık kontrolü — ${HOST}"
    echo
    echo "- Tarih: $(date '+%Y-%m-%d %H:%M:%S %Z')"
    echo "- Betik: \`jetson/scripts/saglik_kontrolu.sh\`"

    section "Kart"
    echo "Model     : $(tr -d '\0' < /proc/device-tree/model 2>/dev/null || echo '?')"
    echo "Uyumluluk : $(tr '\0' ' ' < /proc/device-tree/compatible 2>/dev/null || echo '?')"
    echo "Seri no   : $(tr -d '\0' < /proc/device-tree/serial-number 2>/dev/null || echo '?')"
    end_section

    section "Bellek"
    run free -h
    end_section

    section "Jetson Linux (L4T) / JetPack"
    run cat /etc/nv_tegra_release
    echo
    run dpkg-query -W -f='${Package} ${Version}\n' nvidia-l4t-core nvidia-jetpack
    echo
    run lsb_release -ds
    echo "Çekirdek: $(uname -r)"
    end_section

    section "Önyükleyici (QSPI/UEFI) sürümü"
    # Çıktıdaki "Current version" satırı firmware sürümüdür.
    run_sudo nvbootctrl dump-slots-info
    end_section

    section "Depolama"
    echo "Kök dosya sistemi: $(findmnt -n -o SOURCE /)"
    echo
    run lsblk -o NAME,SIZE,TYPE,MODEL,MOUNTPOINTS
    echo
    run df -h -x tmpfs -x devtmpfs -x squashfs
    end_section

    section "Güç modu"
    run_sudo nvpmodel -q
    end_section

    section "Sıcaklıklar (°C)"
    for z in /sys/class/thermal/thermal_zone*; do
        [[ -r "$z/temp" ]] || continue
        printf '%-14s %s\n' "$(cat "$z/type")" "$(awk '{printf "%.1f", $1/1000}' "$z/temp")"
    done
    end_section

    section "CUDA / TensorRT / cuDNN"
    if [[ -x /usr/local/cuda/bin/nvcc ]]; then
        /usr/local/cuda/bin/nvcc --version | tail -n 2
    else
        echo "nvcc bulunamadı (CUDA kurulu değil veya PATH dışında)"
    fi
    echo
    dpkg -l 2>/dev/null | awk '/^ii/ && ($2 ~ /^(tensorrt|libnvinfer[0-9]*|libcudnn[0-9]*|cuda-toolkit)/) {print $2, $3}' \
        || true
    end_section

    section "Python ve OpenCV"
    echo "Python: $(python3 --version 2>&1)"
    python3 - <<'PY' 2>&1 || true
try:
    import cv2
    info = cv2.getBuildInformation()
    gst = next((l.strip() for l in info.splitlines() if "GStreamer" in l), "GStreamer: ?")
    cuda = next((l.strip() for l in info.splitlines() if l.strip().startswith("NVIDIA CUDA")), "NVIDIA CUDA: ?")
    print("OpenCV:", cv2.__version__)
    print(gst)
    print(cuda)
except Exception as e:
    print("OpenCV içe aktarılamadı:", e)
PY
    end_section

    section "Kameralar"
    echo "/dev/video* aygıtları:"
    ls -1 /dev/video* 2>/dev/null || echo "(hiç yok)"
    echo
    if command -v v4l2-ctl >/dev/null; then
        run v4l2-ctl --list-devices
    else
        echo "v4l2-ctl yok (v4l-utils paketi kurulmamış)"
    fi
    echo
    echo "nvargus-daemon: $(systemctl is-active nvargus-daemon 2>/dev/null || echo '?')"
    end_section

    section "Ağ"
    echo "Hostname : ${HOST}"
    echo "IP       : $(hostname -I 2>/dev/null)"
    echo "SSH      : $(systemctl is-active ssh 2>/dev/null || echo '?')"
    echo "İnternet : $(ping -c1 -W2 8.8.8.8 >/dev/null 2>&1 && echo erişilebilir || echo erişilemiyor)"
    end_section
} > "$REPORT"

echo "Rapor yazıldı: $REPORT"
