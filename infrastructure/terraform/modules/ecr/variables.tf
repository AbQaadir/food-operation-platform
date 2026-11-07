variable "environment" {
  type        = string
  description = "Deployment environment"
}

variable "service_names" {
  type        = list(string)
  description = "List of microservice repository names to create"
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
