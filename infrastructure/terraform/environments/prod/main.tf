terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "food-operations-platform"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

module "networking" {
  source              = "../../modules/networking"
  environment         = var.environment
  vpc_cidr            = var.vpc_cidr
  availability_zones  = ["us-east-1a", "us-east-1b", "us-east-1c"]
  public_subnet_cidrs = ["10.100.1.0/24", "10.100.2.0/24", "10.100.3.0/24"]
  private_subnet_cidrs = ["10.100.11.0/24", "10.100.12.0/24", "10.100.13.0/24"]
}

module "iam" {
  source      = "../../modules/iam"
  environment = var.environment
}

module "monitoring" {
  source      = "../../modules/monitoring"
  environment = var.environment
}

module "ecr" {
  source      = "../../modules/ecr"
  environment = var.environment
}

module "rds" {
  source                = "../../modules/rds"
  environment           = var.environment
  vpc_id                = module.networking.vpc_id
  private_subnet_ids    = module.networking.private_subnet_ids
  ecs_security_group_id = module.ecs.ecs_security_group_id
  instance_class        = "db.t4g.medium"
  multi_az              = true
  allocated_storage     = 50
  max_allocated_storage = 500
}

module "redis" {
  source                = "../../modules/redis"
  environment           = var.environment
  vpc_id                = module.networking.vpc_id
  private_subnet_ids    = module.networking.private_subnet_ids
  ecs_security_group_id = module.ecs.ecs_security_group_id
  node_type             = "cache.t4g.small"
  num_cache_clusters    = 2
}

module "kafka" {
  source                 = "../../modules/kafka"
  environment            = var.environment
  vpc_id                 = module.networking.vpc_id
  private_subnet_ids     = [module.networking.private_subnet_ids[0], module.networking.private_subnet_ids[1]]
  ecs_security_group_id  = module.ecs.ecs_security_group_id
  broker_node_instance_type = "kafka.m5.large"
  number_of_broker_nodes = 2
}

module "ecs" {
  source              = "../../modules/ecs"
  environment         = var.environment
  vpc_id              = module.networking.vpc_id
  public_subnet_ids   = module.networking.public_subnet_ids
  private_subnet_ids  = module.networking.private_subnet_ids
  execution_role_arn  = module.iam.execution_role_arn
  task_role_arn       = module.iam.task_role_arn
  ecr_repository_urls = module.ecr.repository_urls
  db_host             = module.rds.address
  db_port             = module.rds.port
  redis_host          = module.redis.primary_endpoint_address
  redis_port          = module.redis.port
  kafka_brokers       = module.kafka.bootstrap_brokers
}
