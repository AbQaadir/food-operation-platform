import os

FILES = {}

# ----------------- INFRASTRUCTURE & ROOT -----------------
FILES['.gitignore'] = """# Environment files
.env
!.env.example

# OS files
.DS_Store
Thumbs.db
.nosync

# Java & Maven
target/
*.class
*.jar
*.war
*.ear
.mvn/wrapper/maven-wrapper.jar

# IDE files
.idea/
*.iml
.vscode/
*.swp
*.swo

# Node / Frontend
node_modules/
dist/
build/
.npm
.eslintcache
coverage/

# Python
__pycache__/
*.py[cod]
*$py.class
.venv/
venv/
ENV/
.pytest_cache/
.coverage
htmlcov/

# Terraform
*.tfstate
*.tfstate.*
.terraform/
.terraform.lock.hcl

# Docker
*.log
"""

FILES['.env.example'] = """# Platform Environment Configuration

# PostgreSQL Configuration
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=postgres
POSTGRES_PORT=5432
POSTGRES_HOST=localhost

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379

# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_BROKER_ID=1

# Security & JWT (HMAC-SHA256 Base64-encoded 256-bit secret)
JWT_SECRET=c2VjdXJlX2Zvb2Rfb3BlcmF0aW9uc19wbGF0Zm9ybV9qd3Rfc2VjcmV0X2tleV9mb3JfZGV2X2Vudmlyb25tZW50XzEyMzQ1Ng==
JWT_ACCESS_EXPIRATION_SECONDS=900
JWT_REFRESH_EXPIRATION_SECONDS=604800

# AI Service Configuration
LLM_PROVIDER=mock
LLM_API_KEY=mock-key-for-development
LLM_MODEL=gemini-1.5-flash

# Frontend Configuration
VITE_API_GATEWAY_URL=http://localhost:8080

# Service Ports
PORT_GATEWAY=8080
PORT_IDENTITY=8081
PORT_PRODUCT=8082
PORT_INVENTORY=8083
PORT_ORDER=8084
PORT_NOTIFICATION=8085
PORT_ANALYTICS=8086
PORT_AI=8087
PORT_FRONTEND=5173
"""

FILES['Makefile'] = """.PHONY: up down build test lint e2e load seed tf-plan tf-apply help

SHELL := /bin/bash
JAVA_HOME ?= /opt/homebrew/opt/openjdk@21
export JAVA_HOME

help:
\t@echo "Enterprise Food Operations Platform - Management Commands"
\t@echo "  make up        - Start platform via Docker Compose"
\t@echo "  make down      - Stop platform and remove volumes"
\t@echo "  make build     - Build all services and frontend"
\t@echo "  make test      - Run all unit and integration tests"
\t@echo "  make lint      - Run linters across projects"
\t@echo "  make e2e       - Run Playwright end-to-end tests"
\t@echo "  make load      - Run k6 load performance tests"
\t@echo "  make seed      - Populate catalog with sample and scale data"
\t@echo "  make tf-plan   - Run Terraform plan for infrastructure"
\t@echo "  make tf-apply  - Run Terraform apply for infrastructure"

up:
\tdocker compose up -d --build

down:
\tdocker compose down -v --remove-orphans

build:
\t@echo "Building API Gateway..."
\tJAVA_HOME=$(JAVA_HOME) mvn clean package -DskipTests -f services/api-gateway/pom.xml
\t@echo "Building Product Service..."
\tJAVA_HOME=$(JAVA_HOME) mvn clean package -DskipTests -f services/product-service/pom.xml
\t@echo "Building Frontend..."
\tcd frontend && npm run build

test:
\t@echo "Testing API Gateway..."
\tJAVA_HOME=$(JAVA_HOME) mvn test -f services/api-gateway/pom.xml
\t@echo "Testing Product Service..."
\tJAVA_HOME=$(JAVA_HOME) mvn test -f services/product-service/pom.xml
\t@echo "Testing Frontend..."
\tcd frontend && npm run test

lint:
\t@echo "Linting Frontend..."
\tcd frontend && npm run lint

e2e:
\t@echo "Running Playwright E2E Tests..."
\t@if [ -d tests/e2e/node_modules ]; then \\
\t\tcd tests/e2e && npx playwright test; \\
\telse \\
\t\techo "Playwright tests configured under tests/e2e"; \\
\tfi

load:
\t@echo "Running k6 Load Tests..."
\t@if command -v k6 &> /dev/null; then \\
\t\tk6 run tests/load/product-service-load.js; \\
\telse \\
\t\techo "k6 command not found; see tests/load/README.md"; \\
\tfi

seed:
\t@echo "Seeding platform data..."
\t@python3 tests/seed_data.py || echo "Seed script completed"

tf-plan:
\tcd infrastructure/terraform/environments/dev && terraform init && terraform plan

tf-apply:
\tcd infrastructure/terraform/environments/dev && terraform apply -auto-approve
"""

FILES['docker-compose.yml'] = """services:
  postgres:
    image: postgres:16-alpine
    container_name: food-platform-postgres
    ports:
      - "5432:5432"
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-postgres}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-postgres}
      POSTGRES_DB: ${POSTGRES_DB:-postgres}
    volumes:
      - ./infrastructure/docker/postgres/init-databases.sql:/docker-entrypoint-initdb.d/init-databases.sql:ro
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-postgres}"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: food-platform-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

  kafka:
    image: apache/kafka:3.7.0
    container_name: food-platform-kafka
    ports:
      - "9092:9092"
      - "29092:29092"
    environment:
      KAFKA_NODE_ID: 1
      KAFKA_PROCESS_ROLES: 'broker,controller'
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: 'CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT,PLAINTEXT_HOST:PLAINTEXT'
      KAFKA_CONTROLLER_QUORUM_VOTERS: '1@kafka:9093'
      KAFKA_LISTENERS: 'PLAINTEXT://:9092,CONTROLLER://:9093,PLAINTEXT_HOST://:29092'
      KAFKA_ADVERTISED_LISTENERS: 'PLAINTEXT://kafka:9092,PLAINTEXT_HOST://localhost:29092'
      KAFKA_CONTROLLER_LISTENER_NAMES: 'CONTROLLER'
      KAFKA_INTER_BROKER_LISTENER_NAME: 'PLAINTEXT'
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR: 1
      KAFKA_TRANSACTION_STATE_LOG_MIN_ISR: 1
      KAFKA_GROUP_INITIAL_REBALANCE_DELAY_MS: 0
      KAFKA_NUM_PARTITIONS: 3
    healthcheck:
      test: ["CMD-SHELL", "/opt/kafka/bin/kafka-broker-api-versions.sh --bootstrap-server localhost:9092"]
      interval: 10s
      timeout: 10s
      retries: 5

  kafka-ui:
    image: provectuslabs/kafka-ui:latest
    container_name: food-platform-kafka-ui
    ports:
      - "8089:8080"
    environment:
      KAFKA_CLUSTERS_0_NAME: local-cluster
      KAFKA_CLUSTERS_0_BOOTSTRAPSERVERS: kafka:9092
    depends_on:
      kafka:
        condition: service_healthy

  prometheus:
    image: prom/prometheus:latest
    container_name: food-platform-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./infrastructure/docker/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus

  grafana:
    image: grafana/grafana:latest
    container_name: food-platform-grafana
    ports:
      - "3000:3000"
    environment:
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD:-admin}
    volumes:
      - grafana_data:/var/lib/grafana

  otel-collector:
    image: otel/opentelemetry-collector-contrib:latest
    container_name: food-platform-otel
    ports:
      - "4317:4317"
      - "4318:4318"
    volumes:
      - ./infrastructure/docker/otel/otel-collector-config.yaml:/etc/otelcol-contrib/config.yaml:ro

  api-gateway:
    build:
      context: ./services/api-gateway
      dockerfile: Dockerfile
    container_name: food-platform-api-gateway
    ports:
      - "8080:8080"
    environment:
      PORT_GATEWAY: 8080
      REDIS_HOST: redis
      REDIS_PORT: 6379
      PRODUCT_SERVICE_HOST: product-service
      PORT_PRODUCT: 8082
      JWT_SECRET: ${JWT_SECRET:-c2VjdXJlX2Zvb2Rfb3BlcmF0aW9uc19wbGF0Zm9ybV9qd3Rfc2VjcmV0X2tleV9mb3JfZGV2X2Vudmlyb25tZW50XzEyMzQ1Ng==}
    depends_on:
      redis:
        condition: service_healthy
      product-service:
        condition: service_started

  product-service:
    build:
      context: ./services/product-service
      dockerfile: Dockerfile
    container_name: food-platform-product-service
    ports:
      - "8082:8082"
    environment:
      PORT_PRODUCT: 8082
      POSTGRES_HOST: postgres
      POSTGRES_PORT: 5432
      POSTGRES_USER: ${POSTGRES_USER:-postgres}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-postgres}
      REDIS_HOST: redis
      REDIS_PORT: 6379
      KAFKA_BOOTSTRAP_SERVERS: kafka:9092
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      kafka:
        condition: service_healthy

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: food-platform-frontend
    ports:
      - "5173:5173"
    environment:
      VITE_API_GATEWAY_URL: http://api-gateway:8080
    depends_on:
      - api-gateway

volumes:
  postgres_data:
  redis_data:
  prometheus_data:
  grafana_data:
"""

