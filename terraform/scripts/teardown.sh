#!/usr/bin/env bash
set -euo pipefail

echo "🧨 Bắt đầu dọn dẹp hệ thống..."

if kind get clusters 2>/dev/null | grep -q "^devops-k8s$"; then
    echo "Xóa cụm K8s 'devops-k8s'..."
    kind delete cluster --name devops-k8s
fi

echo "Hủy hạ tầng Terraform..."
cd infra
terraform destroy -auto-approve
cd ..

echo "✅ Đã dọn dẹp sạch sẽ!"
