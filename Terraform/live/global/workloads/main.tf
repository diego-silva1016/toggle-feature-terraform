module "k8s_workloads" {
  source = "../../../modules/k8s_deploy"

  manifest_base_path = abspath(var.manifest_base_path)
  services           = var.services
}

output "applied_manifests" {
  value       = module.k8s_workloads.applied_manifests
}
