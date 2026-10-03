#!/usr/bin/env bash
# Jetson ilk açılış sonrası temel kurulum.
#
# Ne yapar:
#   1. Sistemi günceller (apt update + upgrade)
#   2. Geliştirme için temel paketleri kurar (git, python3-venv, v4l-utils ...)
#   3. JetPack bileşenleri (CUDA, TensorRT, cuDNN ...) eksikse nvidia-jetpack kurar
#   4. SSH sunucusunu açar
#   5. İsteğe bağlı: jtop (jetson-stats) kurar  -> --jtop
#
# Ne YAPMAZ: güç modunu, ağ ayarlarını, kullanıcıları veya diski değiştirmez.
# Birden fazla kez çalıştırılabilir; kurulu olanı yeniden kurmaz.
#
# Kullanım:
#   ./jetson/scripts/kurulum_sonrasi.sh            # temel kurulum
#   ./jetson/scripts/kurulum_sonrasi.sh --jtop     # + jtop

set -euo pipefail

INSTALL_JTOP=0
for arg in "$@"; do
    case "$arg" in
        --jtop) INSTALL_JTOP=1 ;;
        -h|--help) sed -n '2,17p' "$0"; exit 0 ;;
        *) echo "Bilinmeyen seçenek: $arg" >&2; exit 1 ;;
    esac
done

if [[ ! -e /etc/nv_tegra_release ]]; then
    echo "Bu betik Jetson üzerinde çalıştırılmalı." >&2
    exit 1
fi

log() { printf '\n\033[1;32m==> %s\033[0m\n' "$*"; }

log "Paket listesi güncelleniyor ve sistem yükseltiliyor"
sudo apt-get update
sudo DEBIAN_FRONTEND=noninteractive apt-get -y upgrade

log "Temel geliştirme paketleri kuruluyor"
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
    git curl wget nano htop tmux tree unzip \
    build-essential cmake pkg-config \
    python3-pip python3-venv python3-dev \
    v4l-utils \
    openssh-server

if dpkg-query -W -f='${Status}' nvidia-jetpack 2>/dev/null | grep -q "install ok installed"; then
    log "nvidia-jetpack zaten kurulu: $(dpkg-query -W -f='${Version}' nvidia-jetpack)"
else
    log "nvidia-jetpack kuruluyor (CUDA, TensorRT, cuDNN, VPI ...). Bu adım uzun sürebilir"
    sudo DEBIAN_FRONTEND=noninteractive apt-get install -y nvidia-jetpack
fi

log "SSH sunucusu etkinleştiriliyor"
sudo systemctl enable --now ssh

# CUDA araçlarını kullanıcının PATH'ine ekle (yalnız bir kez)
if ! grep -q "/usr/local/cuda/bin" "$HOME/.bashrc"; then
    log "CUDA yolları ~/.bashrc dosyasına ekleniyor"
    {
        echo ''
        echo '# CUDA (kurulum_sonrasi.sh tarafından eklendi)'
        echo 'export PATH=/usr/local/cuda/bin${PATH:+:${PATH}}'
        echo 'export LD_LIBRARY_PATH=/usr/local/cuda/lib64${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}'
    } >> "$HOME/.bashrc"
fi

if [[ $INSTALL_JTOP -eq 1 ]]; then
    log "jtop (jetson-stats) kuruluyor"
    # Ubuntu 24.04 (JetPack 7) sistem pip'ini PEP 668 ile kilitliyor; jetson-stats
    # bir systemd servisi kurduğu için sistem genelinde kurulması gerekiyor.
    if sudo pip3 install -U jetson-stats 2>/dev/null; then
        :
    else
        sudo pip3 install -U --break-system-packages jetson-stats
    fi
    echo "jtop servisinin başlaması için oturumu kapatıp açın veya yeniden başlatın."
fi

log "Bitti. Şimdi sağlık kontrolünü çalıştırın: ./jetson/scripts/saglik_kontrolu.sh"
