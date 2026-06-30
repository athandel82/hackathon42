#!/usr/bin/env bash
#
# start.sh — build and (re)start the "Still Defined Vehicle" frontend as a
# self-healing live preview on this machine.
#
# Properties:
#   • Idempotent: safe to re-run. It rewrites the systemd unit and restarts the
#     service cleanly, killing any stray manually-started preview first.
#   • Auto-restarting: the app runs under systemd with Restart=always, so it
#     comes back automatically if it crashes (and on reboot, since it's enabled).
#
# Usage:
#   ./start.sh            # build + (re)start on port 80
#   PORT=8080 ./start.sh  # use a different port
#   SKIP_BUILD=1 ./start.sh   # restart without rebuilding
#
set -euo pipefail

# --- configuration ----------------------------------------------------------
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_NAME="sdv-frontend"
PORT="${PORT:-80}"
RUN_USER="${SUDO_USER:-$(id -un)}"
NODE_BIN="$(command -v node || echo /usr/bin/node)"
VITE_JS="${APP_DIR}/node_modules/vite/bin/vite.js"
UNIT_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

log() { printf '\033[1;36m[start.sh]\033[0m %s\n' "$*"; }
die() { printf '\033[1;31m[start.sh] ERROR:\033[0m %s\n' "$*" >&2; exit 1; }

# sudo wrapper — use sudo only if we are not already root.
SUDO=""
if [[ "$(id -u)" -ne 0 ]]; then
  command -v sudo >/dev/null 2>&1 || die "sudo is required to manage the systemd service."
  SUDO="sudo"
fi

# --- preflight ---------------------------------------------------------------
[[ -x "$NODE_BIN" ]] || die "node not found (looked at: $NODE_BIN)"
command -v systemctl >/dev/null 2>&1 || die "systemctl not found; this host does not use systemd."

cd "$APP_DIR"

# Install dependencies if missing.
if [[ ! -d node_modules ]]; then
  log "Installing dependencies (node_modules missing)…"
  npm install
fi

# Build the production bundle so the preview serves the latest code.
if [[ "${SKIP_BUILD:-0}" != "1" ]]; then
  log "Building production bundle…"
  npm run build
else
  log "SKIP_BUILD=1 set — skipping build."
fi
[[ -f "${APP_DIR}/dist/index.html" ]] || die "dist/index.html not found — build did not produce output."
[[ -f "$VITE_JS" ]] || die "vite not found at $VITE_JS — run 'npm install'."

# --- stop anything currently holding the port -------------------------------
# Kill stray, manually-started preview processes (not managed by systemd) so the
# service can bind the port. (Ignore failures — there may be none.)
log "Stopping any stray 'vite preview' processes…"
$SUDO pkill -f "vite(\.js)? preview" 2>/dev/null || true
sleep 1

# --- write / refresh the systemd unit ---------------------------------------
log "Writing systemd unit ${UNIT_FILE}…"
$SUDO tee "$UNIT_FILE" >/dev/null <<UNIT
[Unit]
Description=SDV (Still Defined Vehicle) frontend live preview
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=${RUN_USER}
WorkingDirectory=${APP_DIR}
ExecStart=${NODE_BIN} ${VITE_JS} preview --host 0.0.0.0 --port ${PORT} --strictPort
# Self-healing: always restart on exit/crash, with a short backoff.
Restart=always
RestartSec=2
# Allow binding privileged ports (e.g. 80) without running as full root.
AmbientCapabilities=CAP_NET_BIND_SERVICE

[Install]
WantedBy=multi-user.target
UNIT

# --- (re)start the service ---------------------------------------------------
log "Reloading systemd and (re)starting ${SERVICE_NAME}…"
$SUDO systemctl daemon-reload
$SUDO systemctl enable "$SERVICE_NAME" >/dev/null 2>&1 || true
$SUDO systemctl restart "$SERVICE_NAME"

# --- verify ------------------------------------------------------------------
sleep 3
if ! $SUDO systemctl is-active --quiet "$SERVICE_NAME"; then
  $SUDO systemctl status "$SERVICE_NAME" --no-pager -l || true
  die "Service failed to start. See logs: sudo journalctl -u ${SERVICE_NAME} -e"
fi

CODE="$(curl -s -o /dev/null -w '%{http_code}' --max-time 5 "http://localhost:${PORT}/" || echo 000)"
log "Service active. Local HTTP check on :${PORT} returned ${CODE}."

PUBLIC_HOST=""
TOKEN="$(curl -s -X PUT 'http://169.254.169.254/latest/api/token' \
  -H 'X-aws-ec2-metadata-token-ttl-seconds: 60' --max-time 2 2>/dev/null || true)"
if [[ -n "$TOKEN" ]]; then
  PUBLIC_HOST="$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" --max-time 2 \
    http://169.254.169.254/latest/meta-data/public-hostname 2>/dev/null || true)"
fi

echo
log "✅ ${SERVICE_NAME} is running and will auto-restart on failure."
if [[ -n "$PUBLIC_HOST" ]]; then
  PORT_SUFFIX=""; [[ "$PORT" != "80" ]] && PORT_SUFFIX=":${PORT}"
  log "   URL:  http://${PUBLIC_HOST}${PORT_SUFFIX}/"
  log "   (ensure the EC2 security group allows inbound TCP ${PORT})"
fi
log "   Logs:    sudo journalctl -u ${SERVICE_NAME} -f"
log "   Status:  systemctl status ${SERVICE_NAME}"
log "   Stop:    sudo systemctl stop ${SERVICE_NAME}"
