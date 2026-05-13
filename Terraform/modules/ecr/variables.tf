variable "repository_names" {
  type        = list(string)
  default     = []
}

variable "tags" {
  type        = map(string)
  default     = {}
}
