output "alb_dns_name" {
  value       = module.ecs.alb_dns_name
  description = "Public ALB DNS endpoint for Food Operations Platform"
}

output "rds_endpoint" {
  value       = module.rds.endpoint
  description = "Production RDS PostgreSQL endpoint"
}

output "redis_endpoint" {
  value       = module.redis.primary_endpoint_address
  description = "Production ElastiCache Redis primary endpoint"
}

output "kafka_bootstrap_brokers" {
  value       = module.kafka.bootstrap_brokers
  description = "Amazon MSK cluster bootstrap brokers"
}
