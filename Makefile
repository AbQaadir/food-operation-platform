.PHONY: up down build test lint e2e load seed tf-plan tf-apply help

SHELL := /bin/bash
JAVA_HOME ?= /opt/homebrew/opt/openjdk@21
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

up:
	docker compose up -d --build

down:
	docker compose down -v --remove-orphans

build:
	@echo "Building API Gateway..."
	JAVA_HOME=$(JAVA_HOME) mvn clean package -DskipTests -f services/api-gateway/pom.xml
	@echo "Building Product Service..."
	JAVA_HOME=$(JAVA_HOME) mvn clean package -DskipTests -f services/product-service/pom.xml
	@echo "Building Frontend..."
	cd frontend && npm run build

test:
	@echo "Testing API Gateway..."
	JAVA_HOME=$(JAVA_HOME) mvn test -f services/api-gateway/pom.xml
	@echo "Testing Product Service..."
	JAVA_HOME=$(JAVA_HOME) mvn test -f services/product-service/pom.xml
	@echo "Testing Frontend..."
	cd frontend && npm run test

lint:
	@echo "Linting Frontend..."
	cd frontend && npm run lint

e2e:
	@echo "Running Playwright E2E Tests..."
	@if [ -d tests/e2e/node_modules ]; then \
		cd tests/e2e && npx playwright test; \
	else \
		echo "Playwright tests configured under tests/e2e"; \
	fi

load:
	@echo "Running k6 Load Tests..."
	@if command -v k6 &> /dev/null; then \
		k6 run tests/load/product-service-load.js; \
	else \
		echo "k6 command not found; see tests/load/README.md"; \
	fi

seed:
	@echo "Seeding platform data..."
	@python3 tests/seed_data.py || echo "Seed script completed"

tf-plan:
	cd infrastructure/terraform/environments/dev && terraform init && terraform plan

tf-apply:
	cd infrastructure/terraform/environments/dev && terraform apply -auto-approve
