resource "aws_elasticache_subnet_group" "redis" {
  name       = var.subnet_group_name
  subnet_ids = var.subnet_ids

  tags = merge(var.tags, { Name = "${var.cluster_name}-subnet-group" })
}

resource "aws_security_group" "redis" {
  name        = "${var.cluster_name}-redis-sg"
  description = "Permite acesso ao Redis"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = var.port
    to_port     = var.port
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, { Name = "${var.cluster_name}-redis-sg" })
}

resource "aws_elasticache_cluster" "redis" {
  cluster_id           = var.cluster_name
  engine               = var.engine
  engine_version       = var.engine_version
  node_type            = var.node_type
  num_cache_nodes      = 1
  parameter_group_name = var.parameter_group_name
  port                 = var.port
  subnet_group_name    = aws_elasticache_subnet_group.redis.name
  security_group_ids   = [aws_security_group.redis.id]

  tags = merge(var.tags, { Name = var.cluster_name })
}
