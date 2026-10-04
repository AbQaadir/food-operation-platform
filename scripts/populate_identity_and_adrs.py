import os

FILES = {}

# ----------------- ADRs -----------------
FILES['docs/adr/001-microservices-architecture.md'] = """# ADR 001: Adoption of Microservices Architecture

## Status
Accepted

## Context
The Enterprise Food Operations Platform manages multiple distinct operational capabilities:
- User identity, credentials, and access control
- Product catalogs, pricing, and category hierarchies
- Warehouse inventory tracking and stock reservation concurrency
- Order placement, state machines, and transactional outbox eventing
- Event-driven notifications and real-time alerts
- AI-driven operations assistance via LLM tool-calling

A monolithic architecture would tightly couple deployment cycles, create shared database contention across high-throughput domains, and prevent polyglot service optimization.

## Decision
We adopt an event-driven **microservices architecture** with a **database-per-service** boundary:
1. **Core Business Domains (Java 21 / Spring Boot 3):** `identity-service`, `product-service`, `inventory-service`, and `order-service`.
2. **Notification & Aggregation (Node.js 22 / Express / TypeScript):** `notification-service` and `analytics-service`.
3. **AI Operations Assistant (Python 3.12 / FastAPI):** `ai-service`.
4. **Edge Gateway (Spring Cloud Gateway):** Directs incoming traffic, enforces rate limiting, authenticates JWTs, and injects correlation IDs.

## Consequences
### Positive
- Independent scalability of write-heavy and read-heavy services.
- Fault isolation: failure in notification/AI does not disrupt order processing.
- Strict schema boundaries prevent accidental cross-boundary database coupling.
### Negative & Trade-offs
- Requires distributed transaction handling (Sagas) rather than two-phase commits.
- Added infrastructure complexity managed via Docker Compose and Terraform.
"""

FILES['docs/adr/002-apache-kafka-for-event-backbone.md'] = """# ADR 002: Apache Kafka as Asynchronous Event Backbone

## Status
Accepted

## Context
The platform requires asynchronous coordination across services for order fulfillment choreography, customer notifications, analytical KPI projection, and auditing. Synchronous REST calls introduce high latency, tight coupling, and cascading failures.

## Decision
We adopt **Apache Kafka** (running in KRaft mode) as the platform's asynchronous messaging backbone.
1. **Partitioning Key:** Aggregate root IDs (e.g. `orderId`) guarantee strict causal ordering.
2. **Transactional Outbox:** Producers write events atomically into a local `outbox_events` table before dispatching to Kafka.
3. **Consumer Idempotency:** Consumers persist processed `eventId` keys.
4. **Dead Letter Queues (DLQ):** Failed messages retry with backoff then route to `<topic>.dlq`.
5. **Schema Contracts:** All events conform strictly to JSON Schema definitions in `contracts/events/`.

## Consequences
### Positive
- High-throughput append-only log durability.
- Decoupled event publication allowing new consumers without producer modification.
- Zero ZooKeeper overhead via modern KRaft metadata consensus.
### Negative & Trade-offs
- Eventual consistency requires UI to support pending states.
- Consumer group offsets and lag must be continuously monitored via Prometheus/Grafana.
"""

# ----------------- IDENTITY-SERVICE -----------------
FILES['services/identity-service/pom.xml'] = """<?xml version="1.0" encoding="UTF-8"?>
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
    <artifactId>identity-service</artifactId>
    <version>1.0.0-SNAPSHOT</version>
    <name>identity-service</name>
    <description>Identity and Access Management Service for Food Operations Platform</description>

    <properties>
        <java.version>21</java.version>
        <springdoc.version>2.6.0</springdoc.version>
        <jjwt.version>0.12.6</jjwt.version>
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
            <artifactId>spring-boot-starter-security</artifactId>
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
            <groupId>org.springdoc</groupId>
            <artifactId>springdoc-openapi-starter-webmvc-ui</artifactId>
            <version>${springdoc.version}</version>
        </dependency>

        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-test</artifactId>
            <scope>test</scope>
        </dependency>
        <dependency>
            <groupId>org.springframework.security</groupId>
            <artifactId>spring-security-test</artifactId>
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

FILES['services/identity-service/Dockerfile'] = """FROM maven:3.9.9-eclipse-temurin-21-alpine AS build
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
EXPOSE 8081
ENTRYPOINT ["java", "-jar", "app.jar"]
"""

FILES['services/identity-service/src/main/resources/application.yml'] = """server:
  port: ${PORT_IDENTITY:8081}

