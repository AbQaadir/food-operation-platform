variable "environment" {
  type        = string
  description = "Deployment environment"
}

variable "service_names" {
  type        = list(string)
  description = "Services to configure CloudWatch logging for"
  default = [
    "api-gateway",
    "identity-service",
    "product-service",
    "inventory-service",
    "order-service",
    "notification-service",
    "ai-service",
    "frontend"
  ]
}

variable "retention_in_days" {
  type        = number
  description = "CloudWatch log retention in days"
  default     = 30
}
