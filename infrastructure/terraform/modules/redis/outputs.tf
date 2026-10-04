output "primary_endpoint_address" {
  value       = aws_elasticache_replication_group.redis.primary_endpoint_address
  description = "Address of the endpoint for the primary node in the replication group"
}

output "port" {
  value       = aws_elasticache_replication_group.redis.port
  description = "Port number on which the cache accepts connections"
}

output "security_group_id" {
  value       = aws_security_group.redis.id
  description = "Security group ID of the Redis cluster"
}