spring:
  application:
    name: identity-service
  datasource:
    url: jdbc:postgresql://${POSTGRES_HOST:localhost}:${POSTGRES_PORT:5432}/identity_db
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
  access-expiration-seconds: ${JWT_ACCESS_EXPIRATION_SECONDS:900}
  refresh-expiration-seconds: ${JWT_REFRESH_EXPIRATION_SECONDS:604800}

springdoc:
  api-docs:
    path: /v3/api-docs
  swagger-ui:
    path: /swagger-ui.html
"""

FILES['services/identity-service/src/test/resources/application-test.yml'] = """spring:
  datasource:
    url: jdbc:h2:mem:identity_test_db;DB_CLOSE_DELAY=-1;MODE=PostgreSQL
    driver-class-name: org.h2.Driver
    username: sa
    password: ""
  jpa:
    hibernate:
      ddl-auto: create-drop
    database-platform: org.hibernate.dialect.H2Dialect
  flyway:
    enabled: false

jwt:
  secret: c2VjdXJlX2Zvb2Rfb3BlcmF0aW9uc19wbGF0Zm9ybV9qd3Rfc2VjcmV0X2tleV9mb3JfZGV2X2Vudmlyb25tZW50XzEyMzQ1Ng==
  access-expiration-seconds: 900
  refresh-expiration-seconds: 604800
"""

FILES['services/identity-service/src/main/resources/db/migration/V1__create_identity_tables.sql'] = """CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    version BIGINT NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS refresh_tokens (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL UNIQUE,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    revoked BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user_id ON refresh_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_token_hash ON refresh_tokens(token_hash);
"""

FILES['services/identity-service/src/main/java/com/foodplatform/identity/domain/Role.java'] = """package com.foodplatform.identity.domain;

public enum Role {
    ADMIN,
    MANAGER,
    WAREHOUSE_OPERATOR,
    CUSTOMER
}
"""

FILES['services/identity-service/src/main/java/com/foodplatform/identity/domain/User.java'] = """package com.foodplatform.identity.domain;

import jakarta.persistence.*;
import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "users")
public class User {

    @Id
    private UUID id;

    @Column(nullable = false, unique = true)
    private String email;

    @Column(name = "password_hash", nullable = false)
    private String passwordHash;

    @Column(name = "full_name", nullable = false)
    private String fullName;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 50)
    private Role role;

    @Column(nullable = false)
    private boolean enabled;

    @Column(name = "created_at", nullable = false, updatable = false)
    private Instant createdAt;

    @Column(name = "updated_at", nullable = false)
    private Instant updatedAt;

    @Version
    @Column(nullable = false)
    private Long version;

    public User() {
    }

    public User(UUID id, String email, String passwordHash, String fullName, Role role, boolean enabled) {
        this.id = id != null ? id : UUID.randomUUID();
        this.email = email;
        this.passwordHash = passwordHash;
        this.fullName = fullName;
        this.role = role;
        this.enabled = enabled;
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

    public String getEmail() { return email; }
    public void setEmail(String email) { this.email = email; }

    public String getPasswordHash() { return passwordHash; }
    public void setPasswordHash(String passwordHash) { this.passwordHash = passwordHash; }

    public String getFullName() { return fullName; }
    public void setFullName(String fullName) { this.fullName = fullName; }

    public Role getRole() { return role; }
    public void setRole(Role role) { this.role = role; }

    public boolean isEnabled() { return enabled; }
    public void setEnabled(boolean enabled) { this.enabled = enabled; }

    public Instant getCreatedAt() { return createdAt; }
    public void setCreatedAt(Instant createdAt) { this.createdAt = createdAt; }

    public Instant getUpdatedAt() { return updatedAt; }
    public void setUpdatedAt(Instant updatedAt) { this.updatedAt = updatedAt; }

    public Long getVersion() { return version; }
    public void setVersion(Long version) { this.version = version; }
}
"""

FILES['services/identity-service/src/main/java/com/foodplatform/identity/domain/RefreshToken.java'] = """package com.foodplatform.identity.domain;

import jakarta.persistence.*;
import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "refresh_tokens")
public class RefreshToken {

