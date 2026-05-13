variable "aws_region" {
  type        = string
  default     = "us-east-1"
}

# Opcional: só se suas credenciais precisarem de sts:AssumeRole. Academy/Vocareum: deixe "".
variable "terraform_assume_role_arn" {
  type        = string
  default     = ""
  description = "ARN para assume_role no provider AWS do Terraform. Vazio = usar a sessão atual (ex.: voclabs/...)."
}

variable "cluster_name" {
  type        = string
}

variable "manifest_base_path" {
  type        = string
  default     = "../../../../Kubernetes"
}

variable "services" {
  type        = list(string)
  default = [
    "analytics-service",
    "auth-service",
    "evaluation-service",
    "flag-service",
    "targeting-service"
  ]
}
