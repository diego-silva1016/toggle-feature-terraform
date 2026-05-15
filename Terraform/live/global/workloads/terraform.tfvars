aws_region      = "us-east-1"
cluster_name    = "toggle-feature-cluster"
manifest_base_path = "../../../../GitOps"

services = [
  "analytics-service",
  "auth-service",
  "evaluation-service",
  "flag-service",
  "targeting-service"
]
