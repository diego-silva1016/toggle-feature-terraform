output "queue_url" {
  value       = aws_sqs_queue.example_queue.id  
}

output "queue_arn" {
    value       = aws_sqs_queue.example_queue.arn  
}

output "queue_id" {
    value       = aws_sqs_queue.example_queue.id  
}
