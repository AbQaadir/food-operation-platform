#!/usr/bin/env python3
import os

BASE = "/Users/qaadir/Desktop/dev/foodOperationPlatform/services/order-service/src/main/java/com/foodplatform/order"

FILES = {
    # Application
    f"{BASE}/OrderServiceApplication.java": """package com.foodplatform.order;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.scheduling.annotation.EnableScheduling;

@SpringBootApplication
@EnableScheduling
@EnableAsync
public class OrderServiceApplication {
    public static void main(String[] args) {
        SpringApplication.run(OrderServiceApplication.class, args);
    }
}
""",

    # Domain: OrderStatus
    f"{BASE}/domain/OrderStatus.java": """package com.foodplatform.order.domain;

public enum OrderStatus {
    PENDING,
    CONFIRMED,
    PAID,
    PROCESSING,
    SHIPPED,
    DELIVERED,
    CANCELLED
}
""",

    # Domain: Order
    f"{BASE}/domain/Order.java": """package com.foodplatform.order.domain;

import jakarta.persistence.*;
import java.math.BigDecimal;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

@Entity
@Table(name = "orders")
public class Order {

    @Id
    private UUID id;

    @Column(name = "customer_id", nullable = false)
    private UUID customerId;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 50)
    private OrderStatus status;

    @Column(name = "total_amount", nullable = false, precision = 12, scale = 2)
    private BigDecimal totalAmount;

    @Column(nullable = false, length = 10)
    private String currency;

    @Column(name = "cancel_reason")
    private String cancelReason;

    @OneToMany(mappedBy = "order", cascade = CascadeType.ALL, orphanRemoval = true, fetch = FetchType.EAGER)
    private List<OrderItem> items = new ArrayList<>();

    @Column(name = "created_at", nullable = false, updatable = false)
    private Instant createdAt;

    @Column(name = "updated_at", nullable = false)
    private Instant updatedAt;

    @Version
    @Column(nullable = false)
    private Long version;

    public Order() {}

    public Order(UUID id, UUID customerId, BigDecimal totalAmount, String currency) {
        this.id = id;
        this.customerId = customerId;
        this.status = OrderStatus.PENDING;
        this.totalAmount = totalAmount;
        this.currency = currency != null ? currency : "USD";
        this.createdAt = Instant.now();
        this.updatedAt = Instant.now();
    }

    public void addItem(OrderItem item) {
        items.add(item);
        item.setOrder(this);
    }

    public void transitionTo(OrderStatus newStatus) {
        this.status = newStatus;
        this.updatedAt = Instant.now();
    }

    public void cancel(String reason) {
        this.status = OrderStatus.CANCELLED;
        this.cancelReason = reason;
        this.updatedAt = Instant.now();
    }

    @PreUpdate
    public void onUpdate() {
        this.updatedAt = Instant.now();
    }

    public UUID getId() { return id; }
    public void setId(UUID id) { this.id = id; }

    public UUID getCustomerId() { return customerId; }
    public void setCustomerId(UUID customerId) { this.customerId = customerId; }

    public OrderStatus getStatus() { return status; }
    public void setStatus(OrderStatus status) { this.status = status; }

    public BigDecimal getTotalAmount() { return totalAmount; }
    public void setTotalAmount(BigDecimal totalAmount) { this.totalAmount = totalAmount; }

    public String getCurrency() { return currency; }
    public void setCurrency(String currency) { this.currency = currency; }

    public String getCancelReason() { return cancelReason; }
    public void setCancelReason(String cancelReason) { this.cancelReason = cancelReason; }

    public List<OrderItem> getItems() { return items; }
    public void setItems(List<OrderItem> items) { this.items = items; }

    public Instant getCreatedAt() { return createdAt; }
    public void setCreatedAt(Instant createdAt) { this.createdAt = createdAt; }

    public Instant getUpdatedAt() { return updatedAt; }
    public void setUpdatedAt(Instant updatedAt) { this.updatedAt = updatedAt; }

    public Long getVersion() { return version; }
    public void setVersion(Long version) { this.version = version; }
}
""",

    # Domain: OrderItem
    f"{BASE}/domain/OrderItem.java": """package com.foodplatform.order.domain;

import jakarta.persistence.*;
import java.math.BigDecimal;
import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "order_items")
public class OrderItem {

    @Id
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "order_id", nullable = false)
    private Order order;

    @Column(name = "product_id", nullable = false)
    private UUID productId;

    @Column(nullable = false, length = 100)
    private String sku;

    @Column(name = "product_name", nullable = false)
    private String productName;

    @Column(name = "unit_price", nullable = false, precision = 12, scale = 2)
    private BigDecimal unitPrice;

    @Column(nullable = false)
    private int qty;

    @Column(name = "created_at", nullable = false, updatable = false)
    private Instant createdAt;

    public OrderItem() {}

    public OrderItem(UUID id, UUID productId, String sku, String productName, BigDecimal unitPrice, int qty) {
        this.id = id;
        this.productId = productId;
        this.sku = sku;
        this.productName = productName;
        this.unitPrice = unitPrice;
        this.qty = qty;
        this.createdAt = Instant.now();
    }

    public UUID getId() { return id; }
    public void setId(UUID id) { this.id = id; }

    public Order getOrder() { return order; }
    public void setOrder(Order order) { this.order = order; }

    public UUID getProductId() { return productId; }
    public void setProductId(UUID productId) { this.productId = productId; }

    public String getSku() { return sku; }
    public void setSku(String sku) { this.sku = sku; }

    public String getProductName() { return productName; }
    public void setProductName(String productName) { this.productName = productName; }

    public BigDecimal getUnitPrice() { return unitPrice; }
    public void setUnitPrice(BigDecimal unitPrice) { this.unitPrice = unitPrice; }

    public int getQty() { return qty; }
    public void setQty(int qty) { this.qty = qty; }

    public Instant getCreatedAt() { return createdAt; }
    public void setCreatedAt(Instant createdAt) { this.createdAt = createdAt; }
}
""",

    # Domain: OutboxEvent
    f"{BASE}/domain/OutboxEvent.java": """package com.foodplatform.order.domain;

import jakarta.persistence.*;
import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "outbox_events")
public class OutboxEvent {

    @Id
    private UUID id;

    @Column(name = "aggregate_type", nullable = false, length = 100)
    private String aggregateType;

    @Column(name = "aggregate_id", nullable = false, length = 100)
    private String aggregateId;

    @Column(nullable = false, length = 100)
    private String type;

    @Column(nullable = false, columnDefinition = "TEXT")
    private String payload;

    @Column(name = "created_at", nullable = false, updatable = false)
    private Instant createdAt;

    @Column(name = "processed_at")
    private Instant processedAt;

    @Column(name = "retry_count", nullable = false)
    private int retryCount;

    public OutboxEvent() {}

    public OutboxEvent(UUID id, String aggregateType, String aggregateId, String type, String payload) {
        this.id = id;
        this.aggregateType = aggregateType;
        this.aggregateId = aggregateId;
        this.type = type;
        this.payload = payload;
        this.createdAt = Instant.now();
        this.retryCount = 0;
    }

    public void markProcessed() {
        this.processedAt = Instant.now();
    }

    public void incrementRetry() {
        this.retryCount++;
    }

    public UUID getId() { return id; }
    public void setId(UUID id) { this.id = id; }

    public String getAggregateType() { return aggregateType; }
    public void setAggregateType(String aggregateType) { this.aggregateType = aggregateType; }

    public String getAggregateId() { return aggregateId; }
    public void setAggregateId(String aggregateId) { this.aggregateId = aggregateId; }

    public String getType() { return type; }
    public void setType(String type) { this.type = type; }

    public String getPayload() { return payload; }
    public void setPayload(String payload) { this.payload = payload; }

    public Instant getCreatedAt() { return createdAt; }
    public void setCreatedAt(Instant createdAt) { this.createdAt = createdAt; }

    public Instant getProcessedAt() { return processedAt; }
    public void setProcessedAt(Instant processedAt) { this.processedAt = processedAt; }

    public int getRetryCount() { return retryCount; }
    public void setRetryCount(int retryCount) { this.retryCount = retryCount; }
}
""",

    # Domain: IdempotencyRecord
    f"{BASE}/domain/IdempotencyRecord.java": """package com.foodplatform.order.domain;

import jakarta.persistence.*;
import java.time.Instant;

@Entity
@Table(name = "idempotency_records")
public class IdempotencyRecord {

    @Id
    @Column(length = 255)
    private String key;

    @Column(name = "response_body", nullable = false, columnDefinition = "TEXT")
    private String responseBody;

    @Column(name = "status_code", nullable = false)
    private int statusCode;

    @Column(name = "created_at", nullable = false, updatable = false)
    private Instant createdAt;

    public IdempotencyRecord() {}

    public IdempotencyRecord(String key, String responseBody, int statusCode) {
        this.key = key;
        this.responseBody = responseBody;
        this.statusCode = statusCode;
        this.createdAt = Instant.now();
    }

    public String getKey() { return key; }
    public void setKey(String key) { this.key = key; }

    public String getResponseBody() { return responseBody; }
    public void setResponseBody(String responseBody) { this.responseBody = responseBody; }

    public int getStatusCode() { return statusCode; }
    public void setStatusCode(int statusCode) { this.statusCode = statusCode; }

    public Instant getCreatedAt() { return createdAt; }
    public void setCreatedAt(Instant createdAt) { this.createdAt = createdAt; }
}
""",

    # Repositories
    f"{BASE}/repository/OrderRepository.java": """package com.foodplatform.order.repository;

import com.foodplatform.order.domain.Order;
import com.foodplatform.order.domain.OrderStatus;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.UUID;

@Repository
public interface OrderRepository extends JpaRepository<Order, UUID> {
    Page<Order> findByCustomerId(UUID customerId, Pageable pageable);
    Page<Order> findByStatus(OrderStatus status, Pageable pageable);
    Page<Order> findByCustomerIdAndStatus(UUID customerId, OrderStatus status, Pageable pageable);
}
""",

    f"{BASE}/repository/OrderItemRepository.java": """package com.foodplatform.order.repository;

import com.foodplatform.order.domain.OrderItem;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.UUID;

@Repository
public interface OrderItemRepository extends JpaRepository<OrderItem, UUID> {
}
""",

    f"{BASE}/repository/OutboxEventRepository.java": """package com.foodplatform.order.repository;

import com.foodplatform.order.domain.OutboxEvent;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.UUID;

@Repository
public interface OutboxEventRepository extends JpaRepository<OutboxEvent, UUID> {
    List<OutboxEvent> findByProcessedAtIsNullOrderByCreatedAtAsc(Pageable pageable);
}
""",

    f"{BASE}/repository/IdempotencyRecordRepository.java": """package com.foodplatform.order.repository;

import com.foodplatform.order.domain.IdempotencyRecord;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface IdempotencyRecordRepository extends JpaRepository<IdempotencyRecord, String> {
}
""",

    # Exceptions
    f"{BASE}/exception/ResourceNotFoundException.java": """package com.foodplatform.order.exception;

public class ResourceNotFoundException extends RuntimeException {
    public ResourceNotFoundException(String message) {
        super(message);
    }
}
""",

    f"{BASE}/exception/InvalidOrderStateException.java": """package com.foodplatform.order.exception;

public class InvalidOrderStateException extends RuntimeException {
    public InvalidOrderStateException(String message) {
        super(message);
    }
}
""",

    f"{BASE}/exception/GlobalExceptionHandler.java": """package com.foodplatform.order.exception;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ProblemDetail;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.context.request.ServletWebRequest;
import org.springframework.web.context.request.WebRequest;

import java.net.URI;
import java.time.Instant;
import java.util.stream.Collectors;

@RestControllerAdvice
public class GlobalExceptionHandler {

    private static final Logger log = LoggerFactory.getLogger(GlobalExceptionHandler.class);

    @ExceptionHandler(ResourceNotFoundException.class)
    public ProblemDetail handleNotFound(ResourceNotFoundException ex, WebRequest request) {
        return buildProblemDetail(HttpStatus.NOT_FOUND, "Resource Not Found", ex.getMessage(), "not-found", request);
    }

    @ExceptionHandler(InvalidOrderStateException.class)
    public ProblemDetail handleInvalidState(InvalidOrderStateException ex, WebRequest request) {
        return buildProblemDetail(HttpStatus.BAD_REQUEST, "Invalid Order State", ex.getMessage(), "invalid-state", request);
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ProblemDetail handleValidation(MethodArgumentNotValidException ex, WebRequest request) {
        String detail = ex.getBindingResult().getFieldErrors().stream()
                .map(err -> err.getField() + ": " + err.getDefaultMessage())
                .collect(Collectors.joining(", "));
        return buildProblemDetail(HttpStatus.BAD_REQUEST, "Validation Error", detail, "validation-error", request);
    }

    @ExceptionHandler(Exception.class)
    public ProblemDetail handleGeneric(Exception ex, WebRequest request) {
        log.error("Unhandled exception in order-service", ex);
        return buildProblemDetail(HttpStatus.INTERNAL_SERVER_ERROR, "Internal Server Error", ex.getMessage(), "internal", request);
    }

    private ProblemDetail buildProblemDetail(HttpStatus status, String title, String detail, String typeCode, WebRequest request) {
        ProblemDetail pd = ProblemDetail.forStatusAndDetail(status, detail);
        pd.setTitle(title);
        pd.setType(URI.create("https://foodplatform.com/errors/" + typeCode));
        pd.setProperty("timestamp", Instant.now());
        if (request instanceof ServletWebRequest swr) {
            pd.setInstance(URI.create(swr.getRequest().getRequestURI()));
            String correlationId = swr.getHeader("X-Correlation-Id");
            if (correlationId != null) {
                pd.setProperty("correlationId", correlationId);
            }
        }
        return pd;
    }
}
""",

    # DTOs
    f"{BASE}/dto/OrderItemDto.java": """package com.foodplatform.order.dto;

import java.math.BigDecimal;
import java.util.UUID;

public record OrderItemDto(
        UUID id,
        UUID productId,
        String sku,
        String productName,
        BigDecimal unitPrice,
        int qty,
        BigDecimal subtotal
) {}
""",

    f"{BASE}/dto/OrderDto.java": """package com.foodplatform.order.dto;

import com.foodplatform.order.domain.OrderStatus;
import java.math.BigDecimal;
import java.time.Instant;
import java.util.List;
import java.util.UUID;

public record OrderDto(
        UUID id,
        UUID customerId,
        OrderStatus status,
        BigDecimal totalAmount,
        String currency,
        String cancelReason,
        List<OrderItemDto> items,
        Instant createdAt,
        Instant updatedAt,
        Long version
) {}
""",

    f"{BASE}/dto/CreateOrderItemRequest.java": """package com.foodplatform.order.dto;

import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;
import java.math.BigDecimal;
import java.util.UUID;

public record CreateOrderItemRequest(
        @NotNull UUID productId,
        String sku,
        String productName,
        BigDecimal unitPrice,
        @Min(1) int qty
) {}
""",

    f"{BASE}/dto/CreateOrderRequest.java": """package com.foodplatform.order.dto;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.NotNull;
import java.util.List;
import java.util.UUID;

public record CreateOrderRequest(
        @NotNull UUID customerId,
        String currency,
        @NotEmpty @Valid List<CreateOrderItemRequest> items
) {}
""",

    f"{BASE}/dto/CancelOrderRequest.java": """package com.foodplatform.order.dto;

import jakarta.validation.constraints.NotBlank;

public record CancelOrderRequest(
        @NotBlank String reason
) {}
""",

    f"{BASE}/dto/PagedResponse.java": """package com.foodplatform.order.dto;

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
    public static <T> PagedResponse<T> from(Page<T> page) {
        return new PagedResponse<>(
                page.getContent(),
                page.getNumber(),
                page.getSize(),
                page.getTotalElements(),
                page.getTotalPages(),
                page.isLast()
        );
    }
}
""",

    # Resilience4j Client: ProductClient
    f"{BASE}/client/ProductClient.java": """package com.foodplatform.order.client;

import io.github.resilience4j.circuitbreaker.annotation.CircuitBreaker;
import io.github.resilience4j.retry.annotation.Retry;
import io.github.resilience4j.timelimiter.annotation.TimeLimiter;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;

import java.math.BigDecimal;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.CompletableFuture;

@Component
public class ProductClient {

    private static final Logger log = LoggerFactory.getLogger(ProductClient.class);

    private final RestClient restClient;

    public ProductClient(@Value("${clients.product-service.url:http://localhost:8082}") String productServiceUrl) {
        this.restClient = RestClient.builder().baseUrl(productServiceUrl).build();
    }

    public record ProductInfo(UUID id, String sku, String name, BigDecimal price, boolean active) {}

    @CircuitBreaker(name = "productClient", fallbackMethod = "fetchProductFallback")
    @Retry(name = "productClient")
    public ProductInfo fetchProduct(UUID productId) {
        log.info("Calling product-service for product {}", productId);
        try {
            @SuppressWarnings("unchecked")
            Map<String, Object> resp = restClient.get()
                    .uri("/api/v1/products/{id}", productId)
                    .retrieve()
                    .body(Map.class);

            if (resp != null) {
                return new ProductInfo(
                        UUID.fromString(resp.get("id").toString()),
                        resp.get("sku").toString(),
                        resp.get("name").toString(),
                        new BigDecimal(resp.get("price").toString()),
                        Boolean.parseBoolean(resp.get("active").toString())
                );
            }
        } catch (Exception e) {
            log.warn("Product client error for {}: {}", productId, e.getMessage());
        }
        return fetchProductFallback(productId, new RuntimeException("Product service unavailable"));
    }

    public ProductInfo fetchProductFallback(UUID productId, Throwable t) {
        log.warn("Executing fallback for product {} due to: {}", productId, t.getMessage());
        return new ProductInfo(productId, "SKU-UNKNOWN", "Product " + productId, new BigDecimal("10.00"), true);
    }
}
""",

    # Idempotency Service
    f"{BASE}/service/IdempotencyService.java": """package com.foodplatform.order.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.foodplatform.order.domain.IdempotencyRecord;
import com.foodplatform.order.repository.IdempotencyRecordRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;

import java.time.Duration;
import java.util.Optional;

@Service
public class IdempotencyService {

    private static final Logger log = LoggerFactory.getLogger(IdempotencyService.class);
    private static final String REDIS_PREFIX = "idempotency:";
    private static final Duration TTL = Duration.ofHours(24);

    private final IdempotencyRecordRepository repository;
    private final StringRedisTemplate redisTemplate;
    private final ObjectMapper objectMapper;

    public IdempotencyService(IdempotencyRecordRepository repository,
                              @Autowired(required = false) StringRedisTemplate redisTemplate,
                              ObjectMapper objectMapper) {
        this.repository = repository;
        this.redisTemplate = redisTemplate;
        this.objectMapper = objectMapper;
    }

    public record CachedResponse(int statusCode, String body) {}

    public Optional<CachedResponse> getCachedResponse(String key) {
        if (key == null || key.isBlank()) return Optional.empty();

        // 1. Try Redis cache
        if (redisTemplate != null) {
            try {
                String cached = redisTemplate.opsForValue().get(REDIS_PREFIX + key);
                if (cached != null) {
                    CachedResponse cr = objectMapper.readValue(cached, CachedResponse.class);
                    log.info("Idempotency HIT from Redis for key: {}", key);
                    return Optional.of(cr);
                }
            } catch (Exception e) {
                log.warn("Redis idempotency read failed for {}: {}", key, e.getMessage());
            }
        }

        // 2. Fall back to PostgreSQL database
        Optional<IdempotencyRecord> record = repository.findById(key);
        if (record.isPresent()) {
            log.info("Idempotency HIT from DB for key: {}", key);
            CachedResponse cr = new CachedResponse(record.get().getStatusCode(), record.get().getResponseBody());
            // Warm Redis
            saveToRedis(key, cr);
            return Optional.of(cr);
        }

        return Optional.empty();
    }

    public void saveResponse(String key, int statusCode, String responseBody) {
        if (key == null || key.isBlank()) return;

        CachedResponse cr = new CachedResponse(statusCode, responseBody);

        // 1. Save to DB
        try {
            repository.save(new IdempotencyRecord(key, responseBody, statusCode));
        } catch (Exception e) {
            log.warn("DB idempotency save failed for {}: {}", key, e.getMessage());
        }

        // 2. Save to Redis
        saveToRedis(key, cr);
    }

    private void saveToRedis(String key, CachedResponse cr) {
        if (redisTemplate != null) {
            try {
                String json = objectMapper.writeValueAsString(cr);
                redisTemplate.opsForValue().set(REDIS_PREFIX + key, json, TTL);
            } catch (Exception e) {
                log.warn("Redis idempotency write failed for {}: {}", key, e.getMessage());
            }
        }
    }
}
""",

    # Outbox Publisher
    f"{BASE}/service/OutboxPublisher.java": """package com.foodplatform.order.service;

import com.foodplatform.order.domain.OutboxEvent;
import com.foodplatform.order.repository.OutboxEventRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.domain.PageRequest;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
public class OutboxPublisher {

    private static final Logger log = LoggerFactory.getLogger(OutboxPublisher.class);

    private final OutboxEventRepository outboxEventRepository;
    private final KafkaTemplate<String, Object> kafkaTemplate;

    public OutboxPublisher(OutboxEventRepository outboxEventRepository,
                           @Autowired(required = false) KafkaTemplate<String, Object> kafkaTemplate) {
        this.outboxEventRepository = outboxEventRepository;
        this.kafkaTemplate = kafkaTemplate;
    }

    @Scheduled(fixedDelay = 500)
    @Transactional
    public void publishOutboxEvents() {
        if (kafkaTemplate == null) return;

        List<OutboxEvent> unprocessed = outboxEventRepository.findByProcessedAtIsNullOrderByCreatedAtAsc(PageRequest.of(0, 50));
        for (OutboxEvent event : unprocessed) {
            try {
                kafkaTemplate.send(event.getType(), event.getAggregateId(), event.getPayload()).get();
                event.markProcessed();
                outboxEventRepository.save(event);
                log.info("Published outbox event {} for {} to topic {}", event.getId(), event.getAggregateId(), event.getType());
            } catch (Exception e) {
                log.warn("Failed to publish outbox event {}: {}", event.getId(), e.getMessage());
                event.incrementRetry();
                outboxEventRepository.save(event);
            }
        }
    }
}
""",

    # Order Service
    f"{BASE}/service/OrderService.java": """package com.foodplatform.order.service;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.foodplatform.order.client.ProductClient;
import com.foodplatform.order.domain.*;
import com.foodplatform.order.dto.*;
import com.foodplatform.order.exception.InvalidOrderStateException;
import com.foodplatform.order.exception.ResourceNotFoundException;
import com.foodplatform.order.repository.OrderRepository;
import com.foodplatform.order.repository.OutboxEventRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.util.*;

@Service
public class OrderService {

    private static final Logger log = LoggerFactory.getLogger(OrderService.class);

    private final OrderRepository orderRepository;
    private final OutboxEventRepository outboxEventRepository;
    private final ProductClient productClient;
    private final ObjectMapper objectMapper;

    public OrderService(OrderRepository orderRepository,
                        OutboxEventRepository outboxEventRepository,
                        ProductClient productClient,
                        ObjectMapper objectMapper) {
        this.orderRepository = orderRepository;
        this.outboxEventRepository = outboxEventRepository;
        this.productClient = productClient;
        this.objectMapper = objectMapper;
    }

    @Transactional(readOnly = true)
    public OrderDto getOrderById(UUID id) {
        return orderRepository.findById(id)
                .map(this::toDto)
                .orElseThrow(() -> new ResourceNotFoundException("Order not found with id: " + id));
    }

    @Transactional(readOnly = true)
    public PagedResponse<OrderDto> getOrders(UUID customerId, OrderStatus status, Pageable pageable) {
        Page<Order> page;
        if (customerId != null && status != null) {
            page = orderRepository.findByCustomerIdAndStatus(customerId, status, pageable);
        } else if (customerId != null) {
            page = orderRepository.findByCustomerId(customerId, pageable);
        } else if (status != null) {
            page = orderRepository.findByStatus(status, pageable);
        } else {
            page = orderRepository.findAll(pageable);
        }
        return PagedResponse.from(page.map(this::toDto));
    }

    /**
     * Transactional Outbox Pattern:
     * Saves the Order and creates the OutboxEvent within the same ACID database transaction!
     */
    @Transactional
    public OrderDto createOrder(CreateOrderRequest req) {
        UUID orderId = UUID.randomUUID();
        BigDecimal totalAmount = BigDecimal.ZERO;

        List<OrderItem> items = new ArrayList<>();
        List<Map<String, Object>> eventItems = new ArrayList<>();

        for (CreateOrderItemRequest itemReq : req.items()) {
            ProductClient.ProductInfo pInfo = productClient.fetchProduct(itemReq.productId());
            String sku = itemReq.sku() != null ? itemReq.sku() : pInfo.sku();
            String name = itemReq.productName() != null ? itemReq.productName() : pInfo.name();
            BigDecimal unitPrice = itemReq.unitPrice() != null ? itemReq.unitPrice() : pInfo.price();

            BigDecimal subtotal = unitPrice.multiply(BigDecimal.valueOf(itemReq.qty()));
            totalAmount = totalAmount.add(subtotal);

            OrderItem orderItem = new OrderItem(UUID.randomUUID(), itemReq.productId(), sku, name, unitPrice, itemReq.qty());
            items.add(orderItem);

            eventItems.add(Map.of(
                    "productId", itemReq.productId().toString(),
                    "sku", sku,
                    "name", name,
                    "unitPrice", unitPrice,
                    "qty", itemReq.qty()
            ));
        }

        Order order = new Order(orderId, req.customerId(), totalAmount, req.currency());
        for (OrderItem oi : items) {
            order.addItem(oi);
        }

        Order saved = orderRepository.save(order);

        // Record outbox event in same transaction
        Map<String, Object> outboxPayload = Map.of(
                "orderId", orderId.toString(),
                "customerId", req.customerId().toString(),
                "totalAmount", totalAmount,
                "currency", order.getCurrency(),
                "items", eventItems
        );

        try {
            String payloadJson = objectMapper.writeValueAsString(outboxPayload);
            OutboxEvent outboxEvent = new OutboxEvent(
                    UUID.randomUUID(),
                    "Order",
                    orderId.toString(),
                    "order.created",
                    payloadJson
            );
            outboxEventRepository.save(outboxEvent);
            log.info("Saved order {} and outbox_event in same transaction", orderId);
        } catch (JsonProcessingException e) {
            throw new RuntimeException("Failed to serialize outbox event payload", e);
        }

        return toDto(saved);
    }

    @Transactional
    public OrderDto cancelOrder(UUID id, String reason) {
        Order order = orderRepository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Order not found with id: " + id));

        if (order.getStatus() == OrderStatus.DELIVERED || order.getStatus() == OrderStatus.CANCELLED) {
            throw new InvalidOrderStateException("Order in status " + order.getStatus() + " cannot be cancelled");
        }

        order.cancel(reason);
        Order updated = orderRepository.save(order);

        // Record cancellation outbox event
        try {
            String payload = objectMapper.writeValueAsString(Map.of(
                    "orderId", id.toString(),
                    "status", "CANCELLED",
                    "reason", reason,
                    "timestamp", java.time.Instant.now().toString()
            ));
            outboxEventRepository.save(new OutboxEvent(UUID.randomUUID(), "Order", id.toString(), "order.cancelled", payload));
        } catch (Exception e) {
            log.warn("Failed to create cancellation outbox event: {}", e.getMessage());
        }

        return toDto(updated);
    }

    @Transactional
    public void confirmOrder(UUID orderId) {
        orderRepository.findById(orderId).ifPresent(order -> {
            if (order.getStatus() == OrderStatus.PENDING) {
                order.transitionTo(OrderStatus.CONFIRMED);
                orderRepository.save(order);
                log.info("Choreography: Order {} transitioned to CONFIRMED", orderId);

                try {
                    String payload = objectMapper.writeValueAsString(Map.of(
                            "orderId", orderId.toString(),
                            "status", "CONFIRMED",
                            "timestamp", java.time.Instant.now().toString()
                    ));
                    outboxEventRepository.save(new OutboxEvent(UUID.randomUUID(), "Order", orderId.toString(), "order.confirmed", payload));
                } catch (Exception e) {
                    log.warn("Failed to create confirmation outbox event: {}", e.getMessage());
                }
            }
        });
    }

    @Transactional
    public void rejectOrder(UUID orderId, String reason) {
        orderRepository.findById(orderId).ifPresent(order -> {
            if (order.getStatus() == OrderStatus.PENDING) {
                order.cancel("INSUFFICIENT_STOCK: " + reason);
                orderRepository.save(order);
                log.info("Choreography: Order {} transitioned to CANCELLED (insufficient stock)", orderId);

                try {
                    String payload = objectMapper.writeValueAsString(Map.of(
                            "orderId", orderId.toString(),
                            "status", "CANCELLED",
                            "reason", "INSUFFICIENT_STOCK: " + reason,
                            "timestamp", java.time.Instant.now().toString()
                    ));
                    outboxEventRepository.save(new OutboxEvent(UUID.randomUUID(), "Order", orderId.toString(), "order.cancelled", payload));
                } catch (Exception e) {
                    log.warn("Failed to create rejection outbox event: {}", e.getMessage());
                }
            }
        });
    }

    public OrderDto toDto(Order order) {
        List<OrderItemDto> itemDtos = order.getItems().stream().map(i -> new OrderItemDto(
                i.getId(),
                i.getProductId(),
                i.getSku(),
                i.getProductName(),
                i.getUnitPrice(),
                i.getQty(),
                i.getUnitPrice().multiply(BigDecimal.valueOf(i.getQty()))
        )).toList();

        return new OrderDto(
                order.getId(),
                order.getCustomerId(),
                order.getStatus(),
                order.getTotalAmount(),
                order.getCurrency(),
                order.getCancelReason(),
                itemDtos,
                order.getCreatedAt(),
                order.getUpdatedAt(),
                order.getVersion()
        );
    }
}
""",

    # Kafka Choreography Listener
    f"{BASE}/event/OrderChoreographyListener.java": """package com.foodplatform.order.event;

import com.foodplatform.order.service.OrderService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Component;

import java.util.Map;
import java.util.UUID;

@Component
public class OrderChoreographyListener {

    private static final Logger log = LoggerFactory.getLogger(OrderChoreographyListener.class);

    private final OrderService orderService;

    public OrderChoreographyListener(OrderService orderService) {
        this.orderService = orderService;
    }

    @KafkaListener(topics = "inventory.reserved", groupId = "order-choreography-group")
    public void onInventoryReserved(Map<String, Object> message) {
        try {
            log.info("Received inventory.reserved event: {}", message);
            UUID orderId = UUID.fromString(message.get("orderId").toString());
            orderService.confirmOrder(orderId);
        } catch (Exception e) {
            log.error("Failed to process inventory.reserved: {}", e.getMessage());
        }
    }

    @KafkaListener(topics = "inventory.rejected", groupId = "order-choreography-group")
    public void onInventoryRejected(Map<String, Object> message) {
        try {
            log.info("Received inventory.rejected event: {}", message);
            UUID orderId = UUID.fromString(message.get("orderId").toString());
            String reason = message.get("reason") != null ? message.get("reason").toString() : "Stock allocation failed";
            orderService.rejectOrder(orderId, reason);
        } catch (Exception e) {
            log.error("Failed to process inventory.rejected: {}", e.getMessage());
        }
    }
}
""",

    # Controller
    f"{BASE}/controller/OrderController.java": """package com.foodplatform.order.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.foodplatform.order.domain.OrderStatus;
import com.foodplatform.order.dto.*;
import com.foodplatform.order.service.IdempotencyService;
import com.foodplatform.order.service.OrderService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.springframework.data.domain.Pageable;
import org.springframework.data.web.PageableDefault;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Optional;
import java.util.UUID;

@RestController
@RequestMapping("/api/v1/orders")
@Tag(name = "Orders", description = "Order lifecycle, idempotency, and transactional outbox management")
public class OrderController {

    private final OrderService orderService;
    private final IdempotencyService idempotencyService;
    private final ObjectMapper objectMapper;

    public OrderController(OrderService orderService,
                           IdempotencyService idempotencyService,
                           ObjectMapper objectMapper) {
        this.orderService = orderService;
        this.idempotencyService = idempotencyService;
        this.objectMapper = objectMapper;
    }

    @PostMapping
    @Operation(summary = "Create new order with idempotency key")
    public ResponseEntity<?> createOrder(
            @RequestHeader(value = "Idempotency-Key", required = false) String idempotencyKey,
            @Valid @RequestBody CreateOrderRequest request
    ) throws Exception {
        // Check idempotency key if provided
        if (idempotencyKey != null && !idempotencyKey.isBlank()) {
            Optional<IdempotencyService.CachedResponse> cached = idempotencyService.getCachedResponse(idempotencyKey);
            if (cached.isPresent()) {
                OrderDto cachedDto = objectMapper.readValue(cached.get().body(), OrderDto.class);
                return ResponseEntity.status(cached.get().statusCode()).body(cachedDto);
            }
        }

        OrderDto created = orderService.createOrder(request);

        if (idempotencyKey != null && !idempotencyKey.isBlank()) {
            String json = objectMapper.writeValueAsString(created);
            idempotencyService.saveResponse(idempotencyKey, HttpStatus.CREATED.value(), json);
        }

        return ResponseEntity.status(HttpStatus.CREATED).body(created);
    }

    @GetMapping("/{id}")
    @Operation(summary = "Get order by ID")
    public ResponseEntity<OrderDto> getOrderById(@PathVariable UUID id) {
        return ResponseEntity.ok(orderService.getOrderById(id));
    }

    @GetMapping
    @Operation(summary = "List orders with filters and pagination")
    public ResponseEntity<PagedResponse<OrderDto>> getOrders(
            @RequestParam(required = false) UUID customerId,
            @RequestParam(required = false) OrderStatus status,
            @PageableDefault(size = 20) Pageable pageable
    ) {
        return ResponseEntity.ok(orderService.getOrders(customerId, status, pageable));
    }

    @PostMapping("/{id}/cancel")
    @Operation(summary = "Cancel an order")
    public ResponseEntity<OrderDto> cancelOrder(
            @PathVariable UUID id,
            @Valid @RequestBody CancelOrderRequest request
    ) {
        return ResponseEntity.ok(orderService.cancelOrder(id, request.reason()));
    }
}
""",

    # OpenAPI Config
    f"{BASE}/config/OpenApiConfig.java": """package com.foodplatform.order.config;

import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Info;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class OpenApiConfig {

    @Bean
    public OpenAPI orderOpenAPI() {
        return new OpenAPI()
                .info(new Info()
                        .title("Order Service API")
                        .description("Order state machine, transactional outbox, and idempotency API")
                        .version("1.0.0"));
    }
}
"""
}

for path, content in FILES.items():
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Wrote {path}")

print("All order-service source files written successfully.")
