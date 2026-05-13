output "applied_manifests" {
  value = concat(
    keys(kubernetes_manifest.namespaces),
    keys(kubernetes_manifest.manifests)
  )
}
