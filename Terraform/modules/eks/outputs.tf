output "cluster_id" {
  value       = aws_eks_cluster.cluster.id
}

output "cluster_endpoint" {
  value       = aws_eks_cluster.cluster.endpoint
}

output "cluster_arn" {
  value       = aws_eks_cluster.cluster.arn
}

output "cluster_certificate_authority_data" {
  value       = aws_eks_cluster.cluster.certificate_authority[0].data
}

output "cluster_name" {
  value       = aws_eks_cluster.cluster.name
}

output "node_group_arn" {
  value       = aws_eks_node_group.nodes.arn
}
