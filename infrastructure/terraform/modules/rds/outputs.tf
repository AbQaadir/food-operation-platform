output "endpoint" {
  value       = aws_db_instance.postgres.endpoint
  description = "Connection endpoint of RDS instance"
}

output "address" {
  value       = aws_db_instance.postgres.address
  description = "Hostname address of RDS instance"
}

output "port" {
  value       = aws_db_instance.postgres.port
  description = "Database port"
}

output "database_name" {
  value       = aws_db_instance.postgres.db_name
  description = "Default database name"
}

output "security_group_id" {
  value       = aws_security_group.rds.id
  description = "ID of RDS security group"
}

output "credentials_secret_arn" {
  value       = aws_secretsmanager_secret.db_credentials.arn
  description = "ARN of database credentials in AWS Secrets Manager"
}