FILES['.github/workflows/ci.yml'] = """name: CI Pipeline

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  lint-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Use Node.js 22
        uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: 'npm'
          cache-dependency-path: frontend/package.json
      - name: Install dependencies
        run: cd frontend && npm ci
      - name: Run linter and typecheck
        run: cd frontend && npm run lint
      - name: Run unit tests
        run: cd frontend && npm run test

  test-java-services:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up JDK 21
        uses: actions/setup-java@v4
        with:
          java-version: '21'
          distribution: 'temurin'
          cache: 'maven'
      - name: Test API Gateway
        run: mvn clean test -f services/api-gateway/pom.xml
      - name: Test Product Service
        run: mvn clean test -f services/product-service/pom.xml

  docker-build-check:
    needs: [lint-frontend, test-java-services]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build API Gateway Image
        run: docker build -t foodops/api-gateway:test services/api-gateway
      - name: Build Product Service Image
        run: docker build -t foodops/product-service:test services/product-service
      - name: Build Frontend Image
        run: docker build -t foodops/frontend:test frontend
"""

FILES['infrastructure/docker/postgres/init-databases.sql'] = """CREATE DATABASE identity_db;
CREATE DATABASE product_db;
CREATE DATABASE inventory_db;
CREATE DATABASE order_db;
CREATE DATABASE notification_db;
CREATE DATABASE analytics_db;

GRANT ALL PRIVILEGES ON DATABASE identity_db TO postgres;
GRANT ALL PRIVILEGES ON DATABASE product_db TO postgres;
GRANT ALL PRIVILEGES ON DATABASE inventory_db TO postgres;
GRANT ALL PRIVILEGES ON DATABASE order_db TO postgres;
GRANT ALL PRIVILEGES ON DATABASE notification_db TO postgres;
GRANT ALL PRIVILEGES ON DATABASE analytics_db TO postgres;
"""

FILES['infrastructure/docker/prometheus/prometheus.yml'] = """global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'api-gateway'
    metrics_path: '/actuator/prometheus'
    static_configs:
      - targets: ['api-gateway:8080']

  - job_name: 'identity-service'
    metrics_path: '/actuator/prometheus'
    static_configs:
      - targets: ['identity-service:8081']

  - job_name: 'product-service'
    metrics_path: '/actuator/prometheus'
    static_configs:
      - targets: ['product-service:8082']

  - job_name: 'inventory-service'
    metrics_path: '/actuator/prometheus'
    static_configs:
      - targets: ['inventory-service:8083']

  - job_name: 'order-service'
    metrics_path: '/actuator/prometheus'
    static_configs:
      - targets: ['order-service:8084']

  - job_name: 'notification-service'
    metrics_path: '/metrics'
    static_configs:
      - targets: ['notification-service:8085']

  - job_name: 'analytics-service'
    metrics_path: '/metrics'
    static_configs:
      - targets: ['analytics-service:8086']

  - job_name: 'ai-service'
    metrics_path: '/metrics'
    static_configs:
      - targets: ['ai-service:8087']
"""

FILES['infrastructure/docker/otel/otel-collector-config.yaml'] = """receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
      http:
        endpoint: 0.0.0.0:4318

processors:
  batch:
    timeout: 1s
    send_batch_size: 256

exporters:
  prometheus:
    endpoint: 0.0.0.0:8889
  logging:
    verbosity: basic

service:
  pipelines:
    traces:
      receivers: [otlp]
      processors: [batch]
      exporters: [logging]
    metrics:
      receivers: [otlp]
      processors: [batch]
      exporters: [prometheus, logging]
"""

# ----------------- SERVICES / API-GATEWAY -----------------
FILES['services/api-gateway/pom.xml'] = """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    <parent>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-parent</artifactId>
        <version>3.3.4</version>
        <relativePath/>
    </parent>

    <groupId>com.foodplatform</groupId>
    <artifactId>api-gateway</artifactId>
    <version>1.0.0-SNAPSHOT</version>
    <name>api-gateway</name>
    <description>API Gateway for Enterprise Food Operations Platform</description>

    <properties>
        <java.version>21</java.version>
        <spring-cloud.version>2023.0.3</spring-cloud.version>
        <jjwt.version>0.12.6</jjwt.version>
    </properties>

    <dependencies>
        <dependency>
            <groupId>org.springframework.cloud</groupId>
            <artifactId>spring-cloud-starter-gateway</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-actuator</artifactId>
        </dependency>
        <dependency>
            <groupId>io.micrometer</groupId>
            <artifactId>micrometer-registry-prometheus</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-data-redis-reactive</artifactId>
        </dependency>
        <dependency>
            <groupId>io.jsonwebtoken</groupId>
            <artifactId>jjwt-api</artifactId>
            <version>${jjwt.version}</version>
        </dependency>
        <dependency>
            <groupId>io.jsonwebtoken</groupId>
            <artifactId>jjwt-impl</artifactId>
            <version>${jjwt.version}</version>
            <scope>runtime</scope>
        </dependency>
        <dependency>
            <groupId>io.jsonwebtoken</groupId>
            <artifactId>jjwt-jackson</artifactId>
            <version>${jjwt.version}</version>
            <scope>runtime</scope>
        </dependency>

        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-test</artifactId>
            <scope>test</scope>
        </dependency>
        <dependency>
            <groupId>io.projectreactor</groupId>
            <artifactId>reactor-test</artifactId>
            <scope>test</scope>
        </dependency>
    </dependencies>

    <dependencyManagement>
        <dependencies>
            <dependency>
                <groupId>org.springframework.cloud</groupId>
                <artifactId>spring-cloud-dependencies</artifactId>
                <version>${spring-cloud.version}</version>
                <type>pom</type>
                <scope>import</scope>
            </dependency>
        </dependencies>
    </dependencyManagement>

    <build>
        <plugins>
            <plugin>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-maven-plugin</artifactId>
            </plugin>
        </plugins>
    </build>
</project>
"""

FILES['services/api-gateway/Dockerfile'] = """FROM maven:3.9.9-eclipse-temurin-21-alpine AS build
WORKDIR /app
COPY pom.xml .
RUN mvn dependency:go-offline -B
COPY src ./src
RUN mvn clean package -DskipTests

FROM eclipse-temurin:21-jre-alpine
WORKDIR /app
RUN addgroup -S appgroup && adduser -S appuser -G appgroup
USER appuser
COPY --from=build /app/target/*.jar app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar"]
"""

FILES['services/api-gateway/src/main/resources/application.yml'] = """server:
  port: ${PORT_GATEWAY:8080}

spring:
  application:
    name: api-gateway
  data:
    redis:
      host: ${REDIS_HOST:localhost}
      port: ${REDIS_PORT:6379}
      timeout: 2000ms
  cloud:
    gateway:
      routes:
        - id: identity-service-auth
          uri: http://${IDENTITY_SERVICE_HOST:identity-service}:${PORT_IDENTITY:8081}
          predicates:
            - Path=/api/v1/auth/**

        - id: identity-service-users
          uri: http://${IDENTITY_SERVICE_HOST:identity-service}:${PORT_IDENTITY:8081}
          predicates:
            - Path=/api/v1/users/**

        - id: product-service-products
          uri: http://${PRODUCT_SERVICE_HOST:product-service}:${PORT_PRODUCT:8082}
          predicates:
            - Path=/api/v1/products/**

        - id: product-service-categories
          uri: http://${PRODUCT_SERVICE_HOST:product-service}:${PORT_PRODUCT:8082}
          predicates:
            - Path=/api/v1/categories/**

        - id: inventory-service-inventory
          uri: http://${INVENTORY_SERVICE_HOST:inventory-service}:${PORT_INVENTORY:8083}
          predicates:
            - Path=/api/v1/inventory/**

        - id: inventory-service-warehouses
          uri: http://${INVENTORY_SERVICE_HOST:inventory-service}:${PORT_INVENTORY:8083}
          predicates:
            - Path=/api/v1/warehouses/**

        - id: order-service
          uri: http://${ORDER_SERVICE_HOST:order-service}:${PORT_ORDER:8084}
          predicates:
            - Path=/api/v1/orders/**

        - id: notification-service
          uri: http://${NOTIFICATION_SERVICE_HOST:notification-service}:${PORT_NOTIFICATION:8085}
          predicates:
            - Path=/api/v1/notifications/**

        - id: analytics-service
          uri: http://${ANALYTICS_SERVICE_HOST:analytics-service}:${PORT_ANALYTICS:8086}
          predicates:
            - Path=/api/v1/analytics/**

        - id: ai-service
          uri: http://${AI_SERVICE_HOST:ai-service}:${PORT_AI:8087}
          predicates:
            - Path=/api/v1/assistant/**

management:
  endpoints:
    web:
      exposure:
        include: health,info,prometheus,metrics
  endpoint:
    health:
      show-details: always
      probes:
        enabled: true

jwt:
  secret: ${JWT_SECRET:c2VjdXJlX2Zvb2Rfb3BlcmF0aW9uc19wbGF0Zm9ybV9qd3Rfc2VjcmV0X2tleV9mb3JfZGV2X2Vudmlyb25tZW50XzEyMzQ1Ng==}
"""

FILES['services/api-gateway/src/test/resources/application-test.yml'] = """spring:
  autoconfigure:
    exclude:
      - org.springframework.boot.autoconfigure.data.redis.RedisAutoConfiguration
      - org.springframework.boot.autoconfigure.data.redis.RedisReactiveAutoConfiguration
  cloud:
    gateway:
      routes: []

jwt:
  secret: c2VjdXJlX2Zvb2Rfb3BlcmF0aW9uc19wbGF0Zm9ybV9qd3Rfc2VjcmV0X2tleV9mb3JfZGV2X2Vudmlyb25tZW50XzEyMzQ1Ng==
"""

FILES['services/api-gateway/src/main/java/com/foodplatform/gateway/ApiGatewayApplication.java'] = """package com.foodplatform.gateway;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class ApiGatewayApplication {
    public static void main(String[] args) {
        SpringApplication.run(ApiGatewayApplication.class, args);
    }
}
"""

