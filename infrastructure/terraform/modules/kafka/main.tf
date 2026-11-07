resource "aws_security_group" "kafka" {
  name        = "food-platform-${var.environment}-kafka-sg"
  description = "Security group for Apache Kafka / Amazon MSK cluster"
  vpc_id      = var.vpc_id

  ingress {
    description     = "Kafka plaintext from ECS tasks"
    from_port       = 9092
    to_port         = 9092
    protocol        = "tcp"
    security_groups = [var.ecs_security_group_id]
  }

  ingress {
    description     = "Kafka TLS from ECS tasks"
    from_port       = 9094
    to_port         = 9094
    protocol        = "tcp"
    security_groups = [var.ecs_security_group_id]
  }

  ingress {
    description     = "Kafka IAM auth from ECS tasks"
    from_port       = 9098
    to_port         = 9098
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
    Name        = "food-platform-${var.environment}-kafka-sg"
    Environment = var.environment
  }
}

resource "aws_msk_configuration" "config" {
  kafka_versions = ["3.6.0", "3.7.0"]
  name           = "food-platform-${var.environment}-msk-config"

  server_properties = <<PROPERTIES
auto.create.topics.enable = false
default.replication.factor = 2
min.insync.replicas = 2
num.partitions = 3
transaction.state.log.replication.factor = 2
transaction.state.log.min.isr = 2
PROPERTIES
}

resource "aws_msk_cluster" "kafka" {
  cluster_name           = "food-platform-${var.environment}-kafka"
  kafka_version          = "3.6.0"
  number_of_broker_nodes = var.number_of_broker_nodes

  broker_node_group_info {
    instance_type   = var.broker_node_instance_type
    client_subnets  = var.private_subnet_ids
    security_groups = [aws_security_group.kafka.id]
    storage_info {
      ebs_storage_info {
        volume_size = 50
      }
    }
  }

  configuration_info {
    arn      = aws_msk_configuration.config.arn
    revision = aws_msk_configuration.config.latest_revision
  }

  encryption_info {
    encryption_in_transit {
      client_broker = "PLAINTEXT"
      in_cluster    = true
    }
  }

  tags = {
    Name        = "food-platform-${var.environment}-kafka"
    Environment = var.environment
  }
}
