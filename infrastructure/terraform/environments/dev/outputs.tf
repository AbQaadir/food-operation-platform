output "alb_dns_name" {
  value       = module.ecs.alb_dns_name
  description = "Public ALB DNS endpoint for Food Operations Platform"
}

output "rds_endpoint" {
  value       = module.rds.endpoint
  description = "RDS PostgreSQL endpoint"
}

output "redis_endpoint" {
  value       = module.redis.primary_endpoint_address
  description = "ElastiCache Redis primary endpoint"
}

output "ecr_repositories" {
  value       = module.ecr.repository_urls
  description = "ECR repository URLs"
}