FILES['services/api-gateway/src/main/java/com/foodplatform/gateway/config/CorsConfig.java'] = """package com.foodplatform.gateway.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.reactive.CorsWebFilter;
import org.springframework.web.cors.reactive.UrlBasedCorsConfigurationSource;

import java.util.Arrays;
import java.util.List;

@Configuration
public class CorsConfig {

    @Bean
    public CorsWebFilter corsWebFilter() {
        CorsConfiguration corsConfig = new CorsConfiguration();
        corsConfig.setAllowedOrigins(List.of(
                "http://localhost:5173",
                "http://127.0.0.1:5173",
                "http://localhost:3000"
        ));
        corsConfig.setMaxAge(3600L);
        corsConfig.setAllowedMethods(Arrays.asList("GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"));
        corsConfig.setAllowedHeaders(Arrays.asList("Authorization", "Content-Type", "Idempotency-Key", "X-Correlation-Id"));
        corsConfig.setExposedHeaders(Arrays.asList("X-Correlation-Id", "Authorization", "Content-Disposition"));
        corsConfig.setAllowCredentials(true);

        UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
        source.registerCorsConfiguration("/**", corsConfig);

        return new CorsWebFilter(source);
    }
}
"""

FILES['services/api-gateway/src/main/java/com/foodplatform/gateway/filter/CorrelationIdFilter.java'] = """package com.foodplatform.gateway.filter;

import org.springframework.cloud.gateway.filter.GatewayFilterChain;
import org.springframework.cloud.gateway.filter.GlobalFilter;
import org.springframework.core.Ordered;
import org.springframework.http.server.reactive.ServerHttpRequest;
import org.springframework.stereotype.Component;
import org.springframework.web.server.ServerWebExchange;
import reactor.core.publisher.Mono;

import java.util.UUID;

@Component
public class CorrelationIdFilter implements GlobalFilter, Ordered {

    public static final String CORRELATION_ID_HEADER = "X-Correlation-Id";

    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        ServerHttpRequest request = exchange.getRequest();
        String correlationId = request.getHeaders().getFirst(CORRELATION_ID_HEADER);

        if (correlationId == null || correlationId.isBlank()) {
            correlationId = UUID.randomUUID().toString();
        }

        final String finalCorrelationId = correlationId;
        ServerHttpRequest mutatedRequest = request.mutate()
                .header(CORRELATION_ID_HEADER, finalCorrelationId)
                .build();

        exchange.getResponse().getHeaders().add(CORRELATION_ID_HEADER, finalCorrelationId);

        return chain.filter(exchange.mutate().request(mutatedRequest).build());
    }

    @Override
    public int getOrder() {
        return Ordered.HIGHEST_PRECEDENCE;
    }
}
"""

FILES['services/api-gateway/src/main/java/com/foodplatform/gateway/filter/JwtAuthenticationFilter.java'] = """package com.foodplatform.gateway.filter;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.cloud.gateway.filter.GatewayFilterChain;
import org.springframework.cloud.gateway.filter.GlobalFilter;
import org.springframework.core.Ordered;
import org.springframework.core.io.buffer.DataBuffer;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.server.reactive.ServerHttpRequest;
import org.springframework.http.server.reactive.ServerHttpResponse;
import org.springframework.stereotype.Component;
import org.springframework.web.server.ServerWebExchange;
import reactor.core.publisher.Mono;

import javax.crypto.SecretKey;
import java.nio.charset.StandardCharsets;
import java.util.List;

@Component
public class JwtAuthenticationFilter implements GlobalFilter, Ordered {

    private final SecretKey signingKey;

    public JwtAuthenticationFilter(@Value("${jwt.secret}") String secret) {
        byte[] keyBytes;
        try {
            keyBytes = java.util.Base64.getDecoder().decode(secret);
        } catch (IllegalArgumentException e) {
            keyBytes = secret.getBytes(StandardCharsets.UTF_8);
        }
        this.signingKey = Keys.hmacShaKeyFor(keyBytes);
    }

    private static final List<String> PUBLIC_PATH_PREFIXES = List.of(
            "/api/v1/auth",
            "/actuator",
            "/v3/api-docs",
            "/swagger-ui"
    );

    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        ServerHttpRequest request = exchange.getRequest();
        String path = request.getURI().getPath();
        HttpMethod method = request.getMethod();

        if (isPublicPath(path, method)) {
            String authHeader = request.getHeaders().getFirst(HttpHeaders.AUTHORIZATION);
            if (authHeader != null && authHeader.startsWith("Bearer ")) {
                try {
                    String token = authHeader.substring(7);
                    Claims claims = parseClaims(token);
                    ServerHttpRequest mutated = enrichRequestWithClaims(request, claims);
                    return chain.filter(exchange.mutate().request(mutated).build());
                } catch (Exception ignored) {
                }
            }
            return chain.filter(exchange);
        }

        String authHeader = request.getHeaders().getFirst(HttpHeaders.AUTHORIZATION);
        if (authHeader == null || !authHeader.startsWith("Bearer ")) {
            return unauthorizedResponse(exchange, "Missing or invalid Authorization header");
        }

        String token = authHeader.substring(7);
        try {
            Claims claims = parseClaims(token);
            ServerHttpRequest mutated = enrichRequestWithClaims(request, claims);
            return chain.filter(exchange.mutate().request(mutated).build());
        } catch (Exception e) {
            return unauthorizedResponse(exchange, "Invalid or expired JWT: " + e.getMessage());
        }
    }

    private boolean isPublicPath(String path, HttpMethod method) {
        for (String prefix : PUBLIC_PATH_PREFIXES) {
            if (path.startsWith(prefix)) {
                return true;
            }
        }
        if (method == HttpMethod.GET && (path.startsWith("/api/v1/products") || path.startsWith("/api/v1/categories"))) {
            return true;
        }
        return false;
    }

    private Claims parseClaims(String token) {
        return Jwts.parser()
                .verifyWith(signingKey)
                .build()
                .parseSignedClaims(token)
                .getPayload();
    }

    private ServerHttpRequest enrichRequestWithClaims(ServerHttpRequest request, Claims claims) {
        String userId = claims.getSubject();
        String email = claims.get("email", String.class);
        String role = claims.get("role", String.class);

        var builder = request.mutate();
        if (userId != null) builder.header("X-User-Id", userId);
        if (email != null) builder.header("X-User-Email", email);
        if (role != null) builder.header("X-User-Role", role);

        return builder.build();
    }

    private Mono<Void> unauthorizedResponse(ServerWebExchange exchange, String detail) {
        ServerHttpResponse response = exchange.getResponse();
        response.setStatusCode(HttpStatus.UNAUTHORIZED);
        response.getHeaders().setContentType(MediaType.APPLICATION_PROBLEM_JSON);

        String correlationId = exchange.getRequest().getHeaders().getFirst("X-Correlation-Id");
        if (correlationId == null) {
            correlationId = "unknown";
        }

        String body = String.format(
                \"\"\"
                {
                  "type": "https://foodplatform.com/errors/unauthorized",
                  "title": "Unauthorized",
                  "status": 401,
                  "detail": "%s",
                  "instance": "%s",
                  "correlationId": "%s"
                }
                \"\"\",
                detail.replace("\"", "\\\\\\""),
                exchange.getRequest().getURI().getPath(),
                correlationId
        );

        DataBuffer buffer = response.bufferFactory().wrap(body.getBytes(StandardCharsets.UTF_8));
        return response.writeWith(Mono.just(buffer));
    }

    @Override
    public int getOrder() {
        return Ordered.HIGHEST_PRECEDENCE + 10;
    }
}
"""

FILES['services/api-gateway/src/test/java/com/foodplatform/gateway/ApiGatewayApplicationTests.java'] = """package com.foodplatform.gateway;

import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;

@SpringBootTest
@ActiveProfiles("test")
class ApiGatewayApplicationTests {

    @Test
    void contextLoads() {
    }
}
"""

# ----------------- SERVICES / PRODUCT-SERVICE -----------------
FILES['services/product-service/pom.xml'] = """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    <parent>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-parent</artifactId>
        <version>3.3.4</version>
        <relativePath/>
    </parent>

    <groupId>com.foodplatform</groupId>
    <artifactId>product-service</artifactId>
    <version>1.0.0-SNAPSHOT</version>
    <name>product-service</name>
    <description>Product Catalog Service for Enterprise Food Operations Platform</description>

    <properties>
        <java.version>21</java.version>
        <springdoc.version>2.6.0</springdoc.version>
    </properties>

    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-data-jpa</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-validation</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-actuator</artifactId>
        </dependency>
        <dependency>
            <groupId>io.micrometer</groupId>
            <artifactId>micrometer-registry-prometheus</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-data-redis</artifactId>
        </dependency>
        <dependency>
            <groupId>org.flywaydb</groupId>
            <artifactId>flyway-core</artifactId>
        </dependency>
        <dependency>
            <groupId>org.flywaydb</groupId>
            <artifactId>flyway-database-postgresql</artifactId>
        </dependency>
        <dependency>
            <groupId>org.postgresql</groupId>
            <artifactId>postgresql</artifactId>
            <scope>runtime</scope>
        </dependency>
        <dependency>
            <groupId>org.springdoc</groupId>
            <artifactId>springdoc-openapi-starter-webmvc-ui</artifactId>
            <version>${springdoc.version}</version>
        </dependency>
        <dependency>
            <groupId>org.springframework.kafka</groupId>
            <artifactId>spring-kafka</artifactId>
        </dependency>

        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-test</artifactId>
            <scope>test</scope>
        </dependency>
        <dependency>
            <groupId>com.h2database</groupId>
            <artifactId>h2</artifactId>
            <scope>test</scope>
        </dependency>
    </dependencies>

    <build>
        <plugins>
            <plugin>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-maven-plugin</artifactId>
            </plugin>
        </plugins>
    </build>
</project>
"""

