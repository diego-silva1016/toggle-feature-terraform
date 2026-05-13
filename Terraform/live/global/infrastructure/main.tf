terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.25"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.0"
    }
    kubectl = {
      source  = "gavinbunney/kubectl"
      version = "~> 1.14"
    }
  }
}

provider "aws" {
  region = var.aws_region

  dynamic "assume_role" {
    for_each = var.terraform_assume_role_arn != "" ? [1] : []
    content {
      role_arn = var.terraform_assume_role_arn
    }
  }
}

module "vpc" {
  source = "../../../modules/vpc"

  vpc_name           = var.vpc_name
  vpc_cidr           = var.vpc_cidr
  public_subnets     = var.public_subnets
  private_subnets    = var.private_subnets
  enable_nat_gateway = var.enable_nat_gateway
  tags               = var.tags
}

module "eks" {
  source = "../../../modules/eks"

  cluster_name                   = var.cluster_name
  cluster_role_arn               = var.lab_role_arn
  subnet_ids                     = concat(values(module.vpc.public_subnet_ids), module.vpc.private_subnet_ids_list)
  enable_elastic_load_balancing  = var.enable_elastic_load_balancing
  node_role_arn                  = var.lab_role_arn
  desired_size                   = var.desired_size
  max_size                       = var.max_size
  min_size                       = var.min_size
  instance_type                  = var.instance_type
  capacity_type                  = "SPOT"
}

data "aws_eks_cluster_auth" "cluster" {
  name = module.eks.cluster_name
}

provider "helm" {
  kubernetes {
    host                   = module.eks.cluster_endpoint
    cluster_ca_certificate = base64decode(module.eks.cluster_certificate_authority_data)
    token                  = data.aws_eks_cluster_auth.cluster.token
  }
}

provider "kubectl" {
  host                   = module.eks.cluster_endpoint
  cluster_ca_certificate = base64decode(module.eks.cluster_certificate_authority_data)
  token                  = data.aws_eks_cluster_auth.cluster.token
}

module "rds_auth" {
  source = "../../../modules/rds"

  project_name       = "auth-service"
  vpc_id             = module.vpc.vpc_id
  vpc_cidr           = var.vpc_cidr
  private_subnet_ids = module.vpc.private_subnet_ids_list
  db_identifier      = "auth-db"
  db_engine_version  = "15"
  instance_class     = "db.t3.micro"
  allocated_storage  = 20
  db_name            = "authdb"
  db_username        = "authuser"
  tags               = var.tags
}

module "rds_flag" {
  source = "../../../modules/rds"

  project_name       = "flag-service"
  vpc_id             = module.vpc.vpc_id
  vpc_cidr           = var.vpc_cidr
  private_subnet_ids = module.vpc.private_subnet_ids_list
  db_identifier      = "flag-db"
  db_engine_version  = "15"
  instance_class     = "db.t3.micro"
  allocated_storage  = 20
  db_name            = "flagdb"
  db_username        = "flaguser"
  tags               = var.tags
}

module "rds_targeting" {
  source = "../../../modules/rds"

  project_name       = "targeting-service"
  vpc_id             = module.vpc.vpc_id
  vpc_cidr           = var.vpc_cidr
  private_subnet_ids = module.vpc.private_subnet_ids_list
  db_identifier      = "targeting-db"
  db_engine_version  = "15"
  instance_class     = "db.t3.micro"
  allocated_storage  = 20
  db_name            = "targetingdb"
  db_username        = "targetinguser"
  tags               = var.tags
}

module "redis" {
  source = "../../../modules/redis"

  cluster_name      = "toggle-feature-redis"
  engine            = "redis"
  engine_version    = "7.0"
  node_type         = "cache.t3.micro"
  parameter_group_name = "default.redis7"
  port              = 6379
  subnet_group_name = "redis-subnet-group"
  subnet_ids        = module.vpc.private_subnet_ids_list
  vpc_id            = module.vpc.vpc_id
  vpc_cidr          = var.vpc_cidr

  tags = var.tags
}

module "dynamodb" {
  source = "../../../modules/dynamodb"

  table_name     = "ToggleMasterAnalytics"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "id"
  hash_key_type  = "S"
  stream_specification = {
    stream_enabled   = false
    stream_view_type = null
  }
  ttl_attribute_name = null
  point_in_time_recovery_enabled = true
  tags = var.tags
}

module "sqs" {
  source = "../../../modules/sqs"

  queue_name                  = "evaluation-queue"
  delay_seconds               = 0
  max_message_size            = 262144
  message_retention_seconds   = 86400
  visibility_timeout_seconds  = 30
  receive_wait_time_seconds   = 0
  tags                        = var.tags
}

module "ecr" {
  source = "../../../modules/ecr"

  repository_names = [
    "auth-service",
    "flag-service",
    "evaluation-service",
    "targeting-service",
    "analytics-service"
  ]
  tags = var.tags
}

resource "helm_release" "argocd" {
  name       = "argocd"
  repository = "https://argoproj.github.io/argo-helm"
  chart      = "argo-cd"
  namespace  = "argocd"
  create_namespace = true

  values = [
    yamlencode({
      server = {
        service = {
          type = "LoadBalancer"
        }
      }
    })
  ]
}

