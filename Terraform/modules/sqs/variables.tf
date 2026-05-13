variable "queue_name" {
  type        = string  
}

variable "delay_seconds" {
  type        = number
  default     = 0
}

variable "max_message_size" {
  type        = number
  default     = 262144
}
variable "message_retention_seconds" {
  type        = number
  default     = 86400
}

variable "visibility_timeout_seconds" {
  type        = number
  default     = 300
}

variable "receive_wait_time_seconds" {
  type        = number
  default     = 0
}

variable "tags" {
  type        = map(string)
  default     = {}
}