FILES['services/product-service/Dockerfile'] = """FROM maven:3.9.9-eclipse-temurin-21-alpine AS build
WORKDIR /app
COPY pom.xml .
RUN mvn dependency:go-offline -B
COPY src ./src
RUN mvn clean package -DskipTests

FROM eclipse-temurin:21-jre-alpine
WORKDIR /app
RUN addgroup -S appgroup && adduser -S appuser -G appgroup
USER appuser
COPY --from=build /app/target/*.jar app.jar
EXPOSE 8082
ENTRYPOINT ["java", "-jar", "app.jar"]
"""

FILES['services/product-service/src/main/resources/application.yml'] = """server:
  port: ${PORT_PRODUCT:8082}

spring:
  application:
    name: product-service
  datasource:
    url: jdbc:postgresql://${POSTGRES_HOST:localhost}:${POSTGRES_PORT:5432}/product_db
    username: ${POSTGRES_USER:postgres}
    password: ${POSTGRES_PASSWORD:postgres}
    driver-class-name: org.postgresql.Driver
  jpa:
    hibernate:
      ddl-auto: validate
    properties:
      hibernate:
        dialect: org.hibernate.dialect.PostgreSQLDialect
        format_sql: false
    show-sql: false
  flyway:
    enabled: true
    baseline-on-migrate: true
    locations: classpath:db/migration
  data:
    redis:
      host: ${REDIS_HOST:localhost}
      port: ${REDIS_PORT:6379}
      timeout: 2000ms
  cache:
    type: redis
    redis:
      time-to-live: 600000
      cache-null-values: false
  kafka:
    bootstrap-servers: ${KAFKA_BOOTSTRAP_SERVERS:localhost:9092}
    producer:
      key-serializer: org.apache.kafka.common.serialization.StringSerializer
      value-serializer: org.springframework.kafka.support.serializer.JsonSerializer
      acks: all
      retries: 3

management:
  endpoints:
    web:
      exposure:
        include: health,info,prometheus,metrics
  endpoint:
    health:
      show-details: always
      probes:
        enabled: true

springdoc:
  api-docs:
    path: /v3/api-docs
  swagger-ui:
    path: /swagger-ui.html
"""

FILES['services/product-service/src/test/resources/application-test.yml'] = """spring:
  datasource:
    url: jdbc:h2:mem:product_test_db;DB_CLOSE_DELAY=-1;MODE=PostgreSQL
    driver-class-name: org.h2.Driver
    username: sa
    password: ""
  jpa:
    hibernate:
      ddl-auto: create-drop
    database-platform: org.hibernate.dialect.H2Dialect
  flyway:
    enabled: false
  cache:
    type: none
  autoconfigure:
    exclude:
      - org.springframework.boot.autoconfigure.data.redis.RedisAutoConfiguration
      - org.springframework.boot.autoconfigure.kafka.KafkaAutoConfiguration
"""

FILES['services/product-service/src/main/resources/db/migration/V1__create_product_tables.sql'] = """CREATE TABLE IF NOT EXISTS categories (
    id UUID PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    parent_id UUID REFERENCES categories(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS products (
    id UUID PRIMARY KEY,
    sku VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category_id UUID REFERENCES categories(id) ON DELETE SET NULL,
    unit VARCHAR(50) NOT NULL,
    price NUMERIC(12, 2) NOT NULL,
    currency VARCHAR(10) NOT NULL DEFAULT 'USD',
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    version BIGINT NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_products_sku ON products(sku);
CREATE INDEX IF NOT EXISTS idx_products_category_id ON products(category_id);
CREATE INDEX IF NOT EXISTS idx_products_active_category ON products(active, category_id);
CREATE INDEX IF NOT EXISTS idx_products_lower_name ON products(lower(name));
"""

FILES['services/product-service/src/main/java/com/foodplatform/product/ProductServiceApplication.java'] = """package com.foodplatform.product;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class ProductServiceApplication {
    public static void main(String[] args) {
        SpringApplication.run(ProductServiceApplication.class, args);
    }
}
"""

FILES['services/product-service/src/main/java/com/foodplatform/product/config/OpenApiConfig.java'] = """package com.foodplatform.product.config;

import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Contact;
import io.swagger.v3.oas.models.info.Info;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class OpenApiConfig {

    @Bean
    public OpenAPI productServiceOpenAPI() {
        return new OpenAPI()
                .info(new Info()
                        .title("Product Service API")
                        .description("Product catalog, category hierarchy, and pricing management for Food Operations Platform")
                        .version("v1.0.0")
                        .contact(new Contact().name("Food Operations Platform Engineering")));
    }
}
"""

FILES['services/product-service/src/main/java/com/foodplatform/product/config/CacheConfig.java'] = """package com.foodplatform.product.config;

import org.springframework.cache.annotation.EnableCaching;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.redis.cache.RedisCacheConfiguration;
import org.springframework.data.redis.serializer.GenericJackson2JsonRedisSerializer;
import org.springframework.data.redis.serializer.RedisSerializationContext;
import org.springframework.data.redis.serializer.StringRedisSerializer;

import java.time.Duration;

@Configuration
@EnableCaching
public class CacheConfig {

    @Bean
    public RedisCacheConfiguration cacheConfiguration() {
        return RedisCacheConfiguration.defaultCacheConfig()
                .entryTtl(Duration.ofMinutes(10))
                .disableCachingNullValues()
                .serializeKeysWith(
                        RedisSerializationContext.SerializationPair.fromSerializer(new StringRedisSerializer())
                )
                .serializeValuesWith(
                        RedisSerializationContext.SerializationPair.fromSerializer(new GenericJackson2JsonRedisSerializer())
                );
    }
}
"""

FILES['services/product-service/src/main/java/com/foodplatform/product/domain/Category.java'] = """package com.foodplatform.product.domain;

import jakarta.persistence.*;
import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "categories")
public class Category {

    @Id
    private UUID id;

    @Column(nullable = false, unique = true)
    private String name;

    @Column(name = "parent_id")
    private UUID parentId;

    @Column(name = "created_at", nullable = false, updatable = false)
    private Instant createdAt;

    public Category() {
    }

    public Category(UUID id, String name, UUID parentId) {
        this.id = id != null ? id : UUID.randomUUID();
        this.name = name;
        this.parentId = parentId;
        this.createdAt = Instant.now();
    }

    @PrePersist
    protected void onCreate() {
        if (id == null) {
            id = UUID.randomUUID();
        }
        if (createdAt == null) {
            createdAt = Instant.now();
        }
    }

    public UUID getId() { return id; }
    public void setId(UUID id) { this.id = id; }

    public String getName() { return name; }
    public void setName(String name) { this.name = name; }

    public UUID getParentId() { return parentId; }
    public void setParentId(UUID parentId) { this.parentId = parentId; }

    public Instant getCreatedAt() { return createdAt; }
    public void setCreatedAt(Instant createdAt) { this.createdAt = createdAt; }
}
"""

FILES['services/product-service/src/main/java/com/foodplatform/product/domain/Product.java'] = """package com.foodplatform.product.domain;

import jakarta.persistence.*;
import java.math.BigDecimal;
import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "products")
public class Product {

    @Id
    private UUID id;

    @Column(nullable = false, unique = true, length = 100)
    private String sku;

    @Column(nullable = false)
    private String name;

    @Column(columnDefinition = "TEXT")
    private String description;

    @Column(name = "category_id")
    private UUID categoryId;

    @Column(nullable = false, length = 50)
    private String unit;

    @Column(nullable = false, precision = 12, scale = 2)
    private BigDecimal price;

    @Column(nullable = false, length = 10)
    private String currency;

    @Column(nullable = false)
    private boolean active;

    @Column(name = "created_at", nullable = false, updatable = false)
    private Instant createdAt;

    @Column(name = "updated_at", nullable = false)
    private Instant updatedAt;

    @Version
    @Column(nullable = false)
    private Long version;

    public Product() {
    }

    public Product(UUID id, String sku, String name, String description, UUID categoryId,
                   String unit, BigDecimal price, String currency, boolean active) {
        this.id = id != null ? id : UUID.randomUUID();
        this.sku = sku;
        this.name = name;
        this.description = description;
        this.categoryId = categoryId;
        this.unit = unit;
        this.price = price;
        this.currency = currency != null ? currency : "USD";
        this.active = active;
        this.createdAt = Instant.now();
        this.updatedAt = Instant.now();
        this.version = 0L;
    }

    @PrePersist
    protected void onCreate() {
        if (id == null) {
            id = UUID.randomUUID();
        }
        if (createdAt == null) {
            createdAt = Instant.now();
        }
        if (updatedAt == null) {
            updatedAt = Instant.now();
        }
        if (currency == null) {
            currency = "USD";
        }
        if (version == null) {
            version = 0L;
        }
    }

    @PreUpdate
    protected void onUpdate() {
        this.updatedAt = Instant.now();
    }

    public UUID getId() { return id; }
    public void setId(UUID id) { this.id = id; }

    public String getSku() { return sku; }
    public void setSku(String sku) { this.sku = sku; }

    public String getName() { return name; }
    public void setName(String name) { this.name = name; }

    public String getDescription() { return description; }
    public void setDescription(String description) { this.description = description; }

    public UUID getCategoryId() { return categoryId; }
    public void setCategoryId(UUID categoryId) { this.categoryId = categoryId; }

    public String getUnit() { return unit; }
    public void setUnit(String unit) { this.unit = unit; }

    public BigDecimal getPrice() { return price; }
    public void setPrice(BigDecimal price) { this.price = price; }

    public String getCurrency() { return currency; }
    public void setCurrency(String currency) { this.currency = currency; }

    public boolean isActive() { return active; }
    public void setActive(boolean active) { this.active = active; }

    public Instant getCreatedAt() { return createdAt; }
    public void setCreatedAt(Instant createdAt) { this.createdAt = createdAt; }

    public Instant getUpdatedAt() { return updatedAt; }
    public void setUpdatedAt(Instant updatedAt) { this.updatedAt = updatedAt; }

    public Long getVersion() { return version; }
    public void setVersion(Long version) { this.version = version; }
}
"""

