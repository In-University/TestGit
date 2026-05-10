# Deployment Report

## What I implemented

- Terraform configuration to create Docker containers representing VMs specified in the provided table:
  - `loadbalancer-k8s` (192.168.1.110)
  - `k8s-master-1` (192.168.1.111)
  - `k8s-master-2` (192.168.1.112)
  - `k8s-master-3` (192.168.1.113)
  - `rancher-server` (192.168.1.114)
  - `database-server` (192.168.1.115)

- A Docker image (`terraform/docker-image/Dockerfile`) used for the containers that exposes SSH.

- Ansible automation in `ansible/site.yml` to configure:
  - `loadbalancer-k8s`: HAProxy load balancer for Kubernetes API servers
  - `k8s-masters`: installs `containerd`, installs kube packages (pinned to stable via `install-k8s.sh`), initializes cluster on `k8s-master-1`, joins other masters
  - `database-server`: installs MariaDB
  - `rancher-server`: runs Rancher in Docker container

- `generate_inventory.sh`: creates `ansible/hosts.ini` from Terraform outputs.
- `deploy_all.sh`: one command wrapper to `terraform apply`, generate inventory, and run `ansible-playbook`.
- `verify_infra.sh`: quick verification checks (SSH, kube nodes, MariaDB, Rancher container presence).

## Why this approach

- Use Terraform for "infrastructure" (create containers and network), and Ansible for "configuration" (install packages, initialize K8s, run services). This separation follows IaC best practices: immutable infra + idempotent configuration.

- Use `for_each` in Terraform to map the machines table directly from variables, improving maintainability and readability.

- Use Ansible to run kubeadm and other system-level tasks; Ansible is widely used in enterprise for configuration and orchestration.

## How it works (high level)

1. `./deploy_all.sh` will:
   - Run `terraform init` and `terraform apply` to create containers.
   - Run `./generate_inventory.sh` which reads `terraform output -json server_info` and writes `ansible/hosts.ini`.
   - Run `ansible-playbook -i ansible/hosts.ini ansible/site.yml` to configure systems.

2. `ansible/site.yml` tasks:
   - Common: update apt cache, disable swap, install common packages.
   - K8s: install containerd, create config, install kubeadm/kubelet/kubectl via `install-k8s.sh` (which pins version to official stable release), initialize cluster on `k8s-master-1`, install Calico CNI, and join other masters.
   - Loadbalancer: installs HAProxy and configures it to balance masters on port 6443.
   - Database: installs MariaDB and ensures service running.
   - Rancher: runs `rancher/rancher:latest` container exposing 80/443.

## Notes on versions and compatibility

- `install-k8s.sh` queries `https://dl.k8s.io/release/stable.txt` for the current official stable Kubernetes release and attempts to install matching `kubelet`, `kubeadm` and `kubectl` packages. This pins Kubernetes tooling to the stable release at time of deployment.

- Rancher compatibility: modern Rancher (2.x) is expected to run on top of Kubernetes as an app. For simplicity this automation runs the `rancher/rancher:latest` Docker image on the `rancher-server` VM. If you prefer running Rancher on the Kubernetes cluster (recommended for production), we can change the playbook to install Rancher via Helm into the cluster.

## How to run

- Ensure host has `terraform`, `ansible`, `sshpass`, `jq` installed.
- Run:

```bash
chmod +x deploy_all.sh generate_inventory.sh verify_infra.sh
./deploy_all.sh
```

- After completion, run verification:

```bash
./verify_infra.sh
```

## Caveats and next improvements

- Security: current automation uses `root` with password `root` for SSH convenience in lab. Replace with SSH keys for production.
- Rancher installation: better to install Rancher onto the Kubernetes cluster using Helm, and ensure Rancher version is compatible with Kubernetes version. I can change the playbook to do that.
- Idempotency: some tasks (kubeadm init/join) are guarded by `creates` checks but may require more robust idempotency logic.
- CRI and kubeadm options: tuning for production (cgroup drivers, sysctl settings) is recommended.

## Files added/modified
- terraform/* (existing)
- ansible/ansible.cfg
- ansible/site.yml
- generate_inventory.sh
- deploy_all.sh
- verify_infra.sh
- REPORT.md


