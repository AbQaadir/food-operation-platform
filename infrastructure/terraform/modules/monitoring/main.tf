resource "aws_cloudwatch_log_group" "services" {
  for_each          = toset(var.service_names)
  name              = "/ecs/food-platform-${each.value}-${var.environment}"
  retention_in_days = var.retention_in_days

  tags = {
    Name        = "food-platform-${each.value}-logs-${var.environment}"
    Service     = each.value
    Environment = var.environment
  }
}

resource "aws_cloudwatch_metric_alarm" "high_cpu_alarm" {
  alarm_name          = "food-platform-high-cpu-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = 60
  statistic           = "Average"
  threshold           = 80
  alarm_description   = "This alarm fires if average ECS cluster CPU exceeds 80% for 2 consecutive minutes."

  dimensions = {
    ClusterName = "food-platform-${var.environment}-cluster"
  }

  tags = {
    Environment = var.environment
  }
}

resource "aws_cloudwatch_metric_alarm" "alb_5xx_alarm" {
  alarm_name          = "food-platform-alb-5xx-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "HTTPCode_Target_5XX_Count"
  namespace           = "AWS/ApplicationELB"
  period              = 60
  statistic           = "Sum"
  threshold           = 10
  alarm_description   = "This alarm fires if ALB target returns more than 10 5XX errors in 1 minute."

  tags = {
    Environment = var.environment
  }
}

