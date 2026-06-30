#!/usr/bin/env bash
#
# test_container.sh — build the ingestion-agent Lambda image, boot it with the
# AWS Lambda Runtime Interface Emulator (RIE, bundled in the base image) and
# verify the ingestion process runs.
#
# Two checks:
#   1. Liveness    — POST a malformed API event, expect HTTP 400 from the
#                    dispatcher. Proves the container + handler are wired up.
#                    No AWS credentials or Bedrock access required.
#   2. Real ingest — if Bedrock creds + BEDROCK_MODEL_ID are available, invoke
#                    the `worker` path against a real GitHub repo and assert the
#                    run returns READY and writes a KB tree to ./out.
#
# Usage:
#   ./scripts/test_container.sh                 # liveness, + ingest if creds present
#   GITHUB_URL=https://github.com/patrikja/autosar BRANCH=master \
#     BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20240620-v1:0 \
#     AWS_REGION=us-west-2 ./scripts/test_container.sh
#   SKIP_INGEST=1 ./scripts/test_container.sh    # liveness only
#
set -euo pipefail

# --------------------------------------------------------------------------- #
# Config
# --------------------------------------------------------------------------- #
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPONENT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

IMAGE_NAME="${IMAGE_NAME:-ingest-agent:test}"
CONTAINER_NAME="${CONTAINER_NAME:-ingest-agent-test}"
HOST_PORT="${HOST_PORT:-9000}"
RIE_URL="http://localhost:${HOST_PORT}/2015-03-31/functions/function/invocations"

GITHUB_URL="${GITHUB_URL:-https://github.com/patrikja/autosar}"
BRANCH="${BRANCH:-master}"
OUT_DIR="${OUT_DIR:-${COMPONENT_DIR}/out}"
INGEST_TIMEOUT="${INGEST_TIMEOUT:-840}"   # seconds; under the 900s Lambda ceiling

# Container-internal paths (LOCAL storage mode: KB_BUCKET/REPOS_TABLE unset).
KB_OUT_MNT="/mnt/kbout"

DOCKER="${DOCKER:-docker}"

GREEN=$'\033[0;32m'; RED=$'\033[0;31m'; YEL=$'\033[0;33m'; NC=$'\033[0m'
info()  { echo "${GREEN}==>${NC} $*"; }
warn()  { echo "${YEL}warn:${NC} $*"; }
fail()  { echo "${RED}FAIL:${NC} $*" >&2; exit 1; }

cleanup() {
  ${DOCKER} rm -f "${CONTAINER_NAME}" >/dev/null 2>&1 || true
}
trap cleanup EXIT

command -v "${DOCKER}" >/dev/null 2>&1 || fail "docker not found on PATH"
command -v curl >/dev/null 2>&1 || fail "curl not found on PATH"

# --------------------------------------------------------------------------- #
# 1. Build
# --------------------------------------------------------------------------- #
info "Building image ${IMAGE_NAME} ..."
${DOCKER} build -t "${IMAGE_NAME}" "${COMPONENT_DIR}"

# --------------------------------------------------------------------------- #
# 2. Run container (RIE listens on :8080 inside the Lambda base image)
# --------------------------------------------------------------------------- #
cleanup
mkdir -p "${OUT_DIR}"

DOCKER_ENV=(
  -e "KB_OUT_DIR=${KB_OUT_MNT}"
  -e "KB_WORKDIR=/tmp"
  -e "BEDROCK_MODEL_ID=${BEDROCK_MODEL_ID:-}"
  -e "AWS_REGION=${AWS_REGION:-us-west-2}"
  -e "BEDROCK_REGION=${BEDROCK_REGION:-${AWS_REGION:-us-west-2}}"
  -e "LOG_LEVEL=${LOG_LEVEL:-INFO}"
)
# Pass through static credentials when present (so a real ingest can call Bedrock).
[ -n "${AWS_ACCESS_KEY_ID:-}" ]     && DOCKER_ENV+=( -e "AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}" )
[ -n "${AWS_SECRET_ACCESS_KEY:-}" ] && DOCKER_ENV+=( -e "AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}" )
[ -n "${AWS_SESSION_TOKEN:-}" ]     && DOCKER_ENV+=( -e "AWS_SESSION_TOKEN=${AWS_SESSION_TOKEN}" )

