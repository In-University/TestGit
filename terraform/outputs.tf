# output "server_info" {
#   value = {
#     for host, srv in docker_container.k8s_nodes : host => {
#       name = srv.name
#     }
#   }
# }