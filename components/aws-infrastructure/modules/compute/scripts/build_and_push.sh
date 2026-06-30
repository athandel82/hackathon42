#!/usr/bin/env bash
#
# build_and_push.sh — build a Lambda container image and push it to ECR.
#
# Usage: build_and_push.sh <context_dir> <dockerfile> <image_uri> <region> [platform]
#
# [platform] defaults to linux/arm64 (Lambda arm64/Graviton). Pass linux/amd64
# for x86_64 Lambdas (ARCHITECTURE.md §S7). buildx builds for the target
# platform regardless of the host arch (native when they match, else emulated).
set -euo pipefail

CONTEXT="$1"
DOCKERFILE="$2"
IMAGE_URI="$3"
REGION="$4"
PLATFORM="${5:-linux/arm64}"

REGISTRY="${IMAGE_URI%%/*}" # <account>.dkr.ecr.<region>.amazonaws.com

echo "[build_and_push] logging in to ${REGISTRY}"
aws ecr get-login-password --region "${REGION}" \
  | docker login --username AWS --password-stdin "${REGISTRY}"

echo "[build_and_push] building ${IMAGE_URI} (${PLATFORM}) from ${CONTEXT}"
docker buildx build \
  --platform "${PLATFORM}" \
  --provenance=false \
  -f "${DOCKERFILE}" \
  -t "${IMAGE_URI}" \
  --push \
  "${CONTEXT}"

echo "[build_and_push] pushed ${IMAGE_URI}"
