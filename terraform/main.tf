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
    subnet = var.subnet
  }
}

resource "docker_image" "ssh_image" {
  name = "tf-ssh-image:latest"
  build {
    context = "${path.module}/docker-image"
  }
}

resource "docker_container" "servers" {
  for_each = var.servers

  name     = each.key
  image    = docker_image.ssh_image.name
  hostname = each.key

  # Privileged is usually required for running K8s components inside docker correctly
  privileged = true

  # Start SSH daemon
  command = ["/usr/sbin/sshd", "-D"]

  # Docker memory is specified in MB, converting from GB
  memory = each.value.ram_gb * 1024

  # For Docker CPU limits we can use cpuset_cpus for exact cores or cpu_shares for weight.
  # But for simplicity in docker we use labels as metadata here.
  labels {
    label = "cpu-core-target"
    value = tostring(each.value.cpu)
  }
  labels {
    label = "disk-target"
    value = each.value.disk
  }
  dynamic "labels" {
    for_each = each.value.domain != null ? [each.value.domain] : []
    content {
      label = "domain"
      value = labels.value
    }
  }

  networks_advanced {
    name         = docker_network.lab_net.name
    ipv4_address = each.value.ip
  }

  ports {
    internal = 22
    # Determine unique port by adding 40000 to the last octet of the IP (e.g. 192.168.1.110 -> 40110)
    external = 40000 + tonumber(split(".", each.value.ip)[3])
  }
}
