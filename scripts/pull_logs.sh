#!/usr/bin/env bash
set -e

EV3="robot@10.42.0.3"
REMOTE_DIR="/home/robot/line-follower/logs"
LOCAL_DIR="logs"

mkdir -p "$LOCAL_DIR"

echo "Baixando logs..."

scp -r "$EV3:$REMOTE_DIR/" "$LOCAL_DIR"

echo "Concluído."
