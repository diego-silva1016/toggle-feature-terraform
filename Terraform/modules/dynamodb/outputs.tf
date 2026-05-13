output "table_name" {
  value       = aws_dynamodb_table.this.name
}

output "table_arn" {
  value       = aws_dynamodb_table.this.arn
}

output "table_id" {
  value       = aws_dynamodb_table.this.id
}

output "stream_arn" {
  value       = try(aws_dynamodb_table.this.stream_arn, null)
}

output "stream_specification" {
  value = {
    stream_enabled   = aws_dynamodb_table.this.stream_enabled
    stream_view_type = try(aws_dynamodb_table.this.stream_view_type, null)
  }
}

output "global_secondary_indexes" {
  value = [
    for gsi in aws_dynamodb_table.this.global_secondary_index : {
      name = gsi.name
      arn  = gsi.arn
    }
  ]
}

output "billing_mode" {
  value       = aws_dynamodb_table.this.billing_mode
}
