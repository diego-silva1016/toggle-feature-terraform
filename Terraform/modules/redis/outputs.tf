output "cluster_address" {
  value       = aws_elasticache_cluster.redis.cache_nodes[0].address
}

output "cluster_port" {
  value       = aws_elasticache_cluster.redis.port
}

output "cluster_id" {
  value       = aws_elasticache_cluster.redis.cluster_id
}

output "replication_group_primary_endpoint_address" {
  value       = null
}

output "replication_group_reader_endpoint_address" {
  value       = null
}

output "replication_group_id" {
  value       = null
}

output "subnet_group_name" {
  value       = aws_elasticache_subnet_group.redis.name
}
