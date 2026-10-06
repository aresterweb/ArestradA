#!/data/data/com.termux/files/usr/bin/bash
set -a
[ -f .env ] && . ./.env
set +a
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
python -m arestrada.main "$@"
