#!/usr/bin/env bash
#
# test_container.sh — build the analyze-agent Lambda image, boot it with the AWS
# Lambda Runtime Interface Emulator (RIE, bundled in the base image) and verify
# the analysis endpoint works.
#
# Two checks:
#   1. Liveness — POST a malformed body, expect HTTP 400 from the handler.
#                 No AWS credentials or Bedrock access required.
#   2. Analyze  — if Bedrock creds + BEDROCK_MODEL_ID are available, POST a real
#                 change request against the bundled fixture KB and assert a
#                 schema-shaped envelope (contains "what_breaks") comes back 200.
#
# Usage:
#   ./scripts/test_container.sh                       # liveness, + analyze if creds present
#   BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20240620-v1:0 \
#     AWS_REGION=us-west-2 ./scripts/test_container.sh
#   SKIP_ANALYZE=1 ./scripts/test_container.sh         # liveness only
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPONENT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

IMAGE_NAME="${IMAGE_NAME:-analyze-agent:test}"
CONTAINER_NAME="${CONTAINER_NAME:-analyze-agent-test}"
HOST_PORT="${HOST_PORT:-9001}"
RIE_URL="http://localhost:${HOST_PORT}/2015-03-31/functions/function/invocations"

# Bundled fixture KB (subset of sample_4_skill) laid out as <repo_id>/kb/.
REPO_ID="${REPO_ID:-demo__repo__main}"
CHANGE_REQUEST="${CHANGE_REQUEST:-remove the rear-door module}"
KB_HOST_DIR="${KB_HOST_DIR:-${COMPONENT_DIR}/tests/fixtures}"
KB_MNT="/mnt/kb"
ANALYZE_TIMEOUT="${ANALYZE_TIMEOUT:-90}"

DOCKER="${DOCKER:-docker}"

GREEN=$'\033[0;32m'; RED=$'\033[0;31m'; YEL=$'\033[0;33m'; NC=$'\033[0m'
info()  { echo "${GREEN}==>${NC} $*"; }
warn()  { echo "${YEL}warn:${NC} $*"; }
fail()  { echo "${RED}FAIL:${NC} $*" >&2; exit 1; }

cleanup() { ${DOCKER} rm -f "${CONTAINER_NAME}" >/dev/null 2>&1 || true; }
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

DOCKER_ENV=(
  -e "KB_DIR=${KB_MNT}"
  -e "KB_CACHE_DIR=/tmp"
  -e "BEDROCK_MODEL_ID=${BEDROCK_MODEL_ID:-}"
  -e "AWS_REGION=${AWS_REGION:-us-west-2}"
  -e "BEDROCK_REGION=${BEDROCK_REGION:-${AWS_REGION:-us-west-2}}"
  -e "LOG_LEVEL=${LOG_LEVEL:-INFO}"
)
[ -n "${AWS_ACCESS_KEY_ID:-}" ]     && DOCKER_ENV+=( -e "AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}" )
[ -n "${AWS_SECRET_ACCESS_KEY:-}" ] && DOCKER_ENV+=( -e "AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}" )
[ -n "${AWS_SESSION_TOKEN:-}" ]     && DOCKER_ENV+=( -e "AWS_SESSION_TOKEN=${AWS_SESSION_TOKEN}" )

info "Starting container ${CONTAINER_NAME} on :${HOST_PORT} ..."
${DOCKER} run -d --name "${CONTAINER_NAME}" \
  -p "${HOST_PORT}:8080" \
  -v "${KB_HOST_DIR}:${KB_MNT}:ro" \
  "${DOCKER_ENV[@]}" \
  "${IMAGE_NAME}" >/dev/null

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
# 3. Liveness check — malformed body must return statusCode 400
# --------------------------------------------------------------------------- #
info "Liveness check (handler) ..."
LIVE_RESP="$(curl -s "${RIE_URL}" \
  -d '{"requestContext":{"http":{"method":"POST"}},"body":"{}"}')"
echo "    response: ${LIVE_RESP}"
case "${LIVE_RESP}" in
  *'"statusCode": 400'*|*'"statusCode":400'*)
    info "Handler is alive (got 400 for missing fields)." ;;
  *)
    ${DOCKER} logs "${CONTAINER_NAME}" || true
    fail "unexpected liveness response (handler not wired up?)" ;;
esac

# --------------------------------------------------------------------------- #
# 4. Real analysis — only when we can reach Bedrock
# --------------------------------------------------------------------------- #
if [ "${SKIP_ANALYZE:-0}" = "1" ]; then
  warn "SKIP_ANALYZE=1 set — skipping the real analysis run."
  info "Liveness check passed."
  exit 0
fi
if [ -z "${BEDROCK_MODEL_ID:-}" ]; then
  warn "BEDROCK_MODEL_ID not set — skipping the real analysis run."
  warn "Set BEDROCK_MODEL_ID (+ AWS creds/region) to exercise a real /analyze."
  info "Liveness check passed."
  exit 0
fi

info "Invoking /analyze for repo '${REPO_ID}': \"${CHANGE_REQUEST}\" (timeout ${ANALYZE_TIMEOUT}s) ..."
BODY="$(printf '{"repo_id":"%s","change_request":"%s"}' "${REPO_ID}" "${CHANGE_REQUEST}")"
EVENT="$(printf '{"requestContext":{"http":{"method":"POST"}},"body":%s}' "$(printf '%s' "${BODY}" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')")"
RESP="$(curl -s --max-time "${ANALYZE_TIMEOUT}" "${RIE_URL}" -d "${EVENT}")"
echo "    response: ${RESP}"

case "${RESP}" in
  *'"statusCode": 200'*|*'"statusCode":200'*) : ;;
  *)
    ${DOCKER} logs "${CONTAINER_NAME}" || true
    fail "analysis did not return 200" ;;
esac
case "${RESP}" in
  *what_breaks*) info "Envelope returned (contains what_breaks)." ;;
  *)
    ${DOCKER} logs "${CONTAINER_NAME}" || true
    fail "200 response did not contain a result envelope" ;;
esac

info "All checks passed."
