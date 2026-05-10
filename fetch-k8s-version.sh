#!/usr/bin/env bash
# Fetch the current stable Kubernetes release tag from official source
set -euo pipefail

URL="https://dl.k8s.io/release/stable.txt"
echo "Fetching stable Kubernetes release from ${URL}"
curl -fsSL "$URL"