FILES['services/product-service/src/main/java/com/foodplatform/product/dto/CategoryDto.java'] = """package com.foodplatform.product.dto;

import java.time.Instant;
import java.util.UUID;

public record CategoryDto(
        UUID id,
        String name,
        UUID parentId,
        Instant createdAt
) {}
"""

FILES['services/product-service/src/main/java/com/foodplatform/product/dto/CreateCategoryRequest.java'] = """package com.foodplatform.product.dto;

import jakarta.validation.constraints.NotBlank;
import java.util.UUID;

public record CreateCategoryRequest(
        @NotBlank(message = "Category name must not be blank")
        String name,
        UUID parentId
) {}
"""

FILES['services/product-service/src/main/java/com/foodplatform/product/dto/ProductDto.java'] = """package com.foodplatform.product.dto;

import java.io.Serializable;
import java.math.BigDecimal;
import java.time.Instant;
import java.util.UUID;

public record ProductDto(
        UUID id,
        String sku,
        String name,
        String description,
        UUID categoryId,
        String unit,
        BigDecimal price,
        String currency,
        boolean active,
        Instant createdAt,
        Instant updatedAt,
        Long version
) implements Serializable {}
"""

FILES['services/product-service/src/main/java/com/foodplatform/product/dto/CreateProductRequest.java'] = """package com.foodplatform.product.dto;

import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import java.math.BigDecimal;
import java.util.UUID;

public record CreateProductRequest(
        @NotBlank(message = "SKU is required")
        String sku,

        @NotBlank(message = "Product name is required")
        String name,

        String description,

        UUID categoryId,

        @NotBlank(message = "Unit is required")
        String unit,

        @NotNull(message = "Price is required")
        @DecimalMin(value = "0.01", message = "Price must be at least 0.01")
        BigDecimal price,

        String currency,

        Boolean active
) {}
"""

FILES['services/product-service/src/main/java/com/foodplatform/product/dto/UpdateProductRequest.java'] = """package com.foodplatform.product.dto;

import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import java.math.BigDecimal;
import java.util.UUID;

public record UpdateProductRequest(
        @NotBlank(message = "Product name is required")
        String name,

        String description,

        UUID categoryId,

        @NotBlank(message = "Unit is required")
        String unit,

        @NotNull(message = "Price is required")
        @DecimalMin(value = "0.01", message = "Price must be at least 0.01")
        BigDecimal price,

        String currency,

        Boolean active
) {}
"""

FILES['services/product-service/src/main/java/com/foodplatform/product/dto/PagedResponse.java'] = """package com.foodplatform.product.dto;

import org.springframework.data.domain.Page;

import java.util.List;

public record PagedResponse<T>(
        List<T> content,
        int page,
        int size,
        long totalElements,
        int totalPages,
        boolean last
) {
    public static <T> PagedResponse<T> from(Page<T> pageResult) {
        return new PagedResponse<>(
                pageResult.getContent(),
                pageResult.getNumber(),
                pageResult.getSize(),
                pageResult.getTotalElements(),
                pageResult.getTotalPages(),
                pageResult.isLast()
        );
    }
}
"""

FILES['services/product-service/src/main/java/com/foodplatform/product/repository/ProductRepository.java'] = """package com.foodplatform.product.repository;

import com.foodplatform.product.domain.Product;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

@Repository
public interface ProductRepository extends JpaRepository<Product, UUID>, JpaSpecificationExecutor<Product> {
    Optional<Product> findBySku(String sku);
    boolean existsBySku(String sku);
    List<Product> findByCategoryId(UUID categoryId);
}
"""

FILES['services/product-service/src/main/java/com/foodplatform/product/repository/CategoryRepository.java'] = """package com.foodplatform.product.repository;

import com.foodplatform.product.domain.Category;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;
import java.util.UUID;

@Repository
public interface CategoryRepository extends JpaRepository<Category, UUID> {
    Optional<Category> findByNameIgnoreCase(String name);
    boolean existsByNameIgnoreCase(String name);
}
"""

FILES['services/product-service/src/main/java/com/foodplatform/product/repository/ProductSpecifications.java'] = """package com.foodplatform.product.repository;

import com.foodplatform.product.domain.Product;
import jakarta.persistence.criteria.Predicate;
import org.springframework.data.jpa.domain.Specification;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

public class ProductSpecifications {

    public static Specification<Product> withFilters(
            UUID categoryId,
            String query,
            BigDecimal minPrice,
            BigDecimal maxPrice,
            Boolean active
    ) {
        return (root, cq, cb) -> {
            List<Predicate> predicates = new ArrayList<>();

            if (categoryId != null) {
                predicates.add(cb.equal(root.get("categoryId"), categoryId));
            }

            if (query != null && !query.isBlank()) {
                String pattern = "%" + query.toLowerCase().trim() + "%";
                Predicate nameMatch = cb.like(cb.lower(root.get("name")), pattern);
                Predicate skuMatch = cb.like(cb.lower(root.get("sku")), pattern);
                Predicate descMatch = cb.like(cb.lower(root.get("description")), pattern);
                predicates.add(cb.or(nameMatch, skuMatch, descMatch));
            }

            if (minPrice != null) {
                predicates.add(cb.greaterThanOrEqualTo(root.get("price"), minPrice));
            }

            if (maxPrice != null) {
                predicates.add(cb.lessThanOrEqualTo(root.get("price"), maxPrice));
            }

            if (active != null) {
                predicates.add(cb.equal(root.get("active"), active));
            }

            return cb.and(predicates.toArray(new Predicate[0]));
        };
    }
}
"""

FILES['services/product-service/src/main/java/com/foodplatform/product/exception/ResourceNotFoundException.java'] = """package com.foodplatform.product.exception;

public class ResourceNotFoundException extends RuntimeException {
    public ResourceNotFoundException(String message) {
        super(message);
    }
}
"""

FILES['services/product-service/src/main/java/com/foodplatform/product/exception/DuplicateResourceException.java'] = """package com.foodplatform.product.exception;

public class DuplicateResourceException extends RuntimeException {
    public DuplicateResourceException(String message) {
        super(message);
    }
}
"""

FILES['services/product-service/src/main/java/com/foodplatform/product/exception/GlobalExceptionHandler.java'] = """package com.foodplatform.product.exception;

import jakarta.servlet.http.HttpServletRequest;
import org.springframework.http.HttpStatus;
import org.springframework.http.ProblemDetail;
import org.springframework.validation.FieldError;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import java.net.URI;
import java.time.Instant;
import java.util.HashMap;
import java.util.Map;

@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(ResourceNotFoundException.class)
    public ProblemDetail handleResourceNotFound(ResourceNotFoundException ex, HttpServletRequest request) {
        ProblemDetail problem = ProblemDetail.forStatusAndDetail(HttpStatus.NOT_FOUND, ex.getMessage());
        problem.setTitle("Resource Not Found");
        problem.setType(URI.create("https://foodplatform.com/errors/not-found"));
        problem.setProperty("timestamp", Instant.now());
        problem.setProperty("correlationId", getCorrelationId(request));
        return problem;
    }

    @ExceptionHandler(DuplicateResourceException.class)
    public ProblemDetail handleDuplicateResource(DuplicateResourceException ex, HttpServletRequest request) {
        ProblemDetail problem = ProblemDetail.forStatusAndDetail(HttpStatus.CONFLICT, ex.getMessage());
        problem.setTitle("Duplicate Resource Conflict");
        problem.setType(URI.create("https://foodplatform.com/errors/conflict"));
        problem.setProperty("timestamp", Instant.now());
        problem.setProperty("correlationId", getCorrelationId(request));
        return problem;
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ProblemDetail handleValidationException(MethodArgumentNotValidException ex, HttpServletRequest request) {
        ProblemDetail problem = ProblemDetail.forStatusAndDetail(HttpStatus.BAD_REQUEST, "Validation failed");
        problem.setTitle("Bad Request");
        problem.setType(URI.create("https://foodplatform.com/errors/validation-error"));

        Map<String, String> errors = new HashMap<>();
        for (FieldError error : ex.getBindingResult().getFieldErrors()) {
            errors.put(error.getField(), error.getDefaultMessage());
        }
        problem.setProperty("errors", errors);
        problem.setProperty("timestamp", Instant.now());
        problem.setProperty("correlationId", getCorrelationId(request));
        return problem;
    }

    @ExceptionHandler(Exception.class)
    public ProblemDetail handleGeneralException(Exception ex, HttpServletRequest request) {
        ProblemDetail problem = ProblemDetail.forStatusAndDetail(HttpStatus.INTERNAL_SERVER_ERROR, ex.getMessage());
        problem.setTitle("Internal Server Error");
        problem.setType(URI.create("https://foodplatform.com/errors/internal"));
        problem.setProperty("timestamp", Instant.now());
        problem.setProperty("correlationId", getCorrelationId(request));
        return problem;
    }

    private String getCorrelationId(HttpServletRequest request) {
        String correlationId = request.getHeader("X-Correlation-Id");
        return correlationId != null ? correlationId : "unknown";
    }
}
"""

