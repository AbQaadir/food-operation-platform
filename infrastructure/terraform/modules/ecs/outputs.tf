output "cluster_id" {
  value       = aws_ecs_cluster.main.id
  description = "ID of ECS cluster"
}

output "cluster_name" {
  value       = aws_ecs_cluster.main.name
  description = "Name of ECS cluster"
}

output "alb_dns_name" {
  value       = aws_lb.main.dns_name
  description = "Public DNS name of Application Load Balancer"
}

output "ecs_security_group_id" {
  value       = aws_security_group.ecs_tasks.id
  description = "Security group ID for ECS tasks"
}

output "alb_security_group_id" {
  value       = aws_security_group.alb.id
  description = "Security group ID for ALB"
}
