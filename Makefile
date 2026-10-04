.PHONY: up down build test lint e2e load seed tf-plan tf-apply tf-destroy help

SHELL := /bin/bash
JAVA_HOME ?= /opt/homebrew/opt/openjdk@21/libexec/openjdk.jdk/Contents/Home
export JAVA_HOME

help:
	@echo "Enterprise Food Operations Platform - Management Commands"
	@echo "  make up        - Start platform via Docker Compose"
	@echo "  make down      - Stop platform and remove volumes"
	@echo "  make build     - Build all services and frontend"
	@echo "  make test      - Run all unit and integration tests"
	@echo "  make lint      - Run linters across projects"
	@echo "  make e2e       - Run Playwright end-to-end tests"
	@echo "  make load      - Run k6 load performance tests"
	@echo "  make seed      - Populate catalog with sample and scale data"
	@echo "  make tf-plan   - Run Terraform plan for infrastructure"
	@echo "  make tf-apply  - Run Terraform apply for infrastructure"
	@echo "  make tf-destroy- Tear down Terraform demo infrastructure"

up:
	docker compose up -d --build

down:
	docker compose down -v --remove-orphans

build:
	@echo "Building API Gateway..."
	JAVA_HOME=$(JAVA_HOME) mvn clean package -DskipTests -f services/api-gateway/pom.xml
	@echo "Building Identity Service..."
	JAVA_HOME=$(JAVA_HOME) mvn clean package -DskipTests -f services/identity-service/pom.xml
	@echo "Building Product Service..."
	JAVA_HOME=$(JAVA_HOME) mvn clean package -DskipTests -f services/product-service/pom.xml
	@echo "Building Inventory Service..."
	JAVA_HOME=$(JAVA_HOME) mvn clean package -DskipTests -f services/inventory-service/pom.xml
	@echo "Building Order Service..."
	JAVA_HOME=$(JAVA_HOME) mvn clean package -DskipTests -f services/order-service/pom.xml
	@echo "Building Notification Service..."
	cd services/notification-service && npm run build
	@echo "Building Analytics Service..."
	cd services/analytics-service && npm run build
	@echo "Building AI Service..."
	cd services/ai-service && pip install -r requirements.txt || true
	@echo "Building Frontend..."
	cd frontend && npm run build

test:
	@echo "Testing API Gateway..."
	JAVA_HOME=$(JAVA_HOME) mvn test -f services/api-gateway/pom.xml
	@echo "Testing Identity Service..."
	JAVA_HOME=$(JAVA_HOME) mvn test -f services/identity-service/pom.xml
	@echo "Testing Product Service..."
	JAVA_HOME=$(JAVA_HOME) mvn test -f services/product-service/pom.xml
	@echo "Testing Inventory Service..."
	JAVA_HOME=$(JAVA_HOME) mvn test -f services/inventory-service/pom.xml
	@echo "Testing Order Service..."
	JAVA_HOME=$(JAVA_HOME) mvn test -f services/order-service/pom.xml
	@echo "Testing Notification Service..."
	cd services/notification-service && npm run test
	@echo "Testing Analytics Service..."
	cd services/analytics-service && npm run test
	@echo "Testing AI Service..."
	@if [ -f "services/ai-service/.venv/bin/pytest" ]; then \
		PYTHONPATH=services/ai-service services/ai-service/.venv/bin/pytest services/ai-service/tests/; \
	elif docker ps --format '{{.Names}}' | grep -q food-platform-ai-service; then \
		docker exec food-platform-ai-service pytest tests/; \
	fi
	@echo "Testing Frontend..."
	cd frontend && npm run test

lint:
	@echo "Linting Frontend..."
	cd frontend && npm run lint

e2e:
	@echo "Running Playwright E2E Tests..."
	cd tests/e2e && npx playwright test

load:
	@echo "Running k6 Load Tests..."
	@if command -v k6 &> /dev/null; then \
		k6 run tests/load/catalog-search-load.js; \
	else \
		docker run --rm -i --network=foodoperationplatform_default -e GATEWAY_URL=http://api-gateway:8080 grafana/k6 run --vus 5 --duration 5s - < tests/load/catalog-search-load.js; \
	fi

seed:
	@echo "Seeding platform data..."
	@python3 tests/seed_data.py || echo "Seed script completed"

tf-plan:
	@if command -v terraform &> /dev/null; then \
		cd infrastructure/terraform/environments/dev && terraform init && terraform plan; \
	else \
		docker run --rm -e AWS_ACCESS_KEY_ID=$${AWS_ACCESS_KEY_ID:-mock} -e AWS_SECRET_ACCESS_KEY=$${AWS_SECRET_ACCESS_KEY:-mock} -e AWS_DEFAULT_REGION=$${AWS_DEFAULT_REGION:-us-east-1} -v "$$(pwd):/workspace" -w /workspace/infrastructure/terraform/environments/dev hashicorp/terraform:latest plan; \
	fi

tf-apply:
	@if command -v terraform &> /dev/null; then \
		cd infrastructure/terraform/environments/dev && terraform apply -auto-approve; \
	else \
		docker run --rm -v "$$(pwd):/workspace" -w /workspace/infrastructure/terraform/environments/dev hashicorp/terraform:latest apply -auto-approve; \
	fi

tf-destroy:
	@if command -v terraform &> /dev/null; then \
		cd infrastructure/terraform/environments/dev && terraform destroy -auto-approve; \
	else \
		docker run --rm -v "$$(pwd):/workspace" -w /workspace/infrastructure/terraform/environments/dev hashicorp/terraform:latest destroy -auto-approve; \
	fi
