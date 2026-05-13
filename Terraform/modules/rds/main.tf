resource "aws_security_group" "rds_sg" {
  name        = "${var.project_name}-rds-sg"
  description = "Permite acesso ao Postgres"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = var.tags
}

resource "aws_db_subnet_group" "main" {
  name       = "${var.project_name}-subnet-group"
  subnet_ids = var.private_subnet_ids

  tags = var.tags
}

resource "random_password" "db_password" {
  length           = 16
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

resource "aws_secretsmanager_secret" "db_secret" {
  name = "rds-postgres-password-${var.db_identifier}"
}

resource "aws_secretsmanager_secret_version" "db_password_val" {
  secret_id     = aws_secretsmanager_secret.db_secret.id
  secret_string = random_password.db_password.result
}

resource "aws_db_instance" "postgres" {
  identifier             = var.db_identifier
  engine                 = "postgres"
  engine_version         = var.db_engine_version
  instance_class         = var.instance_class
  allocated_storage      = var.allocated_storage
  db_name                = var.db_name
  username               = var.db_username
  password               = random_password.db_password.result
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds_sg.id]

  skip_final_snapshot = true
  publicly_accessible = false

  tags = var.tags
}
