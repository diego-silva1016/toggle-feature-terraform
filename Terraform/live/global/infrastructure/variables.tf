variable "aws_region" {
  type        = string
  default     = "us-east-1"
}

variable "vpc_name" {
  type        = string
  default     = "toggle-feature-vpc"
}

variable "vpc_cidr" {
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnets" {
  type = map(object({
    cidr_block = string
    az         = string
  }))
  default = {
    "public-1" = {
      cidr_block = "10.0.1.0/24"
      az         = "us-east-1a"
    }
    "public-2" = {
      cidr_block = "10.0.2.0/24"
      az         = "us-east-1b"
    }
  }
}

variable "private_subnets" {
  type = map(object({
    cidr_block = string
    az         = string
  }))
  default = {
    "private-1" = {
      cidr_block = "10.0.3.0/24"
      az         = "us-east-1a"
    }
    "private-2" = {
      cidr_block = "10.0.4.0/24"
      az         = "us-east-1b"
    }
  }
}

variable "enable_nat_gateway" {
  type        = bool
  default     = true
}

variable "cluster_name" {
  type        = string
  default     = "toggle-feature-cluster"
}

variable "enable_elastic_load_balancing" {
  type        = bool
  default     = true
}

variable "desired_size" {
  type        = number
  default     = 2
}

variable "max_size" {
  type        = number
  default     = 2
}

variable "min_size" {
  type        = number
  default     = 1
}

variable "instance_type" {
  type        = string
  default     = "t3.small"
}

variable "tags" {
  type        = map(string)
  default     = {
    Project = "toggle-feature"
  }
}

# IAM role que o EKS usa como cluster role e node role (na Academy costuma ser a LabRole).
variable "lab_role_arn" {
  type        = string
  default     = "arn:aws:iam::246325869534:role/LabRole"
  description = "ARN da role IAM passada ao EKS (control plane + node group)."
}

# Na AWS Academy/Vocareum você já entra como assumed-role/voclabs/... — não use AssumeRole na LabRole.
# Só preencha se suas credenciais base precisarem assumir outra role (STS permitido).
variable "terraform_assume_role_arn" {
  type        = string
  default     = ""
  description = "Se não vazio, o provider AWS do Terraform usa sts:AssumeRole neste ARN antes das chamadas à API."
}
