#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/setup_usb_network.sh"

EV3="ev3"
REMOTE_DIR="/home/robot/line-follower"
LOCAL_LOGS="$(dirname "$SCRIPT_DIR")/logs"

setup_usb_network

echo "Apagando logs do EV3..."
ssh "$EV3" "rm -rf '$REMOTE_DIR/logs'"

echo "Enviando logs do repositório..."
scp -r "$LOCAL_LOGS" "$EV3:$REMOTE_DIR/"

echo "Concluído."
