#!/usr/bin/env bash
set -euo pipefail

# Activate venv if present
if [ -f "../realtime/bin/activate" ]; then
  # shellcheck disable=SC1091
  source ../realtime/bin/activate
fi

cd "$(dirname "$0")"

MONTHS="6"
PER_DAY="6"

while [[ $# -gt 0 ]]; do
  case $1 in
    --months) MONTHS="$2"; shift 2;;
    --per-day) PER_DAY="$2"; shift 2;;
    *) shift;;
  esac
done

echo "Seeding synthetic tweets: months=$MONTHS per-day=$PER_DAY"
python seed_fake_data.py --months "$MONTHS" --per-day "$PER_DAY"
echo "Done."


