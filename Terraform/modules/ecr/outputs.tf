output "repository_urls" {
  value       = { for repo in aws_ecr_repository.repo : repo.name => repo.repository_url }
}
