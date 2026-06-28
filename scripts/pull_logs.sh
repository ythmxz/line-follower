#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/setup_usb_network.sh"

EV3="robot@10.42.0.3"
REMOTE_DIR="/home/robot/line-follower/logs"
LOCAL_DIR="logs"

mkdir -p "$LOCAL_DIR"

setup_usb_network

echo "Baixando logs..."

scp -r "$EV3:$REMOTE_DIR/" "$LOCAL_DIR"

echo "Concluído."
