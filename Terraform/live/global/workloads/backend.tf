terraform {
  backend "s3" {
    bucket       = "toggle-feature-terraform-state-20"
    key          = "global/workloads/terraform.tfstate"
    region       = "us-east-1"
    encrypt      = true
    use_lockfile = true
    dynamodb_table = "terraform-state-lock"
  }
}
