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
  source      = "../../modules/networking"
  environment = var.environment
  vpc_cidr    = var.vpc_cidr
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
  instance_class        = "db.t4g.micro"
  multi_az              = false
}

module "redis" {
  source                = "../../modules/redis"
  environment           = var.environment
  vpc_id                = module.networking.vpc_id
  private_subnet_ids    = module.networking.private_subnet_ids
  ecs_security_group_id = module.ecs.ecs_security_group_id
  node_type             = "cache.t4g.micro"
  num_cache_clusters    = 1
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
}
