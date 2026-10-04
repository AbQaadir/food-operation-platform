# ADR 008: AWS Deployment Topology & Amazon MSK Migration

## Status
Accepted

## Context
Deploying an enterprise microservices platform to AWS requires decisions regarding compute orchestration (ECS Fargate vs EKS), managed data stores (RDS PostgreSQL vs self-hosted), cache architecture (ElastiCache Redis), and messaging backbone (Amazon MSK vs self-hosted Kafka on ECS/EC2).
Key criteria:
1. **Operational overhead:** Low maintenance burden; serverless/managed where possible.
2. **Cost-efficiency in Dev vs High Availability in Prod:** Dev environments must minimize idle costs (single NAT, single node Redis/RDS), while Prod requires multi-AZ failover and autoscaling.
3. **Kafka strategy:** Amazon MSK has a non-negligible cost baseline (~$200+/month). The architecture must define a clear path from containerized Kafka in dev/staging to managed MSK in prod.

## Decision
1. **Compute Engine: AWS ECS with AWS Fargate:**
   - Selected ECS Fargate over EKS. Fargate eliminates Kubernetes cluster control-plane management, worker node patching, and complex ingress controllers.
   - Microservices run as containerized tasks in private subnets with task definitions specifying CPU/Memory resource constraints.
   - Traffic enters via an AWS Application Load Balancer (ALB) which routes `/api/*` and `/actuator/*` to the Spring Cloud Gateway target group, and all frontend requests to the React/Nginx target group.
   - Inter-service discovery uses AWS Cloud Map private DNS (`foodplatform.local`).

2. **Data Stores:**
   - **Relational:** Amazon RDS for PostgreSQL 16. Multi-AZ in `prod` with storage autoscaling (20GB to 500GB) and encryption at rest with AWS KMS. Credentials stored and rotated via AWS Secrets Manager.
   - **Cache & Idempotency:** Amazon ElastiCache for Redis 7.1 with replication group in private subnets.

3. **Apache Kafka Backbone & MSK Migration Path:**
   - In `dev`: Containerized Apache Kafka in KRaft mode running on ECS Fargate / Docker with persistent EBS volume.
   - In `prod`: Amazon MSK (Managed Streaming for Apache Kafka) cluster spanning multi-AZ private subnets with:
     - 3 partitions per topic default.
     - In-sync replicas = 2 (`min.insync.replicas=2`).
     - Encryption in-transit and SASL/IAM authentication.
   - Zero application code changes: microservices only require updating `KAFKA_BOOTSTRAP_SERVERS` from `kafka:9092` to the MSK broker endpoints.

4. **Infrastructure as Code (IaC):**
   - Implemented modular Terraform under `infrastructure/terraform/modules/`:
     - `networking`: VPC, public/private subnets across AZs, IGW, NAT Gateways.
     - `ecr`: Elastic Container Registry repositories per service with vulnerability scanning and 30-day lifecycle policies.
     - `rds`: PostgreSQL 16 RDS instance, subnet group, and security groups.
     - `redis`: ElastiCache Redis cluster and security groups.
     - `kafka`: Amazon MSK cluster and configuration.
     - `ecs`: ECS Fargate cluster, ALB, target groups, and task definitions.
     - `iam`: ECS task execution and runtime roles with least privilege.
     - `monitoring`: CloudWatch log groups and metric alarms.
   - Environments separated into `dev` and `prod`.

## Consequences
- **Positive:**
  - Production-ready cloud architecture completely reproducible via Terraform.
  - Transparent transition between self-hosted Kafka and managed MSK.
  - Least-privilege IAM policies with Secrets Manager integration.
- **Negative:**
  - Running full multi-AZ MSK and RDS in AWS requires adequate cloud budget.
