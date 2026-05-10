#!/usr/bin/env bash
# Helper: ssh into a VM (container) by hostname via extracted port mapping
# Usage: ./ssh-into-vm.sh <hostname>
set -euo pipefail

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 <hostname> (e.g. k8s-master-1)"
  exit 2
fi

HOST=$1

if ! command -v jq >/dev/null 2>&1; then
  echo "jq is required to parse terraform output. Install: sudo apt install jq"
  exit 2
fi

cd "$(dirname "$0")/terraform"

PORT=$(terraform output -json server_info | jq -r ".[\"${HOST}\"].ssh_port // empty")

if [ -z "$PORT" ]; then
  echo "Could not find SSH port for host: $HOST"
  exit 1
fi

if ! command -v sshpass >/dev/null 2>&1; then
  echo "sshpass is required. Install: sudo apt install -y sshpass"
  exit 2
fi

echo "Connecting to $HOST on localhost port $PORT as root..."
sshpass -p root ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p "$PORT" root@127.0.0.1
