#!/usr/bin/env bash
set -e

EV3="robot@10.42.0.3"
REMOTE_DIR="/home/robot/line-follower"

if [ "$#" -eq 0 ]; then
    echo "Uso: $0 arquivo1.py [arquivo2.py ...]"
    exit 1
fi

scp "$@" "$EV3:$REMOTE_DIR/"

for file in "$@"; do
    ssh "$EV3" "chmod +x '$REMOTE_DIR/$(basename "$file")'"
done

echo "Concluído."
