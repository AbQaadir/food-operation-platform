variable "environment" {
  type        = string
  description = "Deployment environment"
}

variable "vpc_id" {
  type        = string
  description = "VPC ID where Kafka should be deployed"
}

variable "private_subnet_ids" {
  type        = list(string)
  description = "Private subnet IDs for Kafka brokers"
}

variable "ecs_security_group_id" {
  type        = string
  description = "Security group of ECS services communicating with Kafka"
}

variable "broker_node_instance_type" {
  type        = string
  description = "MSK broker instance type"
  default     = "kafka.t3.small"
}

variable "number_of_broker_nodes" {
  type        = number
  description = "Number of MSK broker nodes"
  default     = 2
}
