variable "aws_region" {
  type        = string
  description = "AWS region for production deployment"
  default     = "us-east-1"
}

variable "environment" {
  type        = string
  description = "Environment name"
  default     = "prod"
}

variable "vpc_cidr" {
  type        = string
  description = "VPC CIDR block"
  default     = "10.100.0.0/16"
}
