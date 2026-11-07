output "log_group_names" {
  value       = { for k, v in aws_cloudwatch_log_group.services : k => v.name }
  description = "Map of service names to CloudWatch log group names"
}

output "log_group_arns" {
  value       = { for k, v in aws_cloudwatch_log_group.services : k => v.arn }
  description = "Map of service names to CloudWatch log group ARNs"
}

