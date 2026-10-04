resource "aws_db_subnet_group" "rds" {
  name       = "food-platform-${var.environment}-db-subnet-group"
  subnet_ids = var.private_subnet_ids

  tags = {
    Name        = "food-platform-${var.environment}-db-subnet-group"
    Environment = var.environment
  }
}

resource "aws_security_group" "rds" {
  name        = "food-platform-${var.environment}-rds-sg"
  description = "Security group for PostgreSQL RDS cluster"
  vpc_id      = var.vpc_id

  ingress {
    description     = "PostgreSQL from ECS microservices"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [var.ecs_security_group_id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "food-platform-${var.environment}-rds-sg"
    Environment = var.environment
  }
}

resource "random_password" "db_password" {
  length           = 24
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

resource "aws_secretsmanager_secret" "db_credentials" {
  name                    = "food-platform/${var.environment}/rds/credentials"
  recovery_window_in_days = 0
}

resource "aws_secretsmanager_secret_version" "db_credentials" {
  secret_id = aws_secretsmanager_secret.db_credentials.id
  secret_string = jsonencode({
    engine   = "postgres"
    host     = aws_db_instance.postgres.address
    port     = aws_db_instance.postgres.port
    username = var.admin_username
    password = random_password.db_password.result
    database = var.database_name
  })
}

resource "aws_db_instance" "postgres" {
  identifier             = "food-platform-${var.environment}-postgres"
  engine                 = "postgres"
  engine_version         = "16.3"
  instance_class         = var.instance_class
  allocated_storage      = var.allocated_storage
  max_allocated_storage  = var.max_allocated_storage
  storage_type           = "gp3"
  storage_encrypted      = true
  multi_az               = var.multi_az
  db_name                = var.database_name
  username               = var.admin_username
  password               = random_password.db_password.result
  db_subnet_group_name   = aws_db_subnet_group.rds.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  skip_final_snapshot    = var.environment != "prod"
  deletion_protection    = var.environment == "prod"
  publicly_accessible    = false

  tags = {
    Name        = "food-platform-${var.environment}-postgres"
    Environment = var.environment
  }
}
