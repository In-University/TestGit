variable "subnet" {
  description = "Network subnet for the lab"
  type        = string
  default     = "192.168.1.0/24"
}

variable "servers" {
  description = "Map of server configurations based on requirements"
  type = map(object({
    ip     = string
    ram_gb = number
    cpu    = number
    disk   = string
    domain = optional(string)
  }))
}
