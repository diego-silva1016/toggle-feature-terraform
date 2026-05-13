locals {
  manifest_paths = flatten([
    for service in var.services : [
      for file_name in fileset("${var.manifest_base_path}/${service}", "*.y*ml") :
      "${var.manifest_base_path}/${service}/${file_name}"
    ]
  ])

  namespaces = {
    for path in local.manifest_paths :
    path => yamldecode(file(path))
    if can(regex("namespace\\.ya?ml$", lower(path)))
  }

  non_namespaces = {
    for path in local.manifest_paths :
    path => yamldecode(file(path))
    if !can(regex("namespace\\.ya?ml$", lower(path)))
  }
}

resource "kubernetes_manifest" "namespaces" {
  for_each = local.namespaces
  manifest = each.value
}

resource "kubernetes_manifest" "manifests" {
  for_each   = local.non_namespaces
  manifest   = each.value
  depends_on = [kubernetes_manifest.namespaces]
}