    @Id
    private UUID id;

    @Column(name = "user_id", nullable = false)
    private UUID userId;

    @Column(name = "token_hash", nullable = false, unique = true)
    private String tokenHash;

    @Column(name = "expires_at", nullable = false)
    private Instant expiresAt;

    @Column(nullable = false)
    private boolean revoked;

    @Column(name = "created_at", nullable = false, updatable = false)
    private Instant createdAt;

    public RefreshToken() {
    }

    public RefreshToken(UUID id, UUID userId, String tokenHash, Instant expiresAt) {
        this.id = id != null ? id : UUID.randomUUID();
        this.userId = userId;
        this.tokenHash = tokenHash;
        this.expiresAt = expiresAt;
        this.revoked = false;
        this.createdAt = Instant.now();
    }

    @PrePersist
    protected void onCreate() {
        if (id == null) id = UUID.randomUUID();
        if (createdAt == null) createdAt = Instant.now();
    }

    public UUID getId() { return id; }
    public void setId(UUID id) { this.id = id; }

    public UUID getUserId() { return userId; }
    public void setUserId(UUID userId) { this.userId = userId; }

    public String getTokenHash() { return tokenHash; }
    public void setTokenHash(String tokenHash) { this.tokenHash = tokenHash; }

    public Instant getExpiresAt() { return expiresAt; }
    public void setExpiresAt(Instant expiresAt) { this.expiresAt = expiresAt; }

    public boolean isRevoked() { return revoked; }
    public void setRevoked(boolean revoked) { this.revoked = revoked; }

    public Instant getCreatedAt() { return createdAt; }
    public void setCreatedAt(Instant createdAt) { this.createdAt = createdAt; }
}
"""

FILES['services/identity-service/src/main/java/com/foodplatform/identity/dto/LoginRequest.java'] = """package com.foodplatform.identity.dto;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;

public record LoginRequest(
        @NotBlank(message = "Email is required")
        @Email(message = "Invalid email format")
        String email,

        @NotBlank(message = "Password is required")
        String password
) {}
"""

FILES['services/identity-service/src/main/java/com/foodplatform/identity/dto/RegisterRequest.java'] = """package com.foodplatform.identity.dto;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record RegisterRequest(
        @NotBlank(message = "Email is required")
        @Email(message = "Invalid email format")
        String email,

        @NotBlank(message = "Password is required")
        @Size(min = 6, message = "Password must be at least 6 characters")
        String password,

        @NotBlank(message = "Full name is required")
        String fullName
) {}
"""

FILES['services/identity-service/src/main/java/com/foodplatform/identity/dto/AuthResponse.java'] = """package com.foodplatform.identity.dto;

public record AuthResponse(
        String accessToken,
        String refreshToken,
        long expiresIn,
        UserDto user
) {}
"""

FILES['services/identity-service/src/main/java/com/foodplatform/identity/dto/RefreshTokenRequest.java'] = """package com.foodplatform.identity.dto;

import jakarta.validation.constraints.NotBlank;

public record RefreshTokenRequest(
        @NotBlank(message = "Refresh token is required")
        String refreshToken
) {}
"""

FILES['services/identity-service/src/main/java/com/foodplatform/identity/dto/UserDto.java'] = """package com.foodplatform.identity.dto;

import com.foodplatform.identity.domain.Role;

import java.time.Instant;
import java.util.UUID;

public record UserDto(
        UUID id,
        String email,
        String fullName,
        Role role,
        boolean enabled,
        Instant createdAt
) {}
"""

FILES['services/identity-service/src/main/java/com/foodplatform/identity/dto/CreateUserRequest.java'] = """package com.foodplatform.identity.dto;

import com.foodplatform.identity.domain.Role;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

public record CreateUserRequest(
        @NotBlank(message = "Email is required")
        @Email(message = "Invalid email format")
        String email,

        @NotBlank(message = "Password is required")
        @Size(min = 6, message = "Password must be at least 6 characters")
        String password,

        @NotBlank(message = "Full name is required")
        String fullName,

        @NotNull(message = "Role is required")
        Role role
) {}
"""

FILES['services/identity-service/src/main/java/com/foodplatform/identity/dto/UpdateUserRequest.java'] = """package com.foodplatform.identity.dto;

import com.foodplatform.identity.domain.Role;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

