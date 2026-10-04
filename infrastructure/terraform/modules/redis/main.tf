resource "aws_security_group" "redis" {
  name        = "food-platform-redis-sg-${var.environment}"
  description = "Security group for ElastiCache Redis cluster"
  vpc_id      = var.vpc_id

  ingress {
    description     = "Redis port from ECS tasks"
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [var.ecs_security_group_id]
  }

  egress {
    from_port        = 0
    to_port          = 0
    protocol         = "-1"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  tags = {
    Name        = "food-platform-redis-sg-${var.environment}"
    Environment = var.environment
  }
}

resource "aws_elasticache_subnet_group" "redis" {
  name       = "food-platform-redis-subnet-${var.environment}"
  subnet_ids = var.private_subnet_ids

  tags = {
    Name        = "food-platform-redis-subnet-${var.environment}"
    Environment = var.environment
  }
}

resource "aws_elasticache_replication_group" "redis" {
  replication_group_id       = "food-redis-${var.environment}"
  description                = "ElastiCache Redis replication group for session cache, idempotency, and rate limiting"
  node_type                  = var.node_type
  num_cache_clusters         = var.num_cache_clusters
  parameter_group_name       = "default.redis7"
  port                       = 6379
  subnet_group_name          = aws_elasticache_subnet_group.redis.name
  security_group_ids         = [aws_security_group.redis.id]
  at_rest_encryption_enabled = true
  transit_encryption_enabled = false
  automatic_failover_enabled = var.num_cache_clusters > 1 ? true : false

  tags = {
    Name        = "food-platform-redis-${var.environment}"
    Environment = var.environment
  }
}

