variable "environment" {
  type        = string
  description = "Deployment environment"
}

variable "vpc_id" {
  type        = string
  description = "VPC ID where RDS should be deployed"
}

variable "private_subnet_ids" {
  type        = list(string)
  description = "List of private subnet IDs for DB subnet group"
}

variable "ecs_security_group_id" {
  type        = string
  description = "Security group ID of ECS tasks allowed to connect to RDS"
}

variable "instance_class" {
  type        = string
  description = "RDS instance class"
  default     = "db.t4g.micro"
}

variable "allocated_storage" {
  type        = number
  description = "Initial allocated storage in GB"
  default     = 20
}

variable "max_allocated_storage" {
  type        = number
  description = "Max storage autoscaling limit in GB"
  default     = 100
}

variable "multi_az" {
  type        = bool
  description = "Whether to deploy multi-AZ for high availability"
  default     = false
}

variable "database_name" {
  type        = string
  description = "Initial database name"
  default     = "postgres"
}

variable "admin_username" {
  type        = string
  description = "PostgreSQL admin username"
  default     = "dbadmin"
}
