output "bootstrap_brokers" {
  value       = aws_msk_cluster.kafka.bootstrap_brokers
  description = "Plaintext connection host:port pairs for Kafka brokers"
}

output "security_group_id" {
  value       = aws_security_group.kafka.id
  description = "Security group ID for Kafka cluster"
}

output "cluster_arn" {
  value       = aws_msk_cluster.kafka.arn
  description = "ARN of MSK cluster"
}
