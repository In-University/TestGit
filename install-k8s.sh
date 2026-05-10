#!/usr/bin/env bash
# Install kubeadm, kubelet and kubectl pinned to the official stable Kubernetes version.
# This script is intended to run on the target 'VM' (container) as root.
# Usage: curl -fsSL https://dl.k8s.io/release/stable.txt | tr -d '\n' to get tag; or run this script which queries stable.txt.

set -euo pipefail

if [ "$EUID" -ne 0 ]; then
  echo "Run as root"
  exit 1
fi

echo "Querying official stable Kubernetes release..."
K8S_TAG=$(curl -fsSL https://dl.k8s.io/release/stable.txt)
K8S_VERSION=${K8S_TAG#v}
echo "Stable tag: $K8S_TAG -> using version $K8S_VERSION"

echo "Disabling swap (required by kubeadm)..."
swapoff -a || true
sed -i.bak '/ swap / s/^/#/' /etc/fstab || true

echo "Installing prerequisites..."
apt-get update
apt-get install -y ca-certificates curl gnupg2 apt-transport-https

echo "Adding Kubernetes apt repository..."
curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg | gpg --dearmor -o /usr/share/keyrings/kubernetes-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/kubernetes-archive-keyring.gpg] https://apt.kubernetes.io/ kubernetes-xenial main" > /etc/apt/sources.list.d/kubernetes.list

apt-get update
echo "Installing kubelet kubeadm kubectl version ${K8S_VERSION}-00"
apt-get install -y kubelet=${K8S_VERSION}-00 kubeadm=${K8S_VERSION}-00 kubectl=${K8S_VERSION}-00 || {
  echo "Package install failed. Available versions for debugging:"
  apt-cache madison kubeadm | head -n 20
  exit 1
}

apt-mark hold kubelet kubeadm kubectl

echo "Kubernetes tools installed. Versions:"
kubeadm version && kubelet --version && kubectl version --client
