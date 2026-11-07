resource "aws_ecs_cluster" "main" {
  name = "food-platform-${var.environment}-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = {
    Name        = "food-platform-${var.environment}-cluster"
    Environment = var.environment
  }
}

# Security Groups
resource "aws_security_group" "alb" {
  name        = "food-platform-${var.environment}-alb-sg"
  description = "Security group for public Application Load Balancer"
  vpc_id      = var.vpc_id

  ingress {
    description = "HTTP from Internet"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS from Internet"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "food-platform-${var.environment}-alb-sg"
    Environment = var.environment
  }
}

resource "aws_security_group" "ecs_tasks" {
  name        = "food-platform-${var.environment}-ecs-tasks-sg"
  description = "Security group for ECS tasks in private subnets"
  vpc_id      = var.vpc_id

  ingress {
    description     = "Traffic from ALB"
    from_port       = 0
    to_port         = 65535
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  ingress {
    description = "Inter-service internal communication"
    from_port   = 0
    to_port     = 65535
    protocol    = "tcp"
    self        = true
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "food-platform-${var.environment}-ecs-tasks-sg"
    Environment = var.environment
  }
}

# Application Load Balancer
resource "aws_lb" "main" {
  name               = "food-platform-${var.environment}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = var.public_subnet_ids

  tags = {
    Name        = "food-platform-${var.environment}-alb"
    Environment = var.environment
  }
}

# Target Groups
resource "aws_lb_target_group" "frontend" {
  name        = "food-${var.environment}-tg-frontend"
  port        = 5173
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"

  health_check {
    path                = "/"
    matcher             = "200"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 3
  }
}

resource "aws_lb_target_group" "gateway" {
  name        = "food-${var.environment}-tg-gateway"
  port        = 8080
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "ip"

  health_check {
    path                = "/actuator/health"
    matcher             = "200"
    interval            = 15
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 3
  }
}

# ALB Listener
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.frontend.arn
  }
}

resource "aws_lb_listener_rule" "api_routes" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 10

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.gateway.arn
  }

  condition {
    path_pattern {
      values = ["/api/*", "/actuator/*"]
    }
  }
}

# Service Discovery (Cloud Map for inter-service DNS)
resource "aws_service_discovery_private_dns_namespace" "internal" {
  name        = "foodplatform.local"
  description = "Private DNS namespace for internal ECS microservice communication"
  vpc         = var.vpc_id
}

resource "aws_service_discovery_service" "services" {
  for_each = toset([
    "api-gateway",
    "identity-service",
    "product-service",
    "inventory-service",
    "order-service",
    "notification-service",
    "ai-service"
  ])

  name = each.value

  dns_config {
    namespace_id = aws_service_discovery_private_dns_namespace.internal.id

    dns_records {
      ttl  = 10
      type = "A"
    }

    routing_policy = "MULTIVALUE"
  }

  health_check_custom_config {
    failure_threshold = 1
  }
}

# Sample ECS Service Definitions
resource "aws_ecs_task_definition" "gateway" {
  family                   = "food-platform-${var.environment}-api-gateway"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 512
  memory                   = 1024
  execution_role_arn       = var.execution_role_arn
  task_role_arn            = var.task_role_arn

  container_definitions = jsonencode([
    {
      name      = "api-gateway"
      image     = var.ecr_repository_urls["api-gateway"]
      essential = true
      portMappings = [
        {
          containerPort = 8080
          protocol      = "tcp"
        }
      ]
      environment = [
        { name = "PORT_GATEWAY", value = "8080" },
        { name = "IDENTITY_SERVICE_HOST", value = "identity-service.foodplatform.local" },
        { name = "PRODUCT_SERVICE_HOST", value = "product-service.foodplatform.local" },
        { name = "INVENTORY_SERVICE_HOST", value = "inventory-service.foodplatform.local" },
        { name = "ORDER_SERVICE_HOST", value = "order-service.foodplatform.local" },
        { name = "NOTIFICATION_SERVICE_HOST", value = "notification-service.foodplatform.local" },
        { name = "AI_SERVICE_HOST", value = "ai-service.foodplatform.local" }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = "/ecs/food-platform-${var.environment}-api-gateway"
          "awslogs-region"        = "us-east-1"
          "awslogs-stream-prefix" = "gateway"
        }
      }
    }
  ])
}

resource "aws_ecs_service" "gateway" {
  name            = "food-platform-${var.environment}-api-gateway"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.gateway.arn
  desired_count   = 2
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.gateway.arn
    container_name   = "api-gateway"
    container_port   = 8080
  }

  service_registries {
    registry_arn = aws_service_discovery_service.services["api-gateway"].arn
  }
}
