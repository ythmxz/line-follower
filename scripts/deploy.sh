#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/setup_usb_network.sh"

EV3="ev3"
REMOTE_DIR="/home/robot/line-follower"

setup_usb_network

SRC_DIR="$(dirname "$SCRIPT_DIR")/src"

# Resolve os arquivos em src/
files=()
if [ "$#" -eq 0 ]; then
    while IFS= read -r -d '' path; do
        files+=("$path")
    done < <(find "$SRC_DIR" -maxdepth 1 -type f -print0)
else
    for arg in "$@"; do
        path="$SRC_DIR/$arg"
        if [ ! -f "$path" ]; then
            echo "Arquivo não encontrado: $path"
            exit 1
        fi
        files+=("$path")
    done
fi

scp "${files[@]}" "$EV3:$REMOTE_DIR/"

for file in "${files[@]}"; do
    ssh "$EV3" "chmod +x '$REMOTE_DIR/$(basename "$file")'"
done

echo "Concluído."