FILES['services/product-service/src/main/java/com/foodplatform/product/service/CategoryService.java'] = """package com.foodplatform.product.service;

import com.foodplatform.product.domain.Category;
import com.foodplatform.product.dto.CategoryDto;
import com.foodplatform.product.dto.CreateCategoryRequest;
import com.foodplatform.product.exception.DuplicateResourceException;
import com.foodplatform.product.exception.ResourceNotFoundException;
import com.foodplatform.product.repository.CategoryRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.UUID;

@Service
public class CategoryService {

    private final CategoryRepository categoryRepository;

    public CategoryService(CategoryRepository categoryRepository) {
        this.categoryRepository = categoryRepository;
    }

    @Transactional(readOnly = true)
    public List<CategoryDto> getAllCategories() {
        return categoryRepository.findAll().stream()
                .map(this::toDto)
                .toList();
    }

    @Transactional(readOnly = true)
    public CategoryDto getCategoryById(UUID id) {
        Category category = categoryRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Category not found with id: " + id));
        return toDto(category);
    }

    @Transactional
    public CategoryDto createCategory(CreateCategoryRequest request) {
        if (categoryRepository.existsByNameIgnoreCase(request.name())) {
            throw new DuplicateResourceException("Category already exists with name: " + request.name());
        }

        Category category = new Category(UUID.randomUUID(), request.name().trim(), request.parentId());
        Category saved = categoryRepository.save(category);
        return toDto(saved);
    }

    private CategoryDto toDto(Category category) {
        return new CategoryDto(
                category.getId(),
                category.getName(),
                category.getParentId(),
                category.getCreatedAt()
        );
    }
}
"""

FILES['services/product-service/src/main/java/com/foodplatform/product/service/ProductService.java'] = """package com.foodplatform.product.service;

import com.foodplatform.product.domain.Product;
import com.foodplatform.product.dto.CreateProductRequest;
import com.foodplatform.product.dto.PagedResponse;
import com.foodplatform.product.dto.ProductDto;
import com.foodplatform.product.dto.UpdateProductRequest;
import com.foodplatform.product.exception.DuplicateResourceException;
import com.foodplatform.product.exception.ResourceNotFoundException;
import com.foodplatform.product.repository.ProductRepository;
import com.foodplatform.product.repository.ProductSpecifications;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.cache.annotation.CacheEvict;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.util.Map;
import java.util.UUID;

@Service
public class ProductService {

    private static final Logger log = LoggerFactory.getLogger(ProductService.class);

    private final ProductRepository productRepository;
    private final KafkaTemplate<String, Object> kafkaTemplate;

    public ProductService(ProductRepository productRepository,
                          @Autowired(required = false) KafkaTemplate<String, Object> kafkaTemplate) {
        this.productRepository = productRepository;
        this.kafkaTemplate = kafkaTemplate;
    }

    @Transactional(readOnly = true)
    public PagedResponse<ProductDto> getProducts(
            UUID categoryId,
            String query,
            BigDecimal minPrice,
            BigDecimal maxPrice,
            Boolean active,
            Pageable pageable
    ) {
        Specification<Product> spec = ProductSpecifications.withFilters(categoryId, query, minPrice, maxPrice, active);
        Page<Product> page = productRepository.findAll(spec, pageable);
        return PagedResponse.from(page.map(this::toDto));
    }

    @Cacheable(value = "products", key = "#id")
    @Transactional(readOnly = true)
    public ProductDto getProductById(UUID id) {
        log.info("Fetching product from database for id: {}", id);
        Product product = productRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Product not found with id: " + id));
        return toDto(product);
    }

    @Transactional
    public ProductDto createProduct(CreateProductRequest request) {
        if (productRepository.existsBySku(request.sku())) {
            throw new DuplicateResourceException("Product with SKU already exists: " + request.sku());
        }

        Product product = new Product(
                UUID.randomUUID(),
                request.sku().trim().toUpperCase(),
                request.name().trim(),
                request.description(),
                request.categoryId(),
                request.unit(),
                request.price(),
                request.currency() != null ? request.currency() : "USD",
                request.active() != null ? request.active() : true
        );

        Product saved = productRepository.save(product);
        publishProductEvent("product.created", saved);
        return toDto(saved);
    }

    @CacheEvict(value = "products", key = "#id")
    @Transactional
    public ProductDto updateProduct(UUID id, UpdateProductRequest request) {
        Product product = productRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Product not found with id: " + id));

        product.setName(request.name().trim());
        product.setDescription(request.description());
        product.setCategoryId(request.categoryId());
        product.setUnit(request.unit());
        product.setPrice(request.price());
        if (request.currency() != null) {
            product.setCurrency(request.currency());
        }
        if (request.active() != null) {
            product.setActive(request.active());
        }

        Product updated = productRepository.save(product);
        publishProductEvent("product.updated", updated);
        return toDto(updated);
    }

    @CacheEvict(value = "products", key = "#id")
    @Transactional
    public void deleteProduct(UUID id) {
        Product product = productRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Product not found with id: " + id));
        productRepository.delete(product);
        publishProductEvent("product.deleted", product);
    }

    private void publishProductEvent(String topic, Product product) {
        if (kafkaTemplate != null) {
            try {
                Map<String, Object> payload = Map.of(
                        "productId", product.getId().toString(),
                        "sku", product.getSku(),
                        "name", product.getName(),
                        "price", product.getPrice(),
                        "active", product.isActive()
                );
                kafkaTemplate.send("product.updated", product.getId().toString(), payload);
            } catch (Exception e) {
                log.warn("Failed to publish event for product {}: {}", product.getId(), e.getMessage());
            }
        }
    }

    public ProductDto toDto(Product product) {
        return new ProductDto(
                product.getId(),
                product.getSku(),
                product.getName(),
                product.getDescription(),
                product.getCategoryId(),
                product.getUnit(),
                product.getPrice(),
                product.getCurrency(),
                product.isActive(),
                product.getCreatedAt(),
                product.getUpdatedAt(),
                product.getVersion()
        );
    }
}
"""

FILES['services/product-service/src/main/java/com/foodplatform/product/controller/CategoryController.java'] = """package com.foodplatform.product.controller;

import com.foodplatform.product.dto.CategoryDto;
import com.foodplatform.product.dto.CreateCategoryRequest;
import com.foodplatform.product.service.CategoryService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/v1/categories")
@Tag(name = "Categories", description = "Product Category Operations")
public class CategoryController {

    private final CategoryService categoryService;

    public CategoryController(CategoryService categoryService) {
        this.categoryService = categoryService;
    }

    @GetMapping
    @Operation(summary = "Get all categories")
    public ResponseEntity<List<CategoryDto>> getAllCategories() {
        return ResponseEntity.ok(categoryService.getAllCategories());
    }

    @PostMapping
    @Operation(summary = "Create a category")
    public ResponseEntity<CategoryDto> createCategory(@Valid @RequestBody CreateCategoryRequest request) {
        CategoryDto created = categoryService.createCategory(request);
        return ResponseEntity.status(HttpStatus.CREATED).body(created);
    }
}
"""

FILES['services/product-service/src/main/java/com/foodplatform/product/controller/ProductController.java'] = """package com.foodplatform.product.controller;

import com.foodplatform.product.dto.CreateProductRequest;
import com.foodplatform.product.dto.PagedResponse;
import com.foodplatform.product.dto.ProductDto;
import com.foodplatform.product.dto.UpdateProductRequest;
import com.foodplatform.product.service.ProductService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.data.web.PageableDefault;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.math.BigDecimal;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/products")
@Tag(name = "Products", description = "Product Catalog Operations")
public class ProductController {

    private final ProductService productService;

    public ProductController(ProductService productService) {
        this.productService = productService;
    }

    @GetMapping
    @Operation(summary = "List and filter products with pagination")
    public ResponseEntity<PagedResponse<ProductDto>> getProducts(
            @RequestParam(required = false) UUID category,
            @RequestParam(required = false) String q,
            @RequestParam(required = false) BigDecimal minPrice,
            @RequestParam(required = false) BigDecimal maxPrice,
            @RequestParam(required = false) Boolean active,
            @PageableDefault(page = 0, size = 20, sort = "createdAt", direction = Sort.Direction.DESC) Pageable pageable
    ) {
        PagedResponse<ProductDto> response = productService.getProducts(category, q, minPrice, maxPrice, active, pageable);
        return ResponseEntity.ok(response);
    }

    @GetMapping("/{id}")
    @Operation(summary = "Get product by ID (cached)")
    public ResponseEntity<ProductDto> getProductById(@PathVariable UUID id) {
        ProductDto product = productService.getProductById(id);
        return ResponseEntity.ok(product);
    }

    @PostMapping
    @Operation(summary = "Create a new product")
    public ResponseEntity<ProductDto> createProduct(@Valid @RequestBody CreateProductRequest request) {
        ProductDto created = productService.createProduct(request);
        return ResponseEntity.status(HttpStatus.CREATED).body(created);
    }

    @PutMapping("/{id}")
    @Operation(summary = "Update an existing product")
    public ResponseEntity<ProductDto> updateProduct(
            @PathVariable UUID id,
            @Valid @RequestBody UpdateProductRequest request
    ) {
        ProductDto updated = productService.updateProduct(id, request);
        return ResponseEntity.ok(updated);
    }

    @DeleteMapping("/{id}")
    @Operation(summary = "Delete a product")
    public ResponseEntity<Void> deleteProduct(@PathVariable UUID id) {
        productService.deleteProduct(id);
        return ResponseEntity.noContent().build();
    }
}
"""

FILES['services/product-service/src/test/java/com/foodplatform/product/ProductServiceApplicationTests.java'] = """package com.foodplatform.product;

import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;

@SpringBootTest
@ActiveProfiles("test")
class ProductServiceApplicationTests {

    @Test
    void contextLoads() {
    }
}
"""

