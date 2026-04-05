#!/usr/bin/env bash
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive

echo "[1/5] Installing base packages..."
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg

echo "[2/5] Configuring Kubernetes apt repository..."
sudo mkdir -p -m 755 /etc/apt/keyrings
curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.35/deb/Release.key | \
	sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
sudo chmod 644 /etc/apt/keyrings/kubernetes-apt-keyring.gpg

echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.35/deb/ /' | \
	sudo tee /etc/apt/sources.list.d/kubernetes.list >/dev/null
sudo chmod 644 /etc/apt/sources.list.d/kubernetes.list

echo "[3/5] Installing kubectl..."
sudo apt-get update
sudo apt-get install -y kubectl

echo "[4/5] Installing minikube..."
ARCH="$(uname -m)"
case "$ARCH" in
	x86_64|amd64)
		MINIKUBE_ARCH="amd64"
		;;
	aarch64|arm64)
		MINIKUBE_ARCH="arm64"
		;;
	*)
		echo "Unsupported architecture: $ARCH"
		exit 1
		;;
esac

TMP_BIN="/tmp/minikube-linux-${MINIKUBE_ARCH}"
curl -fLo "$TMP_BIN" "https://github.com/kubernetes/minikube/releases/latest/download/minikube-linux-${MINIKUBE_ARCH}"
sudo install "$TMP_BIN" /usr/local/bin/minikube
rm -f "$TMP_BIN"

echo "[5/5] Starting minikube..."
if command -v docker >/dev/null 2>&1; then
	minikube start --driver=docker
elif command -v podman >/dev/null 2>&1; then
	minikube start --driver=podman
else
	echo "No supported runtime found (docker/podman)."
	echo "Installation finished. Start minikube manually after installing a driver."
fi

echo "Installing k9s..."
wget https://github.com/derailed/k9s/releases/latest/download/k9s_Linux_amd64.tar.gz
tar -xzf k9s_Linux_amd64.tar.gz
sudo mv k9s /usr/local/bin/
rm k9s_Linux_amd64.tar.gz
sudo chmod +x /usr/local/bin/k9s
