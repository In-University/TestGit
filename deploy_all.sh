#!/usr/bin/env bash
set -e

echo "🚀 BƯỚC 1: Dựng hạ tầng cơ bản (Network, Nginx, Rancher, Database) bằng Terraform..."
cd terraform
terraform init
terraform apply -auto-approve
cd ..

echo "🚀 BƯỚC 2: Khởi tạo cụm Kubernetes (3 Masters) bằng Kind..."
# Trick cực hay: Ép Kind sử dụng Docker network do Terraform tạo ra
export KIND_EXPERIMENTAL_DOCKER_NETWORK=lab_network

# Kiểm tra nếu cụm đã tồn tại thì bỏ qua
if ! kind get clusters | grep -q "devops-k8s"; then
    kind create cluster --config kind-config.yaml
else
    echo "Cụm K8s 'devops-k8s' đã tồn tại. Bỏ qua tạo mới."
fi

echo ""
echo "🎉 HOÀN TẤT! TOÀN BỘ HẠ TẦNG ĐÃ ĐƯỢC DỰNG THÀNH CÔNG."
echo "------------------------------------------------------"
echo "👉 1. Kiểm tra k8s nodes:  kubectl get nodes"
echo "👉 2. Truy cập Rancher  :  Thêm '127.0.0.1 rancher.devopsedu.vn' vào file /etc/hosts (hoặc C:\Windows\System32\drivers\etc\hosts) và truy cập http://rancher.devopsedu.vn"
echo "👉 3. Database Postgres :  localhost:5432 (User/Pass: admin/admin)"