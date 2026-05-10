subnet = "192.168.1.0/24"

servers = {
  "loadbalancer-k8s" = { ip = "192.168.1.110", ram_gb = 1, cpu = 1, disk = "20GB" }
  "k8s-master-1"     = { ip = "192.168.1.111", ram_gb = 4, cpu = 2, disk = "20GB" }
  "k8s-master-2"     = { ip = "192.168.1.112", ram_gb = 4, cpu = 2, disk = "20GB" }
  "k8s-master-3"     = { ip = "192.168.1.113", ram_gb = 4, cpu = 2, disk = "20GB" }
  "rancher-server"   = { ip = "192.168.1.114", ram_gb = 2, cpu = 1, disk = "20GB", domain = "rancher.devopsedu.vn" }
  "database-server"  = { ip = "192.168.1.115", ram_gb = 2, cpu = 1, disk = "20GB" }
}
