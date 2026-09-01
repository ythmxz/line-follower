#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/setup_usb_network.sh"

EV3="ev3"
REMOTE_FILE="/home/robot/line-follower/config.json"
LOCAL_DIR="$(dirname "$SCRIPT_DIR")/src"

setup_usb_network

echo "Baixando config.json..."

scp "$EV3:$REMOTE_FILE" "$LOCAL_DIR/"

echo "Concluído."
