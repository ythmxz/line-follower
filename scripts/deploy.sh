#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/setup_usb_network.sh"

EV3="ev3"
REMOTE_DIR="/home/robot/line-follower"

setup_usb_network

# Garante que os diretórios necessários existam no EV3
ssh "$EV3" "mkdir -p '$REMOTE_DIR/controllers' '$REMOTE_DIR/logs/calibration' '$REMOTE_DIR/logs/on_off' '$REMOTE_DIR/logs/proportional' '$REMOTE_DIR/logs/pid'"

SRC_DIR="$(dirname "$SCRIPT_DIR")/src"

# Resolve os arquivos em src/
files=()
if [ "$#" -eq 0 ]; then
    while IFS= read -r -d '' path; do
        files+=("$path")
    done < <(find "$SRC_DIR" -mindepth 1 -maxdepth 1 -print0)
else
    for arg in "$@"; do
        path="$SRC_DIR/$arg"
        if [ ! -e "$path" ]; then
            echo "Arquivo ou diretório não encontrado: $path"
            exit 1
        fi
        files+=("$path")
    done
fi

scp -r "${files[@]}" "$EV3:$REMOTE_DIR/"

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        ssh "$EV3" "chmod +x '$REMOTE_DIR/$(basename "$file")'"
    fi
done

echo "Concluído."
