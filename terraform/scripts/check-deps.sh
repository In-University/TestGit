#!/usr/bin/env bash
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' 

echo -e "${YELLOW}🔍 Đang kiểm tra các công cụ cần thiết (Pre-flight checks)...${NC}"

MISSING_DEPS=0

check_cmd() {
    if ! command -v "$1" &> /dev/null; then
        echo -e "${RED}❌ Lỗi: Chưa cài đặt '$1'${NC}"
        echo -e "   👉 $2"
        MISSING_DEPS=1
    else
        echo -e "${GREEN}✅ $1 đã được cài đặt ($(command -v $1))${NC}"
    fi
}

check_cmd "docker" "Cài đặt Docker: https://docs.docker.com/get-docker/"
check_cmd "terraform" "Cài đặt Terraform: https://developer.hashicorp.com/terraform/downloads"
check_cmd "kubectl" "Cài đặt Kubectl: https://kubernetes.io/docs/tasks/tools/"
check_cmd "kind" "Cài đặt Kind: curl -Lo ./kind https://kind.sigs.k8s.io/dl/latest/kind-linux-amd64 && chmod +x ./kind && sudo mv ./kind /usr/local/bin/kind"

if [ "$MISSING_DEPS" -ne 0 ]; then
    echo -e "\n${RED}🛑 Vui lòng cài đặt các công cụ còn thiếu bên trên trước khi tiếp tục.${NC}"
    exit 1
fi
echo -e "${GREEN}Tất cả công cụ đã sẵn sàng! 🚀${NC}\n"