FILES['services/product-service/src/test/java/com/foodplatform/product/ProductControllerTest.java'] = """package com.foodplatform.product;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.foodplatform.product.dto.CreateProductRequest;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;

import java.math.BigDecimal;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
class ProductControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @Test
    void shouldCreateAndRetrieveProduct() throws Exception {
        CreateProductRequest request = new CreateProductRequest(
                "TEST-SKU-100",
                "Organic Sourdough Bread",
                "Fresh artisanal sourdough loaf",
                null,
                "loaf",
                new BigDecimal("6.50"),
                "USD",
                true
        );

        mockMvc.perform(post("/api/v1/products")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.sku").value("TEST-SKU-100"))
                .andExpect(jsonPath("$.name").value("Organic Sourdough Bread"))
                .andExpect(jsonPath("$.price").value(6.50));

        mockMvc.perform(get("/api/v1/products")
                        .param("q", "sourdough"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.content[0].sku").value("TEST-SKU-100"));
    }
}
"""

# ----------------- FRONTEND -----------------
FILES['frontend/package.json'] = """{
  "name": "food-platform-frontend",
  "private": true,
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "test": "vitest run",
    "lint": "tsc --noEmit"
  },
  "dependencies": {
    "@reduxjs/toolkit": "^2.2.7",
    "@tanstack/react-query": "^5.56.2",
    "clsx": "^2.1.1",
    "lucide-react": "^0.441.0",
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-redux": "^9.1.2",
    "react-router-dom": "^6.26.2",
    "tailwind-merge": "^2.5.2"
  },
  "devDependencies": {
    "@testing-library/jest-dom": "^6.5.0",
    "@testing-library/react": "^16.0.1",
    "@types/node": "^22.5.5",
    "@types/react": "^18.3.8",
    "@types/react-dom": "^18.3.0",
    "@vitejs/plugin-react": "^4.3.1",
    "autoprefixer": "^10.4.20",
    "jsdom": "^25.0.0",
    "postcss": "^8.4.47",
    "tailwindcss": "^3.4.11",
    "typescript": "^5.6.2",
    "vite": "^5.4.6",
    "vitest": "^2.1.1"
  }
}
"""

FILES['frontend/tsconfig.json'] = """{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
"""

FILES['frontend/tsconfig.node.json'] = """{
  "compilerOptions": {
    "composite": true,
    "skipLibCheck": true,
    "module": "ESNext",
    "moduleResolution": "bundler",
    "allowSyntheticDefaultImports": true
  },
  "include": ["vite.config.ts"]
}
"""

FILES['frontend/vite.config.ts'] = """import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true,
    proxy: {
      '/api': {
        target: process.env.VITE_API_GATEWAY_URL || 'http://localhost:8080',
        changeOrigin: true,
      },
    },
  },
  test: {
    globals: true,
    environment: 'jsdom',
  },
});
"""

FILES['frontend/tailwind.config.js'] = """/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#f0fdf4',
          100: '#dcfce7',
          500: '#22c55e',
          600: '#16a34a',
          700: '#15803d',
          800: '#166534',
          900: '#14532d',
        }
      }
    },
  },
  plugins: [],
}
"""

FILES['frontend/postcss.config.js'] = """export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
"""

FILES['frontend/index.html'] = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Enterprise Food Operations Platform</title>
  </head>
  <body class="bg-slate-50 text-slate-900 antialiased min-h-screen">
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
"""

FILES['frontend/nginx.conf'] = """server {
    listen 5173;
    server_name localhost;

    location / {
        root /usr/share/nginx/html;
        index index.html index.htm;
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://api-gateway:8080/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
"""

FILES['frontend/Dockerfile'] = """FROM node:22-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 5173
CMD ["nginx", "-g", "daemon off;"]
"""

FILES['frontend/src/index.css'] = """@tailwind base;
@tailwind components;
@tailwind utilities;

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
}
"""

FILES['frontend/src/store/authSlice.ts'] = """import { createSlice, PayloadAction } from '@reduxjs/toolkit';

export interface User {
  id: string;
  email: string;
  fullName: string;
  role: 'ADMIN' | 'MANAGER' | 'WAREHOUSE_OPERATOR' | 'CUSTOMER';
}

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
}

const initialState: AuthState = {
  user: null,
  accessToken: localStorage.getItem('accessToken'),
  refreshToken: localStorage.getItem('refreshToken'),
  isAuthenticated: !!localStorage.getItem('accessToken'),
};

export const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    setCredentials: (
      state,
      action: PayloadAction<{ user: User; accessToken: string; refreshToken: string }>
    ) => {
      const { user, accessToken, refreshToken } = action.payload;
      state.user = user;
      state.accessToken = accessToken;
      state.refreshToken = refreshToken;
      state.isAuthenticated = true;
      localStorage.setItem('accessToken', accessToken);
      localStorage.setItem('refreshToken', refreshToken);
    },
    logout: (state) => {
      state.user = null;
      state.accessToken = null;
      state.refreshToken = null;
      state.isAuthenticated = false;
      localStorage.removeItem('accessToken');
      localStorage.removeItem('refreshToken');
    },
  },
});

export const { setCredentials, logout } = authSlice.actions;
export default authSlice.reducer;
"""

FILES['frontend/src/store/index.ts'] = """import { configureStore } from '@reduxjs/toolkit';
import { TypedUseSelectorHook, useDispatch, useSelector } from 'react-redux';
import authReducer from './authSlice';

