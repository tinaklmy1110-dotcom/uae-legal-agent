#!/usr/bin/env bash
set -euo pipefail

echo "[render_boot] starting container for ${RENDER_SERVICE_NAME:-local} (commit ${RENDER_GIT_COMMIT:-unknown})"

if [[ "${RUN_SEED_ON_BOOT:-1}" == "1" ]]; then
  echo "[render_boot] RUN_SEED_ON_BOOT=${RUN_SEED_ON_BOOT:-1} → loading seed_samples.json"
  python -m backend.utils.seed_loader data/seed_samples.json
  echo "[render_boot] seed loader finished"
else
  echo "[render_boot] RUN_SEED_ON_BOOT=${RUN_SEED_ON_BOOT:-0} → skipping seed loader"
fi

echo "[render_boot] launching uvicorn"
exec uvicorn backend.main:app --host 0.0.0.0 --port "${PORT:-8000}"