public record UpdateUserRequest(
        @NotBlank(message = "Full name is required")
        String fullName,

        @NotNull(message = "Role is required")
        Role role,

        Boolean enabled
) {}
"""

FILES['services/identity-service/src/main/java/com/foodplatform/identity/repository/UserRepository.java'] = """package com.foodplatform.identity.repository;

import com.foodplatform.identity.domain.User;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;
import java.util.UUID;

@Repository
public interface UserRepository extends JpaRepository<User, UUID> {
    Optional<User> findByEmailIgnoreCase(String email);
    boolean existsByEmailIgnoreCase(String email);
}
"""

FILES['services/identity-service/src/main/java/com/foodplatform/identity/repository/RefreshTokenRepository.java'] = """package com.foodplatform.identity.repository;

import com.foodplatform.identity.domain.RefreshToken;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;
import java.util.UUID;

@Repository
public interface RefreshTokenRepository extends JpaRepository<RefreshToken, UUID> {
    Optional<RefreshToken> findByTokenHash(String tokenHash);
    void deleteByUserId(UUID userId);
}
"""

FILES['services/identity-service/src/main/java/com/foodplatform/identity/security/JwtTokenProvider.java'] = """package com.foodplatform.identity.security;

import com.foodplatform.identity.domain.User;
import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import javax.crypto.SecretKey;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.Date;
import java.util.UUID;

@Component
public class JwtTokenProvider {

    private final SecretKey signingKey;
    private final long accessExpirationSeconds;
    private final long refreshExpirationSeconds;

    public JwtTokenProvider(
            @Value("${jwt.secret}") String secret,
            @Value("${jwt.access-expiration-seconds:900}") long accessExpirationSeconds,
            @Value("${jwt.refresh-expiration-seconds:604800}") long refreshExpirationSeconds
    ) {
        byte[] keyBytes;
        try {
            keyBytes = java.util.Base64.getDecoder().decode(secret);
        } catch (IllegalArgumentException e) {
            keyBytes = secret.getBytes(StandardCharsets.UTF_8);
        }
        this.signingKey = Keys.hmacShaKeyFor(keyBytes);
        this.accessExpirationSeconds = accessExpirationSeconds;
        this.refreshExpirationSeconds = refreshExpirationSeconds;
    }

    public String generateAccessToken(User user) {
        Instant now = Instant.now();
        Instant expiry = now.plusSeconds(accessExpirationSeconds);

        return Jwts.builder()
                .subject(user.getId().toString())
                .claim("email", user.getEmail())
                .claim("role", user.getRole().name())
                .claim("fullName", user.getFullName())
                .issuedAt(Date.from(now))
                .expiration(Date.from(expiry))
                .signWith(signingKey)
                .compact();
    }

    public String generateRefreshTokenString() {
        return UUID.randomUUID().toString().replace("-", "") + UUID.randomUUID().toString().replace("-", "");
    }

    public long getAccessExpirationSeconds() {
        return accessExpirationSeconds;
    }

    public long getRefreshExpirationSeconds() {
        return refreshExpirationSeconds;
    }

    public Claims parseClaims(String token) {
        return Jwts.parser()
                .verifyWith(signingKey)
                .build()
                .parseSignedClaims(token)
                .getPayload();
    }

    public boolean validateToken(String token) {
        try {
            parseClaims(token);
            return true;
        } catch (Exception e) {
            return false;
        }
    }
}
"""

FILES['services/identity-service/src/main/java/com/foodplatform/identity/security/CustomUserDetailsService.java'] = """package com.foodplatform.identity.security;

import com.foodplatform.identity.domain.User;
import com.foodplatform.identity.repository.UserRepository;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.stereotype.Service;

import java.util.Collections;

@Service
public class CustomUserDetailsService implements UserDetailsService {

    private final UserRepository userRepository;

    public CustomUserDetailsService(UserRepository userRepository) {
        this.userRepository = userRepository;
    }

