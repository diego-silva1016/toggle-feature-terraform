output "vpc_id" {
  value       = module.vpc.vpc_id
}

output "public_subnet_ids" {
  value       = module.vpc.public_subnet_ids
}

output "private_subnet_ids" {
  value       = module.vpc.private_subnet_ids_list
}

output "eks_cluster_name" {
  value       = module.eks.cluster_name
}

output "eks_cluster_endpoint" {
  value       = module.eks.cluster_endpoint
}

output "rds_auth_endpoint" {
  value       = module.rds_auth.db_instance_endpoint
}

output "rds_auth_address" {
  value = module.rds_auth.db_instance_address
}

output "rds_auth_port" {
  value = module.rds_auth.db_instance_port
}

output "rds_auth_name" {
  value = module.rds_auth.db_name
}

output "rds_auth_username" {
  value = module.rds_auth.db_username
}

output "rds_flag_endpoint" {
  value       = module.rds_flag.db_instance_endpoint
}

output "rds_flag_address" {
  value = module.rds_flag.db_instance_address
}

output "rds_flag_port" {
  value = module.rds_flag.db_instance_port
}

output "rds_flag_name" {
  value = module.rds_flag.db_name
}

output "rds_flag_username" {
  value = module.rds_flag.db_username
}

output "rds_targeting_endpoint" {
  value       = module.rds_targeting.db_instance_endpoint
}

output "rds_targeting_address" {
  value = module.rds_targeting.db_instance_address
}

output "rds_targeting_port" {
  value = module.rds_targeting.db_instance_port
}

output "rds_targeting_name" {
  value = module.rds_targeting.db_name
}

output "rds_targeting_username" {
  value = module.rds_targeting.db_username
}

output "redis_endpoint" {
  value       = module.redis.cluster_address
}

output "redis_port" {
  value = module.redis.cluster_port
}

output "redis_cluster_id" {
  value = module.redis.cluster_id
}

output "redis_replication_group_primary_endpoint_address" {
  value = module.redis.replication_group_primary_endpoint_address
}

output "redis_replication_group_reader_endpoint_address" {
  value = module.redis.replication_group_reader_endpoint_address
}

output "redis_replication_group_id" {
  value = module.redis.replication_group_id
}

output "redis_subnet_group_name" {
  value = module.redis.subnet_group_name
}

output "dynamodb_table_name" {
  value       = module.dynamodb.table_name
}

output "dynamodb_table_arn" {
  value = module.dynamodb.table_arn
}

output "dynamodb_table_id" {
  value = module.dynamodb.table_id
}

output "dynamodb_stream_arn" {
  value = module.dynamodb.stream_arn
}

output "dynamodb_stream_specification" {
  value = module.dynamodb.stream_specification
}

output "dynamodb_global_secondary_indexes" {
  value = module.dynamodb.global_secondary_indexes
}

output "dynamodb_billing_mode" {
  value = module.dynamodb.billing_mode
}

output "sqs_queue_url" {
  value       = module.sqs.queue_url
}

output "sqs_queue_arn" {
  value = module.sqs.queue_arn
}

output "sqs_queue_id" {
  value = module.sqs.queue_id
}

output "ecr_repository_urls" {
  value       = module.ecr.repository_urls
}
