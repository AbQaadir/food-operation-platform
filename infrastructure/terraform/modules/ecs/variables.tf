variable "environment" {
  type        = string
  description = "Deployment environment"
}

variable "vpc_id" {
  type        = string
  description = "VPC ID where ECS should be deployed"
}

variable "public_subnet_ids" {
  type        = list(string)
  description = "Public subnet IDs for ALB"
}

variable "private_subnet_ids" {
  type        = list(string)
  description = "Private subnet IDs for ECS tasks"
}

variable "execution_role_arn" {
  type        = string
  description = "ARN of ECS execution role"
}

variable "task_role_arn" {
  type        = string
  description = "ARN of ECS task role"
}

variable "ecr_repository_urls" {
  type        = map(string)
  description = "Map of service names to ECR repository URLs"
}

variable "db_host" {
  type        = string
  description = "RDS database hostname"
  default     = ""
}

variable "db_port" {
  type        = string
  description = "RDS database port"
  default     = "5432"
}

variable "redis_host" {
  type        = string
  description = "ElastiCache Redis hostname"
  default     = ""
}

variable "redis_port" {
  type        = string
  description = "ElastiCache Redis port"
  default     = "6379"
}

variable "kafka_brokers" {
  type        = string
  description = "Kafka bootstrap brokers string"
  default     = ""
}
