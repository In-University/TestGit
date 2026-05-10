#!/usr/bin/env bash
set -euo pipefail

GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}====================================================${NC}"
echo -e "${CYAN}   🚀 KHỞI TẠO HẠ TẦNG & KUBERNETES CLUSTER   ${NC}"
echo -e "${CYAN}====================================================${NC}"

# Bước 1: Terraform
echo -e "\n${GREEN}[1/2] Đang triển khai hạ tầng mạng, Proxy, Database & Rancher bằng Terraform...${NC}"
cd infra
terraform init 
terraform apply -auto-approve
cd ..

# Bước 2: Kind K8s Cluster
echo -e "\n${GREEN}[2/2] Đang khởi tạo Kubernetes Cluster bằng Kind...${NC}"
export KIND_EXPERIMENTAL_DOCKER_NETWORK=lab_network

if ! kind get clusters 2>/dev/null | grep -q "^devops-k8s$"; then
    kind create cluster --config k8s/kind-config.yaml
else
    echo -e "⚡ Cụm K8s 'devops-k8s' đã tồn tại, bỏ qua tạo mới."
fi

echo -e "\n${GREEN}🎉 HOÀN TẤT TRIỂN KHAI THÀNH CÔNG!${NC}"
echo "------------------------------------------------------"
echo "👉 1. Node Status : kubectl get nodes"
echo "👉 2. Rancher UI  : Thêm '127.0.0.1 rancher.devopsedu.vn' vào file /etc/hosts và truy cập http://rancher.devopsedu.vn"