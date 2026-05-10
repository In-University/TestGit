output "server_info" {
  description = "Connection and configuration details for the servers"
  value = {
    for host, srv in docker_container.servers : host => {
      host     = host
      ip       = element(srv.networks_advanced[*].ipv4_address, 0)
      ssh_port = element(srv.ports[*].external, 0)
    }
  }
}
