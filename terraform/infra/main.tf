terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}

provider "docker" {}

resource "docker_network" "lab_net" {
  name = "lab_network"
  ipam_config {
    subnet = "192.168.1.0/24"
  }
}

resource "docker_container" "loadbalancer" {
  name  = "loadbalancer-k8s"
  image = "nginx:alpine"
  memory = 1024
  
  networks_advanced {
    name         = docker_network.lab_net.name
    ipv4_address = "192.168.1.110"
  }

  volumes {
    host_path      = abspath("${path.module}/../proxy/nginx.conf")
    container_path = "/etc/nginx/nginx.conf"
    read_only      = true
  }

  ports {
    internal = 80
    external = 80
  }
}

resource "docker_container" "rancher" {
  name       = "rancher-server"
  image      = "rancher/rancher:latest"
  privileged = true
  # memory     = 4096

  ports {
    internal = 80
    external = 8080
  }

  ports {
    internal = 443
    external = 8443
  }
  
  networks_advanced {
    name         = docker_network.lab_net.name
    ipv4_address = "192.168.1.114"
  }
}

resource "docker_container" "database" {
  name  = "database-server"
  image = "postgres:15-alpine"
  memory = 2048
  
  env =[
    "POSTGRES_USER=admin",
    "POSTGRES_PASSWORD=admin",
    "POSTGRES_DB=devopsdb"
  ]

  networks_advanced {
    name         = docker_network.lab_net.name
    ipv4_address = "192.168.1.115"
  }

  ports {
    internal = 5432
    external = 5432
  }
}
