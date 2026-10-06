#!/data/data/com.termux/files/usr/bin/bash
set -e
pkg update -y
pkg install -y python
python -m pip install -e . pytest
mkdir -p data
cp -n .env.example .env || true
echo "Installed. Edit .env locally, then: ./run.sh --health"
