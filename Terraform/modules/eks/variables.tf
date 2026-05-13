variable "cluster_name" {
  type        = string
}

variable "cluster_role_arn" {
  type        = string
}

variable "subnet_ids" {
  type        = list(string)
}

variable "enable_elastic_load_balancing" {
  type        = bool
  default     = true
}

variable "node_group_name" {
  type        = string
  default     = "default"
}

variable "node_role_arn" {
  type        = string
}

variable "instance_type" {
  type        = string
  default     = "t3.medium"
}

variable "desired_size" {
  type        = number
  default     = 2
}

variable "min_size" {
  type        = number
  default     = 1
}

variable "max_size" {
  type        = number
  default     = 3
}

variable "capacity_type" {
  type        = string
  default     = "SPOT"
}

variable "tags" {
  type        = map(string)
  default     = {}
}