    @Override
    public UserDetails loadUserByUsername(String email) throws UsernameNotFoundException {
        User user = userRepository.findByEmailIgnoreCase(email)
                .orElseThrow(() -> new UsernameNotFoundException("User not found with email: " + email));

        return new org.springframework.security.core.userdetails.User(
                user.getEmail(),
                user.getPasswordHash(),
                user.isEnabled(),
                true,
                true,
                true,
                Collections.singletonList(new SimpleGrantedAuthority("ROLE_" + user.getRole().name()))
        );
    }
}
"""

FILES['services/identity-service/src/main/java/com/foodplatform/identity/security/SecurityConfig.java'] = """package com.foodplatform.identity.security;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.config.annotation.authentication.configuration.AuthenticationConfiguration;
import org.springframework.security.config.annotation.method.configuration.EnableMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configurers.AbstractHttpConfigurer;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.SecurityFilterChain;

@Configuration
@EnableWebSecurity
@EnableMethodSecurity
public class SecurityConfig {

    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    @Bean
    public AuthenticationManager authenticationManager(AuthenticationConfiguration config) throws Exception {
        return config.getAuthenticationManager();
    }

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
                .csrf(AbstractHttpConfigurer::disable)
                .sessionManagement(session -> session.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
                .authorizeHttpRequests(auth -> auth
                        .requestMatchers(
                                "/api/v1/auth/**",
                                "/actuator/**",
                                "/v3/api-docs/**",
                                "/swagger-ui/**",
                                "/swagger-ui.html"
                        ).permitAll()
                        .anyRequest().authenticated()
                );

        return http.build();
    }
}
"""

FILES['services/identity-service/src/main/java/com/foodplatform/identity/exception/ResourceNotFoundException.java'] = """package com.foodplatform.identity.exception;

public class ResourceNotFoundException extends RuntimeException {
    public ResourceNotFoundException(String message) {
        super(message);
    }
}
"""

FILES['services/identity-service/src/main/java/com/foodplatform/identity/exception/UserAlreadyExistsException.java'] = """package com.foodplatform.identity.exception;

public class UserAlreadyExistsException extends RuntimeException {
    public UserAlreadyExistsException(String message) {
        super(message);
    }
}
"""

FILES['services/identity-service/src/main/java/com/foodplatform/identity/exception/InvalidCredentialsException.java'] = """package com.foodplatform.identity.exception;

