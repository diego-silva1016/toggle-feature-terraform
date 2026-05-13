resource "aws_ecr_repository" "repo" {
  for_each = toset(var.repository_names)

  name                 = each.value
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = var.tags
}

resource "aws_ecr_lifecycle_policy" "policy" {
  for_each = toset(var.repository_names)

  repository = aws_ecr_repository.repo[each.value].name

  policy = jsonencode({
    rules = [{
      rulePriority = 1
      selection = {
        tagStatus   = "any"
        countType   = "imageCountMoreThan"
        countNumber = 10
      }
      action = {
        type = "expire"
      }
    }]
  })
}
