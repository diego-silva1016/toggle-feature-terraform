variable "cluster_name" {
  type        = string
}

variable "elasticache_description" {
  type        = string
  default     = "Cluster de ElastiCache para caching de dados"
}

variable "replication_group_id" {
  type        = string
  default     = null
}

variable "engine" {
  type        = string
  default     = "redis"
}

variable "node_type" {
  type        = string
  default     = "cache.t3.micro"
}

variable "num_cache_nodes" {
  type        = number
  default     = 1
}

variable "parameter_group_name" {
  type        = string
  default     = "default.redis7"
}

variable "engine_version" {
  type        = string
  default     = "7.0"
}

variable "port" {
  type        = number
  default     = 6379
}

variable "subnet_group_name" {
  type        = string
}

variable "subnet_ids" {
  type        = list(string)
}

variable "vpc_id" {
  type        = string
}

variable "vpc_cidr" {
  type        = string
}

variable "automatic_failover_enabled" {
  type        = bool
  default     = false
}

variable "tags" {
  type        = map(string)
  default     = {}
}
