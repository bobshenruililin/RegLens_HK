#!/usr/bin/env bash
# Start LawTrace production preview with correct static routing.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

MODE="${1:-auto}"   # auto | demo | local
PORT="${LAWTRACE_PORT:-}"
PID_FILE="$ROOT/apps/lawtrace/.lawtrace-preview.pid"
PORT_FILE="$ROOT/apps/lawtrace/.lawtrace-preview.port"
LOG_FILE="$ROOT/apps/lawtrace/.lawtrace-preview.log"

die() { echo "ERROR: $*" >&2; exit 1; }

command -v python3 >/dev/null || die "python3 is required"
command -v npm >/dev/null || die "npm is required"
command -v node >/dev/null || die "node is required"

# Stop any previous LawTrace preview we started
if [[ -f "$PID_FILE" ]]; then
  oldpid="$(cat "$PID_FILE" || true)"
  if [[ -n "${oldpid:-}" ]] && kill -0 "$oldpid" 2>/dev/null; then
    kill "$oldpid" 2>/dev/null || true
    sleep 0.5
  fi
  rm -f "$PID_FILE"
fi

pick_port() {
  local p
  for p in ${PORT:-} 3010 3011 3012 3020 3030; do
    [[ -z "$p" ]] && continue
    if python3 - "$p" <<'PY'
import socket, sys
port=int(sys.argv[1])
s=socket.socket(); s.settimeout(0.2)
try:
    s.connect(("127.0.0.1", port)); s.close(); sys.exit(1)  # in use
except Exception:
    sys.exit(0)  # free
PY
    then
      echo "$p"
      return 0
    fi
  done
  die "No free port in 3010–3030; set LAWTRACE_PORT"
}

EXTRACT="$ROOT/data/lawtrace/extracted/cap599g"
HAS_599G=0
if [[ -d "$EXTRACT" ]] && find "$EXTRACT" -name '*.xml' 2>/dev/null | grep -q .; then
  HAS_599G=1
fi

if [[ "$MODE" == "auto" ]]; then
  if [[ "$HAS_599G" == "1" ]]; then MODE=local; else MODE=demo; fi
fi

echo "LawTrace open mode: $MODE"

# Allow restart without full rebuild when out/ is already valid.
SKIP_BUILD="${LAWTRACE_SKIP_BUILD:-0}"

if [[ "$SKIP_BUILD" != "1" ]]; then
if [[ "$MODE" == "local" ]]; then
  [[ "$HAS_599G" == "1" ]] || die "Cap. 599G extracts missing at $EXTRACT (see docs/LAWTRACE_OPERATIONS.md)"
  echo "Exporting complete Cap. 599G local-real web data…"
  make lawtrace-web-data-local
  echo "Building static site with Cap. 599G + local review workspace…"
  rm -rf apps/lawtrace/app/review apps/lawtrace/app/audit
  mkdir -p apps/lawtrace/app/review
  cp apps/lawtrace/optional/review/page.tsx apps/lawtrace/app/review/page.tsx
  (
    cd apps/lawtrace
    if [[ ! -d node_modules ]]; then npm ci; fi
    LAWTRACE_LOCAL_REVIEW=1 npm run typecheck
    LAWTRACE_LOCAL_REVIEW=1 npm run build
  )
  rm -rf apps/lawtrace/app/review
elif [[ "$MODE" == "demo" ]]; then
  echo "Exporting Cap. 614 demo web data…"
  make lawtrace-web-data
  echo "Building demo static site…"
  rm -rf apps/lawtrace/app/review apps/lawtrace/app/audit
  (
    cd apps/lawtrace
    if [[ ! -d node_modules ]]; then npm ci; fi
    npm run typecheck
    npm run build
  )
else
  die "Unknown mode: $MODE (use auto|demo|local)"
fi
else
  echo "LAWTRACE_SKIP_BUILD=1 — using existing apps/lawtrace/out"
fi

test -f apps/lawtrace/out/index.html || die "Build failed: apps/lawtrace/out/index.html missing"

PORT="$(pick_port)"
echo "$PORT" > "$PORT_FILE"

nohup python3 "$ROOT/scripts/lawtrace_static_server.py" \
  --dir "$ROOT/apps/lawtrace/out" \
  --host 127.0.0.1 \
  --port "$PORT" \
  >"$LOG_FILE" 2>&1 &
echo $! > "$PID_FILE"
sleep 0.8
kill -0 "$(cat "$PID_FILE")" 2>/dev/null || die "Preview server failed to start; see $LOG_FILE"

URL="http://127.0.0.1:${PORT}/"
echo ""
echo "=============================================="
echo "LawTrace HK is ready"
echo "Open: $URL"
echo "=============================================="
echo "Mode: $MODE"
echo "Stop: make lawtrace-stop"
echo "Log:  $LOG_FILE"

# Open browser when possible (may be a no-op in headless agents)
if command -v xdg-open >/dev/null 2>&1; then
  xdg-open "$URL" >/dev/null 2>&1 || true
elif command -v open >/dev/null 2>&1; then
  open "$URL" >/dev/null 2>&1 || true
fi

# Keep script useful when invoked interactively; for make, exit 0 after start
exit 0