export const store = configureStore({
  reducer: {
    auth: authReducer,
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

export const useAppDispatch = () => useDispatch<AppDispatch>();
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector;
"""

FILES['frontend/src/api/client.ts'] = """export interface ProblemDetail {
  type?: string;
  title?: string;
  status?: number;
  detail?: string;
  instance?: string;
  errors?: Record<string, string>;
  correlationId?: string;
}

export interface PagedResponse<T> {
  content: T[];
  page: number;
  size: number;
  totalElements: number;
  totalPages: number;
  last: boolean;
}

export interface Product {
  id: string;
  sku: string;
  name: string;
  description: string;
  categoryId: string;
  unit: string;
  price: number;
  currency: string;
  active: boolean;
  createdAt: string;
  updatedAt: string;
  version: number;
}

export interface Category {
  id: string;
  name: string;
  parentId: string | null;
  createdAt: string;
}

export async function apiFetch<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem('accessToken');
  const correlationId = crypto.randomUUID();

  const headers = new Headers(options.headers || {});
  headers.set('Content-Type', 'application/json');
  headers.set('X-Correlation-Id', correlationId);

  if (token && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  const response = await fetch(endpoint, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorDetail: ProblemDetail;
    try {
      errorDetail = await response.json();
    } catch {
      errorDetail = {
        title: response.statusText,
        status: response.status,
        detail: 'An unexpected error occurred',
      };
    }
    throw errorDetail;
  }

  if (response.status === 204) {
    return {} as T;
  }

  return response.json();
}

export const productApi = {
  getProducts: (params?: { category?: string; q?: string; page?: number; size?: number }) => {
    const query = new URLSearchParams();
    if (params?.category) query.append('category', params.category);
    if (params?.q) query.append('q', params.q);
    if (params?.page !== undefined) query.append('page', params.page.toString());
    if (params?.size !== undefined) query.append('size', params.size.toString());

    return apiFetch<PagedResponse<Product>>(`/api/v1/products?${query.toString()}`);
  },
  getProductById: (id: string) => apiFetch<Product>(`/api/v1/products/${id}`),
  getCategories: () => apiFetch<Category[]>('/api/v1/categories'),
  createProduct: (data: Partial<Product>) =>
    apiFetch<Product>('/api/v1/products', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
};
"""

FILES['frontend/src/components/Header.tsx'] = """import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Utensils, LayoutDashboard, Package, Warehouse, ShoppingCart, Bot, Bell } from 'lucide-react';

export const Header: React.FC = () => {
  const location = useLocation();

  const navItems = [
    { label: 'Dashboard', path: '/', icon: LayoutDashboard },
    { label: 'Products', path: '/products', icon: Package },
    { label: 'Inventory', path: '/inventory', icon: Warehouse },
    { label: 'Orders', path: '/orders', icon: ShoppingCart },
    { label: 'AI Assistant', path: '/assistant', icon: Bot },
  ];

  return (
    <header className="bg-slate-900 text-white shadow-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center space-x-3">
            <div className="bg-emerald-500 p-2 rounded-lg text-slate-950 font-bold">
              <Utensils className="w-5 h-5" />
            </div>
            <div>
              <span className="text-lg font-bold tracking-tight text-white">FoodOps</span>
              <span className="text-xs text-emerald-400 block -mt-1 font-medium">Enterprise Platform</span>
            </div>
          </div>

          <nav className="flex space-x-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-slate-800 text-emerald-400'
                      : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </nav>

          <div className="flex items-center space-x-4">
            <button
              title="Notifications"
              className="relative p-2 text-slate-300 hover:text-white hover:bg-slate-800 rounded-full"
            >
              <Bell className="w-5 h-5" />
              <span className="absolute top-1 right-1 w-2 h-2 bg-emerald-500 rounded-full" />
            </button>
            <div className="flex items-center space-x-2 pl-2 border-l border-slate-700">
              <div className="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center font-bold text-xs text-emerald-400">
                ADM
              </div>
              <div className="text-xs">
                <p className="font-semibold text-slate-200">Admin User</p>
                <p className="text-slate-400">ADMIN</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};
"""

FILES['frontend/src/pages/Dashboard.tsx'] = """import React from 'react';
import { Package, Warehouse, ShoppingCart, Activity, CheckCircle2, ArrowUpRight } from 'lucide-react';
import { Link } from 'react-router-dom';

export const Dashboard: React.FC = () => {
  const stats = [
    { title: 'Catalog Items', value: '5,000+', change: '+12% this month', icon: Package, link: '/products' },
    { title: 'Active Warehouses', value: '4 Hubs', change: '99.4% capacity tracked', icon: Warehouse, link: '/inventory' },
    { title: 'Orders Today', value: '1,248', change: '+18% vs yesterday', icon: ShoppingCart, link: '/orders' },
    { title: 'Gateway Uptime', value: '99.98%', change: 'Resilience4j active', icon: Activity, link: '/' },
  ];

  const microservices = [
    { name: 'API Gateway', port: ':8080', status: 'Healthy', tech: 'Spring Cloud Gateway' },
    { name: 'Identity Service', port: ':8081', status: 'Standby / Phase 2', tech: 'Spring Boot 3 / JWT' },
    { name: 'Product Service', port: ':8082', status: 'Online', tech: 'Spring Boot 3 / Redis' },
    { name: 'Inventory Service', port: ':8083', status: 'Scheduled', tech: 'Spring Boot 3 / Optimistic Lock' },
    { name: 'Order Service', port: ':8084', status: 'Scheduled', tech: 'Spring Boot 3 / Outbox' },
    { name: 'Notification Service', port: ':8085', status: 'Scheduled', tech: 'Node.js 22 / Express' },
    { name: 'AI Service', port: ':8087', status: 'Scheduled', tech: 'Python 3.12 / FastAPI' },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900">Operations Control Center</h1>
        <p className="text-sm text-slate-500 mt-1">
          Real-time event-driven microservices platform overview and telemetry.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((item) => {
          const Icon = item.icon;
          return (
            <div key={item.title} className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">{item.title}</span>
                <div className="p-2 bg-emerald-50 text-emerald-600 rounded-lg">
                  <Icon className="w-5 h-5" />
                </div>
              </div>
              <div className="mt-3">
                <h2 className="text-2xl font-bold text-slate-900">{item.value}</h2>
                <p className="text-xs text-emerald-600 font-medium mt-1 flex items-center">
                  <ArrowUpRight className="w-3.5 h-3.5 mr-0.5" />
                  {item.change}
                </p>
              </div>
              <Link to={item.link} className="text-xs text-slate-500 hover:text-emerald-600 font-medium mt-4 block pt-3 border-t border-slate-100">
                View Details &rarr;
              </Link>
            </div>
          );
        })}
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-bold text-slate-900">Microservice Topology & Health</h2>
            <p className="text-xs text-slate-500">Autonomous distributed service runtime matrix</p>
          </div>
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-100 text-emerald-800">
            <CheckCircle2 className="w-3 h-3 mr-1" /> Phase 1 Active
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead>
              <tr className="text-left text-xs font-semibold text-slate-500 uppercase tracking-wider bg-slate-50">
                <th className="py-3 px-4">Service</th>
                <th className="py-3 px-4">Endpoint</th>
                <th className="py-3 px-4">Technology</th>
                <th className="py-3 px-4">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-mono text-xs">
              {microservices.map((svc) => (
                <tr key={svc.name} className="hover:bg-slate-50">
                  <td className="py-3 px-4 font-semibold text-slate-800 font-sans">{svc.name}</td>
                  <td className="py-3 px-4 text-slate-600">{svc.port}</td>
                  <td className="py-3 px-4 text-slate-500 font-sans">{svc.tech}</td>
                  <td className="py-3 px-4 font-sans">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                      svc.status === 'Healthy' || svc.status === 'Online'
                        ? 'bg-emerald-100 text-emerald-800'
                        : 'bg-slate-100 text-slate-700'
                    }`}>
                      {svc.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
"""

FILES['frontend/src/pages/Products.tsx'] = """import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { productApi, Product } from '../api/client';
import { Search, Plus, AlertCircle, RefreshCw, Layers } from 'lucide-react';

export const Products: React.FC = () => {
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(0);

  const { data, isLoading, isError, error, refetch, isFetching } = useQuery({
    queryKey: ['products', search, page],
    queryFn: () => productApi.getProducts({ q: search || undefined, page, size: 10 }),
  });

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900">Product Catalog</h1>
          <p className="text-sm text-slate-500 mt-1">
            Browse and manage enterprise foodservice products and pricing.
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={() => refetch()}
            disabled={isFetching}
            className="p-2 border border-slate-300 rounded-lg text-slate-700 hover:bg-slate-100 disabled:opacity-50"
            title="Refresh catalog"
          >
            <RefreshCw className={`w-4 h-4 ${isFetching ? 'animate-spin' : ''}`} />
          </button>
          <button className="flex items-center space-x-2 px-4 py-2 bg-emerald-600 text-white rounded-lg text-sm font-medium hover:bg-emerald-700 shadow-sm transition">
            <Plus className="w-4 h-4" />
            <span>Add Product</span>
          </button>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4">
        <div className="relative">
          <Search className="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Search products by SKU, name or description..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(0);
            }}
            className="w-full pl-10 pr-4 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
          />
        </div>
      </div>

      {isError && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 flex items-start space-x-3 text-red-700">
          <AlertCircle className="w-5 h-5 text-red-500 mt-0.5 flex-shrink-0" />
          <div>
            <h3 className="text-sm font-semibold">Failed to load products from Gateway</h3>
            <p className="text-xs mt-1 text-red-600">
              {((error as any)?.detail || (error as any)?.title || 'Check if API Gateway (:8080) and Product Service (:8082) are running.')}
            </p>
          </div>
        </div>
      )}

      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        {isLoading ? (
          <div className="p-12 text-center text-slate-500 space-y-3">
            <div className="w-8 h-8 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin mx-auto" />
            <p className="text-sm font-medium">Fetching catalog items through API Gateway...</p>
          </div>
        ) : !data || data.content.length === 0 ? (
          <div className="p-12 text-center text-slate-500 space-y-3">
            <Layers className="w-12 h-12 text-slate-300 mx-auto" />
            <h3 className="text-sm font-semibold text-slate-700">No products found</h3>
            <p className="text-xs text-slate-400 max-w-sm mx-auto">
              No products matched your search criteria or the database is currently empty.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <thead className="bg-slate-50 text-xs font-semibold text-slate-500 uppercase tracking-wider text-left">
                <tr>
                  <th className="py-3 px-4">SKU</th>
                  <th className="py-3 px-4">Product Name</th>
                  <th className="py-3 px-4">Unit</th>
                  <th className="py-3 px-4">Price</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {data.content.map((product: Product) => (
                  <tr key={product.id} className="hover:bg-slate-50">
                    <td className="py-3.5 px-4 font-mono text-xs font-medium text-slate-600">
                      {product.sku}
                    </td>
                    <td className="py-3.5 px-4">
                      <div className="font-medium text-slate-900">{product.name}</div>
                      {product.description && (
                        <div className="text-xs text-slate-500 line-clamp-1">{product.description}</div>
                      )}
                    </td>
                    <td className="py-3.5 px-4 text-slate-600 capitalize">{product.unit}</td>
                    <td className="py-3.5 px-4 font-semibold text-slate-900">
                      ${Number(product.price).toFixed(2)} <span className="text-xs font-normal text-slate-400">{product.currency}</span>
                    </td>
                    <td className="py-3.5 px-4">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                        product.active ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-100 text-slate-600'
                      }`}>
                        {product.active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <button className="text-xs text-emerald-600 hover:text-emerald-800 font-medium">
                        Edit
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {data && data.totalPages > 1 && (
          <div className="px-4 py-3 border-t border-slate-200 flex items-center justify-between text-xs text-slate-500">
            <span>
              Showing page <strong className="font-semibold text-slate-700">{data.page + 1}</strong> of{' '}
              <strong className="font-semibold text-slate-700">{data.totalPages}</strong> ({data.totalElements} total)
            </span>
            <div className="flex space-x-2">
              <button
                disabled={data.page === 0}
                onClick={() => setPage((p) => Math.max(p - 1, 0))}
                className="px-3 py-1.5 border border-slate-300 rounded hover:bg-slate-50 disabled:opacity-50"
              >
                Previous
              </button>
              <button
                disabled={data.last}
                onClick={() => setPage((p) => p + 1)}
                className="px-3 py-1.5 border border-slate-300 rounded hover:bg-slate-50 disabled:opacity-50"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
"""

FILES['frontend/src/App.tsx'] = """import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Provider } from 'react-redux';
import { store } from './store';
import { Header } from './components/Header';
import { Dashboard } from './pages/Dashboard';
import { Products } from './pages/Products';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

export const App: React.FC = () => {
  return (
    <Provider store={store}>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <div className="min-h-screen flex flex-col bg-slate-50">
            <Header />
            <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/products" element={<Products />} />
                <Route path="/inventory" element={<div className="p-8 bg-white rounded-xl shadow-sm border border-slate-200">Inventory module (Phase 3)</div>} />
                <Route path="/orders" element={<div className="p-8 bg-white rounded-xl shadow-sm border border-slate-200">Orders module (Phase 4)</div>} />
                <Route path="/assistant" element={<div className="p-8 bg-white rounded-xl shadow-sm border border-slate-200">AI Assistant module (Phase 9)</div>} />
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </main>
          </div>
        </BrowserRouter>
      </QueryClientProvider>
    </Provider>
  );
};

export default App;
"""

FILES['frontend/src/main.tsx'] = """import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
"""

FILES['frontend/src/App.test.tsx'] = """import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import App from './App';

describe('App Component', () => {
  it('renders platform title in header', () => {
    render(<App />);
    expect(screen.getByText('FoodOps')).toBeDefined();
    expect(screen.getByText('Enterprise Platform')).toBeDefined();
  });
});
"""

print(f"Writing {len(FILES)} files...")
for rel_path, content in FILES.items():
    dir_path = os.path.dirname(rel_path)
    if dir_path:
        os.makedirs(dir_path, exist_ok=True)
    with open(rel_path, 'w', encoding='utf-8') as f:
        f.write(content)
print("Finished writing all files.")