info "Starting container ${CONTAINER_NAME} on :${HOST_PORT} ..."
${DOCKER} run -d --name "${CONTAINER_NAME}" \
  -p "${HOST_PORT}:8080" \
  -v "${OUT_DIR}:${KB_OUT_MNT}" \
  "${DOCKER_ENV[@]}" \
  "${IMAGE_NAME}" >/dev/null

# Wait for the emulator to accept connections.
info "Waiting for the runtime emulator ..."
for _ in $(seq 1 30); do
  if curl -s -o /dev/null "${RIE_URL}" -d '{}' 2>/dev/null; then
    break
  fi
  if ! ${DOCKER} ps -q -f "name=${CONTAINER_NAME}" | grep -q .; then
    ${DOCKER} logs "${CONTAINER_NAME}" || true
    fail "container exited during startup"
  fi
  sleep 1
done

# --------------------------------------------------------------------------- #
# 3. Liveness check — malformed API request must return statusCode 400
# --------------------------------------------------------------------------- #
info "Liveness check (api dispatcher) ..."
LIVE_RESP="$(curl -s "${RIE_URL}" \
  -d '{"requestContext":{"http":{"method":"POST"}},"body":"{}"}')"
echo "    response: ${LIVE_RESP}"
case "${LIVE_RESP}" in
  *'"statusCode": 400'*|*'"statusCode":400'*)
    info "Handler is alive (got 400 for missing github_url)." ;;
  *)
    ${DOCKER} logs "${CONTAINER_NAME}" || true
    fail "unexpected liveness response (handler not wired up?)" ;;
esac

# --------------------------------------------------------------------------- #
# 4. Real ingest (worker path) — only when we can reach Bedrock
# --------------------------------------------------------------------------- #
if [ "${SKIP_INGEST:-0}" = "1" ]; then
  warn "SKIP_INGEST=1 set — skipping the full ingestion run."
  info "Liveness check passed."
  exit 0
fi
if [ -z "${BEDROCK_MODEL_ID:-}" ]; then
  warn "BEDROCK_MODEL_ID not set — skipping the full ingestion run."
  warn "Set BEDROCK_MODEL_ID (+ AWS creds/region) to exercise a real ingest."
  info "Liveness check passed."
  exit 0
fi

info "Invoking worker ingest for ${GITHUB_URL}@${BRANCH} (timeout ${INGEST_TIMEOUT}s) ..."
PAYLOAD="$(printf '{"mode":"worker","github_url":"%s","branch":"%s"}' "${GITHUB_URL}" "${BRANCH}")"
INGEST_RESP="$(curl -s --max-time "${INGEST_TIMEOUT}" "${RIE_URL}" -d "${PAYLOAD}")"
echo "    response: ${INGEST_RESP}"

case "${INGEST_RESP}" in
  *'"status": "READY"'*|*'"status":"READY"'*)
    info "Ingestion reported READY." ;;
  *)
    ${DOCKER} logs "${CONTAINER_NAME}" || true
    fail "ingestion did not report READY" ;;
esac

# --------------------------------------------------------------------------- #
# 5. Verify the KB tree landed in ./out
# --------------------------------------------------------------------------- #
info "Verifying KB output under ${OUT_DIR} ..."
README_COUNT="$(find "${OUT_DIR}" -path '*/kb/README.md' | wc -l | tr -d ' ')"
INDEX_COUNT="$(find "${OUT_DIR}" -path '*/kb/_index/*.md' | wc -l | tr -d ' ')"
[ "${README_COUNT}" -ge 1 ] || fail "no kb/README.md written to ${OUT_DIR}"
[ "${INDEX_COUNT}" -ge 1 ]  || fail "no kb/_index/*.md files written to ${OUT_DIR}"

info "KB written: ${README_COUNT} README, ${INDEX_COUNT} index file(s)."
find "${OUT_DIR}" -name '*.md' | sed "s|^|    |" | head -n 20
info "All checks passed."