public class InvalidCredentialsException extends RuntimeException {
    public InvalidCredentialsException(String message) {
        super(message);
    }
}
"""

FILES['services/identity-service/src/main/java/com/foodplatform/identity/exception/GlobalExceptionHandler.java'] = """package com.foodplatform.identity.exception;

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

    @ExceptionHandler(UserAlreadyExistsException.class)
    public ProblemDetail handleUserAlreadyExists(UserAlreadyExistsException ex, HttpServletRequest request) {
        ProblemDetail problem = ProblemDetail.forStatusAndDetail(HttpStatus.CONFLICT, ex.getMessage());
        problem.setTitle("User Conflict");
        problem.setType(URI.create("https://foodplatform.com/errors/conflict"));
        problem.setProperty("timestamp", Instant.now());
        problem.setProperty("correlationId", getCorrelationId(request));
        return problem;
    }

    @ExceptionHandler(InvalidCredentialsException.class)
    public ProblemDetail handleInvalidCredentials(InvalidCredentialsException ex, HttpServletRequest request) {
        ProblemDetail problem = ProblemDetail.forStatusAndDetail(HttpStatus.UNAUTHORIZED, ex.getMessage());
        problem.setTitle("Authentication Failed");
        problem.setType(URI.create("https://foodplatform.com/errors/unauthorized"));
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

FILES['services/identity-service/src/main/java/com/foodplatform/identity/service/AuthService.java'] = """package com.foodplatform.identity.service;

import com.foodplatform.identity.domain.RefreshToken;
import com.foodplatform.identity.domain.Role;
import com.foodplatform.identity.domain.User;
import com.foodplatform.identity.dto.AuthResponse;
import com.foodplatform.identity.dto.LoginRequest;
import com.foodplatform.identity.dto.RegisterRequest;
import com.foodplatform.identity.dto.UserDto;
import com.foodplatform.identity.exception.InvalidCredentialsException;
import com.foodplatform.identity.exception.UserAlreadyExistsException;
import com.foodplatform.identity.repository.RefreshTokenRepository;
import com.foodplatform.identity.repository.UserRepository;
import com.foodplatform.identity.security.JwtTokenProvider;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Instant;
import java.util.UUID;

@Service
public class AuthService {

    private final UserRepository userRepository;
    private final RefreshTokenRepository refreshTokenRepository;
    private final PasswordEncoder passwordEncoder;
    private final JwtTokenProvider jwtTokenProvider;

    public AuthService(
            UserRepository userRepository,
            RefreshTokenRepository refreshTokenRepository,
            PasswordEncoder passwordEncoder,
            JwtTokenProvider jwtTokenProvider
    ) {
        this.userRepository = userRepository;
        this.refreshTokenRepository = refreshTokenRepository;
        this.passwordEncoder = passwordEncoder;
        this.jwtTokenProvider = jwtTokenProvider;
    }

    @Transactional
    public AuthResponse register(RegisterRequest request) {
        if (userRepository.existsByEmailIgnoreCase(request.email())) {
            throw new UserAlreadyExistsException("Email already registered: " + request.email());
        }

        User user = new User(
                UUID.randomUUID(),
                request.email().toLowerCase().trim(),
                passwordEncoder.encode(request.password()),
                request.fullName().trim(),
                Role.CUSTOMER,
                true
        );

        User saved = userRepository.save(user);
        return createAuthResponse(saved);
    }

    @Transactional
    public AuthResponse login(LoginRequest request) {
        User user = userRepository.findByEmailIgnoreCase(request.email().trim())
                .orElseThrow(() -> new InvalidCredentialsException("Invalid email or password"));

        if (!user.isEnabled()) {
            throw new InvalidCredentialsException("Account is disabled");
        }

        if (!passwordEncoder.matches(request.password(), user.getPasswordHash())) {
            throw new InvalidCredentialsException("Invalid email or password");
        }

        return createAuthResponse(user);
    }

    @Transactional
    public AuthResponse refresh(String refreshTokenString) {
        RefreshToken token = refreshTokenRepository.findByTokenHash(refreshTokenString)
                .orElseThrow(() -> new InvalidCredentialsException("Invalid refresh token"));

        if (token.isRevoked() || token.getExpiresAt().isBefore(Instant.now())) {
            throw new InvalidCredentialsException("Refresh token is expired or revoked");
        }

        User user = userRepository.findById(token.getUserId())
                .orElseThrow(() -> new InvalidCredentialsException("User not found"));

        token.setRevoked(true);
        refreshTokenRepository.save(token);

        return createAuthResponse(user);
    }

    private AuthResponse createAuthResponse(User user) {
        String accessToken = jwtTokenProvider.generateAccessToken(user);
        String refreshTokenStr = jwtTokenProvider.generateRefreshTokenString();

        RefreshToken refreshToken = new RefreshToken(
                UUID.randomUUID(),
                user.getId(),
                refreshTokenStr,
                Instant.now().plusSeconds(jwtTokenProvider.getRefreshExpirationSeconds())
        );
        refreshTokenRepository.save(refreshToken);

        UserDto userDto = new UserDto(
                user.getId(),
                user.getEmail(),
                user.getFullName(),
                user.getRole(),
                user.isEnabled(),
                user.getCreatedAt()
        );

        return new AuthResponse(
                accessToken,
                refreshTokenStr,
                jwtTokenProvider.getAccessExpirationSeconds(),
                userDto
        );
    }
}
"""

FILES['services/identity-service/src/main/java/com/foodplatform/identity/service/UserService.java'] = """package com.foodplatform.identity.service;

import com.foodplatform.identity.domain.User;
import com.foodplatform.identity.dto.CreateUserRequest;
import com.foodplatform.identity.dto.UpdateUserRequest;
import com.foodplatform.identity.dto.UserDto;
import com.foodplatform.identity.exception.ResourceNotFoundException;
import com.foodplatform.identity.exception.UserAlreadyExistsException;
import com.foodplatform.identity.repository.UserRepository;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.UUID;

@Service
public class UserService {

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;

    public UserService(UserRepository userRepository, PasswordEncoder passwordEncoder) {
        this.userRepository = userRepository;
        this.passwordEncoder = passwordEncoder;
    }

    @Transactional(readOnly = true)
    public List<UserDto> getAllUsers() {
        return userRepository.findAll().stream().map(this::toDto).toList();
    }

    @Transactional(readOnly = true)
    public UserDto getUserById(UUID id) {
        User user = userRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("User not found with id: " + id));
        return toDto(user);
    }

    @Transactional(readOnly = true)
    public UserDto getUserByEmail(String email) {
        User user = userRepository.findByEmailIgnoreCase(email)
                .orElseThrow(() -> new ResourceNotFoundException("User not found with email: " + email));
        return toDto(user);
    }

    @Transactional
    public UserDto createUser(CreateUserRequest request) {
        if (userRepository.existsByEmailIgnoreCase(request.email())) {
            throw new UserAlreadyExistsException("Email already in use: " + request.email());
        }

        User user = new User(
                UUID.randomUUID(),
                request.email().toLowerCase().trim(),
                passwordEncoder.encode(request.password()),
                request.fullName().trim(),
                request.role(),
                true
        );

        return toDto(userRepository.save(user));
    }

    @Transactional
    public UserDto updateUser(UUID id, UpdateUserRequest request) {
        User user = userRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("User not found with id: " + id));

        user.setFullName(request.fullName().trim());
        user.setRole(request.role());
        if (request.enabled() != null) {
            user.setEnabled(request.enabled());
        }

        return toDto(userRepository.save(user));
    }

    private UserDto toDto(User user) {
        return new UserDto(
                user.getId(),
                user.getEmail(),
                user.getFullName(),
                user.getRole(),
                user.isEnabled(),
                user.getCreatedAt()
        );
    }
}
"""

FILES['services/identity-service/src/main/java/com/foodplatform/identity/controller/AuthController.java'] = """package com.foodplatform.identity.controller;

import com.foodplatform.identity.dto.AuthResponse;
import com.foodplatform.identity.dto.LoginRequest;
import com.foodplatform.identity.dto.RefreshTokenRequest;
import com.foodplatform.identity.dto.RegisterRequest;
import com.foodplatform.identity.service.AuthService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/auth")
@Tag(name = "Authentication", description = "Authentication & JWT Token operations")
public class AuthController {

    private final AuthService authService;

    public AuthController(AuthService authService) {
        this.authService = authService;
    }

    @PostMapping("/register")
    @Operation(summary = "Register customer account")
    public ResponseEntity<AuthResponse> register(@Valid @RequestBody RegisterRequest request) {
        AuthResponse response = authService.register(request);
        return ResponseEntity.status(HttpStatus.CREATED).body(response);
    }

    @PostMapping("/login")
    @Operation(summary = "Authenticate user and issue JWT tokens")
    public ResponseEntity<AuthResponse> login(@Valid @RequestBody LoginRequest request) {
        AuthResponse response = authService.login(request);
        return ResponseEntity.ok(response);
    }

    @PostMapping("/refresh")
    @Operation(summary = "Refresh access token using valid refresh token")
    public ResponseEntity<AuthResponse> refresh(@Valid @RequestBody RefreshTokenRequest request) {
        AuthResponse response = authService.refresh(request.refreshToken());
        return ResponseEntity.ok(response);
    }
}
"""

FILES['services/identity-service/src/main/java/com/foodplatform/identity/controller/UserController.java'] = """package com.foodplatform.identity.controller;

import com.foodplatform.identity.dto.CreateUserRequest;
import com.foodplatform.identity.dto.UpdateUserRequest;
import com.foodplatform.identity.dto.UserDto;
import com.foodplatform.identity.service.UserService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/users")
@Tag(name = "Users", description = "User Profile and Management")
public class UserController {

    private final UserService userService;

    public UserController(UserService userService) {
        this.userService = userService;
    }

    @GetMapping("/me")
    @Operation(summary = "Get current authenticated user profile")
    public ResponseEntity<UserDto> getMe(
            @RequestHeader(value = "X-User-Id", required = false) String headerUserId,
            Authentication authentication
    ) {
        if (headerUserId != null && !headerUserId.isBlank()) {
            return ResponseEntity.ok(userService.getUserById(UUID.fromString(headerUserId)));
        }
        if (authentication != null) {
            return ResponseEntity.ok(userService.getUserByEmail(authentication.getName()));
        }
        return ResponseEntity.status(HttpStatus.UNAUTHORIZED).build();
    }

    @GetMapping
    @PreAuthorize("hasRole('ADMIN')")
    @Operation(summary = "Get all users (ADMIN only)")
    public ResponseEntity<List<UserDto>> getAllUsers() {
        return ResponseEntity.ok(userService.getAllUsers());
    }

    @PostMapping
    @PreAuthorize("hasRole('ADMIN')")
    @Operation(summary = "Create user with specific role (ADMIN only)")
    public ResponseEntity<UserDto> createUser(@Valid @RequestBody CreateUserRequest request) {
        UserDto created = userService.createUser(request);
        return ResponseEntity.status(HttpStatus.CREATED).body(created);
    }

    @PutMapping("/{id}")
    @PreAuthorize("hasRole('ADMIN')")
    @Operation(summary = "Update user details (ADMIN only)")
    public ResponseEntity<UserDto> updateUser(
            @PathVariable UUID id,
            @Valid @RequestBody UpdateUserRequest request
    ) {
        UserDto updated = userService.updateUser(id, request);
        return ResponseEntity.ok(updated);
    }
}
"""

FILES['services/identity-service/src/main/java/com/foodplatform/identity/config/DataInitializer.java'] = """package com.foodplatform.identity.config;

import com.foodplatform.identity.domain.Role;
import com.foodplatform.identity.domain.User;
import com.foodplatform.identity.repository.UserRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.CommandLineRunner;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.crypto.password.PasswordEncoder;

import java.util.UUID;

@Configuration
public class DataInitializer implements CommandLineRunner {

    private static final Logger log = LoggerFactory.getLogger(DataInitializer.class);

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;

    public DataInitializer(UserRepository userRepository, PasswordEncoder passwordEncoder) {
        this.userRepository = userRepository;
        this.passwordEncoder = passwordEncoder;
    }

    @Override
    public void run(String... args) {
        seedUser("admin@foodplatform.com", "Admin123!", "Global Administrator", Role.ADMIN);
        seedUser("manager@foodplatform.com", "Manager123!", "Operations Manager", Role.MANAGER);
        seedUser("operator@foodplatform.com", "Operator123!", "Warehouse Operator", Role.WAREHOUSE_OPERATOR);
        seedUser("customer@foodplatform.com", "Customer123!", "Customer Account", Role.CUSTOMER);
    }

    private void seedUser(String email, String rawPassword, String fullName, Role role) {
        if (!userRepository.existsByEmailIgnoreCase(email)) {
            User user = new User(
                    UUID.randomUUID(),
                    email.toLowerCase(),
                    passwordEncoder.encode(rawPassword),
                    fullName,
                    role,
                    true
            );
            userRepository.save(user);
            log.info("Seeded default user: {} with role: {}", email, role);
        }
    }
}
"""

FILES['services/identity-service/src/main/java/com/foodplatform/identity/IdentityServiceApplication.java'] = """package com.foodplatform.identity;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class IdentityServiceApplication {
    public static void main(String[] args) {
        SpringApplication.run(IdentityServiceApplication.class, args);
    }
}
"""

FILES['services/identity-service/src/test/java/com/foodplatform/identity/IdentityServiceApplicationTests.java'] = """package com.foodplatform.identity;

import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;

@SpringBootTest
@ActiveProfiles("test")
class IdentityServiceApplicationTests {

    @Test
    void contextLoads() {
    }
}
"""

FILES['services/identity-service/src/test/java/com/foodplatform/identity/AuthControllerTest.java'] = """package com.foodplatform.identity;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.foodplatform.identity.dto.LoginRequest;
import com.foodplatform.identity.dto.RegisterRequest;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
class AuthControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @Test
    void shouldRegisterAndLoginSuccessfully() throws Exception {
        RegisterRequest registerReq = new RegisterRequest(
                "jane.doe@example.com",
                "Secret123!",
                "Jane Doe"
        );

        mockMvc.perform(post("/api/v1/auth/register")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(registerReq)))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.accessToken").exists())
                .andExpect(jsonPath("$.refreshToken").exists())
                .andExpect(jsonPath("$.user.email").value("jane.doe@example.com"));

        LoginRequest loginReq = new LoginRequest("jane.doe@example.com", "Secret123!");
        mockMvc.perform(post("/api/v1/auth/login")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(loginReq)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.accessToken").exists())
                .andExpect(jsonPath("$.user.role").value("CUSTOMER"));
    }
}
"""

print(f"Writing {len(FILES)} files...")
for rel_path, content in FILES.items():
    dir_path = os.path.dirname(rel_path)
    if dir_path:
        os.makedirs(dir_path, exist_ok=True)
    with open(rel_path, 'w', encoding='utf-8') as f:
        f.write(content)
print("Finished writing identity files.")
