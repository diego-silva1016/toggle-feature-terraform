resource "aws_dynamodb_table" "this" {
  name             = var.table_name
  billing_mode     = var.billing_mode
  hash_key         = var.hash_key
  read_capacity    = var.billing_mode == "PROVISIONED" ? var.read_capacity : null
  write_capacity   = var.billing_mode == "PROVISIONED" ? var.write_capacity : null
  stream_enabled   = var.stream_specification.stream_enabled
  stream_view_type = var.stream_specification.stream_enabled ? var.stream_specification.stream_view_type : null

  attribute {
    name = var.hash_key
    type = var.hash_key_type
  }

  ttl {
    attribute_name = var.ttl_attribute_name
    enabled        = var.ttl_attribute_name != null
  }

  point_in_time_recovery {
    enabled = var.point_in_time_recovery_enabled
  }

  tags = merge(var.tags, { Name = var.table_name })
}
