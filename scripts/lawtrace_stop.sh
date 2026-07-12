#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PID_FILE="$ROOT/apps/lawtrace/.lawtrace-preview.pid"
PORT_FILE="$ROOT/apps/lawtrace/.lawtrace-preview.port"

if [[ -f "$PID_FILE" ]]; then
  pid="$(cat "$PID_FILE" || true)"
  if [[ -n "${pid:-}" ]] && kill -0 "$pid" 2>/dev/null; then
    kill "$pid" 2>/dev/null || true
    sleep 0.3
    echo "Stopped LawTrace preview (pid $pid)"
  else
    echo "No running LawTrace preview process"
  fi
  rm -f "$PID_FILE"
else
  echo "No LawTrace preview pid file"
fi
rm -f "$PORT_FILE"
# Best-effort: free common ports left by orphaned servers we own
for p in 3010 3011 3012; do
  if command -v lsof >/dev/null 2>&1; then
    lsof -tiTCP:"$p" -sTCP:LISTEN 2>/dev/null | while read -r opid; do
      # only kill if cmdline mentions lawtrace_static_server
      if tr '\0' ' ' <"/proc/$opid/cmdline" 2>/dev/null | grep -q lawtrace_static_server; then
        kill "$opid" 2>/dev/null || true
        echo "Stopped orphan lawtrace_static_server on :$p (pid $opid)"
      fi
    done
  fi
done
